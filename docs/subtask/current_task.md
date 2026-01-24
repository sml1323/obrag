# LLM Provider 구현체 구현 계획

> **Target Task**: Phase 2 - 멀티 LLM 지원 > LLM Provider 구현체
> **Target Path**: `src/core/llm/`

## 목표

Skeleton으로 남아있는 `GeminiLLM`과 `OllamaLLM` 클래스를 실제 API 호출이 가능하도록 완성합니다.

---

## 기존 패턴 분석

### OpenAILLM 구현체 참고

| 항목                  | 구현 방식                                        |
| --------------------- | ------------------------------------------------ |
| **클라이언트 초기화** | `__init__`에서 API 클라이언트 생성               |
| **API 호출**          | `generate()` 메서드에서 Chat Completion API 호출 |
| **응답 변환**         | API 응답을 `LLMResponse` dataclass로 래핑        |
| **파라미터**          | `temperature`, `max_tokens` 지원                 |

```python
# OpenAILLM.generate() 패턴
response = self._client.chat.completions.create(
    model=self._model_name,
    messages=messages,
    temperature=temperature,
    max_tokens=max_tokens,
)

return LLMResponse(
    content=response.choices[0].message.content,
    model=response.model,
    usage={"input_tokens": ..., "output_tokens": ...}
)
```

---

## 제안하는 구조

```
src/core/llm/
├── strategy.py      # (기존) Protocol + FakeLLM
├── openai_llm.py    # (기존) OpenAI 구현체
├── gemini_llm.py    # ← 수정: google-genai SDK 활용
└── ollama_llm.py    # ← 수정: OpenAI 호환 API 활용
```

### 핵심 설계 결정

#### 1. GeminiLLM - `google-genai` SDK 사용

- Google 공식 Python SDK (`google-genai`) 사용
- 단순 텍스트 생성에는 `client.models.generate_content()` 사용
- Chat 형식 지원을 위해 messages를 Gemini 포맷으로 변환

#### 2. OllamaLLM - OpenAI 호환 API 사용

- Ollama는 OpenAI API 호환 엔드포인트 제공 (`/v1/chat/completions`)
- 기존 `openai` 라이브러리를 `base_url`만 변경하여 재사용
- 추가 의존성 없이 구현 가능

---

## 파일별 상세 계획

### 1. [MODIFY] [gemini_llm.py](file:///Users/imseungmin/work/portfolio/obsidian_RAG/obrag/src/core/llm/gemini_llm.py)

```python
from typing import List, Optional
from google import genai
from google.genai import types
from .strategy import LLMResponse, Message


class GeminiLLM:
    """Google Gemini LLM 구현체."""

    def __init__(
        self,
        model_name: str = "gemini-2.0-flash",
        api_key: Optional[str] = None,
    ):
        """
        Args:
            model_name: Gemini 모델 이름
            api_key: API 키 (None이면 환경변수 GOOGLE_API_KEY 사용)
        """
        self._model_name = model_name
        self._client = genai.Client(api_key=api_key)

    def generate(
        self,
        messages: List[Message],
        *,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        """Gemini API 호출."""
        # OpenAI 형식 → Gemini 형식 변환
        contents = self._convert_messages(messages)
        config = types.GenerateContentConfig(
            temperature=temperature,
            max_output_tokens=max_tokens,
        )

        response = self._client.models.generate_content(
            model=self._model_name,
            contents=contents,
            config=config,
        )

        return LLMResponse(
            content=response.text or "",
            model=self._model_name,
            usage={
                "input_tokens": response.usage_metadata.prompt_token_count if response.usage_metadata else 0,
                "output_tokens": response.usage_metadata.candidates_token_count if response.usage_metadata else 0,
            }
        )

    def _convert_messages(self, messages: List[Message]) -> list:
        """OpenAI 형식 메시지를 Gemini 형식으로 변환."""
        contents = []
        system_instruction = None

        for msg in messages:
            role = msg["role"]
            content = msg["content"]

            if role == "system":
                system_instruction = content
            elif role == "user":
                contents.append(types.Content(
                    role="user",
                    parts=[types.Part(text=content)]
                ))
            elif role == "assistant":
                contents.append(types.Content(
                    role="model",
                    parts=[types.Part(text=content)]
                ))

        return contents

    @property
    def model_name(self) -> str:
        return self._model_name
```

---

### 2. [MODIFY] [ollama_llm.py](file:///Users/imseungmin/work/portfolio/obsidian_RAG/obrag/src/core/llm/ollama_llm.py)

```python
from typing import List, Optional
from openai import OpenAI
from .strategy import LLMResponse, Message


class OllamaLLM:
    """로컬 Ollama 서버용 LLM 구현체."""

    def __init__(
        self,
        model_name: str = "llama3.2",
        base_url: str = "http://localhost:11434/v1",
    ):
        """
        Args:
            model_name: Ollama 모델 이름
            base_url: Ollama 서버 URL (OpenAI 호환 엔드포인트)
        """
        self._model_name = model_name
        self._client = OpenAI(
            base_url=base_url,
            api_key="ollama",  # 필수이지만 무시됨
        )

    def generate(
        self,
        messages: List[Message],
        *,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        """Ollama API 호출 (OpenAI 호환)."""
        response = self._client.chat.completions.create(
            model=self._model_name,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )

        return LLMResponse(
            content=response.choices[0].message.content or "",
            model=response.model,
            usage={
                "input_tokens": response.usage.prompt_tokens if response.usage else 0,
                "output_tokens": response.usage.completion_tokens if response.usage else 0,
            }
        )

    @property
    def model_name(self) -> str:
        return self._model_name
```

---

### 3. 의존성 추가

`pyproject.toml` 또는 `requirements.txt`에 추가 필요:

```
google-genai>=1.0.0
```

> **Note**: `ollama` 구현은 기존 `openai` 패키지를 재사용하므로 추가 의존성 없음

---

## Verification Plan

### Automated Tests

1. **단위 테스트** (`tests/core/llm/`)
   - `test_gemini_llm.py`: API 키 없을 시 skip, 기본 generate 호출 테스트
   - `test_ollama_llm.py`: 서버 연결 불가 시 skip, 기본 generate 호출 테스트

2. **Mock 테스트**
   - API 호출부 mocking으로 응답 형식 검증

```bash
pytest tests/core/llm/ -v
```

### Manual Verification

1. **Gemini 테스트**: `GOOGLE_API_KEY` 환경변수 설정 후 실행
2. **Ollama 테스트**: 로컬에서 `ollama serve` 실행 후 테스트

---

## 요약

| 항목             | 내용                                                            |
| ---------------- | --------------------------------------------------------------- |
| **수정 파일 수** | 2개 (`gemini_llm.py`, `ollama_llm.py`)                          |
| **추가 의존성**  | `google-genai`                                                  |
| **테스트 파일**  | `test_gemini_llm.py`, `test_ollama_llm.py` (신규 또는 업데이트) |
| **주요 패턴**    | OpenAI 구현체 패턴 재사용                                       |
| **특이사항**     | Ollama는 OpenAI 호환 API 활용 (추가 라이브러리 불필요)          |
