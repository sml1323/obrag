# LLMStrategy Protocol 구현 계획

> **Target Task**: Phase 2 - 멀티 LLM 지원 > LLMStrategy Protocol
> **Target Path**: `src/core/llm/`

## 목표

LLM 호출을 위한 **공통 인터페이스(Protocol)**를 정의하여, 다양한 LLM 프로바이더(OpenAI, Gemini, Ollama)를 일관된 방식으로 사용할 수 있게 합니다. 기존 `EmbeddingStrategy` 패턴을 참고하여 DI 원칙과 테스트 용이성을 확보합니다.

---

## 기존 패턴 분석

`src/core/embedding/` 구조를 참고합니다:

| 파일                 | 역할                                    |
| -------------------- | --------------------------------------- |
| `strategy.py`        | Protocol 정의 + FakeEmbedder (테스트용) |
| `openai_embedder.py` | OpenAI 구현체                           |
| `local_embedder.py`  | 로컬 모델 구현체 (Skeleton)             |
| `factory.py`         | Config 기반 인스턴스 생성               |
| `__init__.py`        | 깔끔한 모듈 export                      |

### 핵심 특징

- **Protocol 패턴**: `typing.Protocol`을 사용한 덕 타이핑
- **Type Alias**: `Vector = List[float]` 등 명확한 타입 힌트
- **FakeEmbedder**: API 호출 없이 빠른 단위 테스트
- **Config Dataclass**: `src/config/models.py`에서 설정 검증

---

## 제안하는 구조

```
src/core/llm/
├── __init__.py           # 모듈 export
├── strategy.py           # LLMStrategy Protocol + FakeLLM
├── openai_llm.py         # OpenAI 구현체 (Phase 2 우선 구현)
├── gemini_llm.py         # Gemini 구현체 (Skeleton)
└── ollama_llm.py         # Ollama 구현체 (Skeleton)
```

```
src/config/models.py      # LLM Config 추가
```

---

## 파일별 상세 계획

### 1. `src/core/llm/strategy.py`

LLM 호출을 위한 Protocol과 테스트용 FakeLLM을 정의합니다.

```python
from typing import Protocol, List, Optional
from dataclasses import dataclass

# Type Aliases
Message = dict  # {"role": "user"|"assistant"|"system", "content": str}

@dataclass
class LLMResponse:
    """LLM 응답 데이터"""
    content: str
    model: str
    usage: dict  # {"input_tokens": int, "output_tokens": int}


class LLMStrategy(Protocol):
    """LLM 전략 Protocol"""

    def generate(
        self,
        messages: List[Message],
        *,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        """메시지 기반 응답 생성"""
        ...

    @property
    def model_name(self) -> str:
        """사용 중인 모델 이름"""
        ...


class FakeLLM:
    """테스트용 가짜 LLM"""

    def __init__(self, response: str = "This is a fake response."):
        self._response = response
        self._model_name = "fake-llm"

    def generate(
        self,
        messages: List[Message],
        *,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        return LLMResponse(
            content=self._response,
            model=self._model_name,
            usage={"input_tokens": 10, "output_tokens": 5}
        )

    @property
    def model_name(self) -> str:
        return self._model_name
```

---

### 2. `src/core/llm/openai_llm.py`

OpenAI Chat Completion API 구현체입니다.

```python
from typing import List, Optional
from openai import OpenAI
from .strategy import LLMStrategy, LLMResponse, Message

class OpenAILLM:
    """OpenAI LLM 구현체"""

    def __init__(
        self,
        model_name: str = "gpt-4o-mini",
        api_key: Optional[str] = None,
    ):
        self._model_name = model_name
        self._client = OpenAI(api_key=api_key)

    def generate(
        self,
        messages: List[Message],
        *,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        response = self._client.chat.completions.create(
            model=self._model_name,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return LLMResponse(
            content=response.choices[0].message.content,
            model=response.model,
            usage={
                "input_tokens": response.usage.prompt_tokens,
                "output_tokens": response.usage.completion_tokens,
            }
        )

    @property
    def model_name(self) -> str:
        return self._model_name
```

---

### 3. `src/core/llm/gemini_llm.py` (Skeleton)

```python
from typing import List, Optional
from .strategy import LLMResponse, Message

class GeminiLLM:
    """Gemini LLM 구현체 (추후 구현)"""

    def __init__(self, model_name: str = "gemini-1.5-flash"):
        self._model_name = model_name

    def generate(
        self,
        messages: List[Message],
        *,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        raise NotImplementedError("GeminiLLM is not implemented yet")

    @property
    def model_name(self) -> str:
        return self._model_name
```

---

### 4. `src/core/llm/ollama_llm.py` (Skeleton)

```python
from typing import List, Optional
from .strategy import LLMResponse, Message

class OllamaLLM:
    """Ollama LLM 구현체 (추후 구현)"""

    def __init__(self, model_name: str = "llama3"):
        self._model_name = model_name

    def generate(
        self,
        messages: List[Message],
        *,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        raise NotImplementedError("OllamaLLM is not implemented yet")

    @property
    def model_name(self) -> str:
        return self._model_name
```

---

### 5. `src/config/models.py` 추가

```python
# LLM Config Types
LLMProvider = Literal["openai", "gemini", "ollama"]
OpenAILLMModel = Literal["gpt-4o", "gpt-4o-mini", "gpt-4-turbo"]
GeminiLLMModel = Literal["gemini-1.5-pro", "gemini-1.5-flash"]

@dataclass
class OpenAILLMConfig:
    provider: LLMProvider = "openai"
    model_name: OpenAILLMModel = "gpt-4o-mini"
    api_key: str | None = None

    def __post_init__(self):
        # validation...

@dataclass
class GeminiLLMConfig:
    provider: LLMProvider = "gemini"
    model_name: GeminiLLMModel = "gemini-1.5-flash"
    api_key: str | None = None

@dataclass
class OllamaLLMConfig:
    provider: LLMProvider = "ollama"
    model_name: str = "llama3"
    base_url: str = "http://localhost:11434"
```

---

## Verification Plan

### Automated Tests

1. **단위 테스트 작성**: `src/test/llm/test_strategy.py`

```bash
# 테스트 실행 명령어
cd /Users/imseungmin/work/portfolio/obsidian_RAG/obrag
python -m pytest src/test/llm/test_strategy.py -v
```

테스트 항목:

- `FakeLLM.generate()` 정상 동작
- `LLMResponse` 데이터 구조 검증
- OpenAI Config 유효성 검증

2. **실제 API 호출 테스트** (선택적):

```bash
# OpenAI API 연동 테스트 (API 키 필요)
python -m pytest src/test/llm/test_openai_llm.py -v -k "integration"
```

### Manual Verification

사용자에게 다음 확인을 요청할 수 있습니다:

- OpenAI API 키가 `.env`에 설정되어 있는지 확인
- 실제 API 호출 테스트 결과 확인

---

## 요약

| 항목            | 내용                                                                                  |
| --------------- | ------------------------------------------------------------------------------------- |
| **신규 파일**   | 5개 (`strategy.py`, `openai_llm.py`, `gemini_llm.py`, `ollama_llm.py`, `__init__.py`) |
| **수정 파일**   | 1개 (`src/config/models.py`)                                                          |
| **테스트 파일** | 2개 (`test_strategy.py`, `test_openai_llm.py`)                                        |
| **외부 의존성** | `openai` (이미 설치됨), `google-generativeai` (Gemini용, 추후), `ollama` (추후)       |
| **참고 패턴**   | `src/core/embedding/` 구조 동일 적용                                                  |

> [!IMPORTANT]
> 이 Sub-task에서는 **LLMStrategy Protocol**과 **OpenAI 구현체**만 완전 구현합니다.
> Gemini, Ollama는 Skeleton만 생성하고, 다음 Sub-task "LLM Provider 구현체"에서 완성합니다.
