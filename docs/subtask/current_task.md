# LLMFactory & Config 구현 계획

> **Target Task**: Phase 2 - 멀티 LLM 지원 > LLMFactory & Config
> **Target Path**: `src/core/llm/factory.py`

## 목표

Config 기반으로 적절한 LLM 인스턴스를 생성하는 Factory 구현.
기존 `EmbedderFactory` 패턴을 재사용하여 일관성 유지.

---

## 기존 패턴 분석

### EmbedderFactory 패턴 ([factory.py](file:///Users/imseungmin/work/portfolio/obsidian_RAG/obrag/src/core/embedding/factory.py))

```python
class EmbedderFactory:
    @staticmethod
    def create(config: EmbeddingConfig) -> EmbeddingStrategy:
        if config.provider == "openai":
            return OpenAIEmbedder(...)
        elif config.provider == "local":
            return LocalEmbedder(...)

    @staticmethod
    def create_fake(dimension: int = 8) -> FakeEmbedder:
        # 테스트용 편의 메서드
```

**핵심 특징:**

- `provider` 필드로 분기
- 타입 체크로 config 유효성 검증
- 테스트용 `create_fake()` 제공
- 편의 메서드 (`create_openai()`)

### 기존 LLM Config ([models.py](file:///Users/imseungmin/work/portfolio/obsidian_RAG/obrag/src/config/models.py#L42-L87))

| Config Class      | Provider   | 주요 필드                |
| ----------------- | ---------- | ------------------------ |
| `OpenAILLMConfig` | `"openai"` | `model_name`, `api_key`  |
| `GeminiLLMConfig` | `"gemini"` | `model_name`, `api_key`  |
| `OllamaLLMConfig` | `"ollama"` | `model_name`, `base_url` |

---

## 제안하는 구조

### 신규 파일

| 파일                      | 역할                    |
| ------------------------- | ----------------------- |
| `src/core/llm/factory.py` | [NEW] LLMFactory 클래스 |

### 수정 파일

| 파일                                       | 수정 사항              |
| ------------------------------------------ | ---------------------- |
| `src/core/llm/__init__.py`                 | LLMFactory export 추가 |
| `src/tasktests/phase2/test_llm_factory.py` | [NEW] 통합 테스트      |

---

## 파일별 상세 계획

### [NEW] `src/core/llm/factory.py`

```python
"""
LLM Factory

Config 기반으로 적절한 LLM을 생성하는 Factory 패턴 구현.
"""

from typing import Union

from .strategy import LLMStrategy, FakeLLM
from .openai_llm import OpenAILLM
from .gemini_llm import GeminiLLM
from .ollama_llm import OllamaLLM

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from config.models import (
    OpenAILLMConfig,
    GeminiLLMConfig,
    OllamaLLMConfig,
    LLMConfig,
)


class LLMFactory:
    """
    Config 기반 LLM 팩토리.

    사용법:
        # OpenAI LLM 생성
        config = OpenAILLMConfig(model_name="gpt-4o-mini")
        llm = LLMFactory.create(config)

        # Gemini LLM 생성
        config = GeminiLLMConfig(model_name="gemini-1.5-flash")
        llm = LLMFactory.create(config)

        # Ollama LLM 생성
        config = OllamaLLMConfig(model_name="llama3")
        llm = LLMFactory.create(config)

        # 테스트용 Fake LLM
        llm = LLMFactory.create_fake(response="Test response")
    """

    @staticmethod
    def create(config: LLMConfig) -> LLMStrategy:
        """
        Config 기반 LLM 생성.

        Args:
            config: OpenAILLMConfig, GeminiLLMConfig, 또는 OllamaLLMConfig

        Returns:
            LLMStrategy 프로토콜을 구현한 LLM 인스턴스

        Raises:
            ValueError: 알 수 없는 provider인 경우
        """
        if config.provider == "openai":
            if not isinstance(config, OpenAILLMConfig):
                raise TypeError("OpenAI provider requires OpenAILLMConfig")
            return OpenAILLM(
                model_name=config.model_name,
                api_key=config.api_key,
            )

        elif config.provider == "gemini":
            if not isinstance(config, GeminiLLMConfig):
                raise TypeError("Gemini provider requires GeminiLLMConfig")
            return GeminiLLM(
                model_name=config.model_name,
                api_key=config.api_key,
            )

        elif config.provider == "ollama":
            if not isinstance(config, OllamaLLMConfig):
                raise TypeError("Ollama provider requires OllamaLLMConfig")
            return OllamaLLM(
                model_name=config.model_name,
                base_url=config.base_url,
            )

        else:
            raise ValueError(
                f"Unknown provider: {config.provider}. "
                "Supported providers: 'openai', 'gemini', 'ollama'"
            )

    @staticmethod
    def create_fake(response: str = "This is a fake response.") -> FakeLLM:
        """
        테스트용 Fake LLM 생성.

        Args:
            response: 반환할 고정 응답 문자열

        Returns:
            FakeLLM 인스턴스
        """
        return FakeLLM(response=response)
```

---

### [MODIFY] `src/core/llm/__init__.py`

```diff
 from .strategy import LLMStrategy, LLMResponse, FakeLLM, Message
 from .openai_llm import OpenAILLM
 from .gemini_llm import GeminiLLM
 from .ollama_llm import OllamaLLM
+from .factory import LLMFactory

 __all__ = [
     "LLMStrategy",
     "LLMResponse",
     "FakeLLM",
     "Message",
     "OpenAILLM",
     "GeminiLLM",
     "OllamaLLM",
+    "LLMFactory",
 ]
```

---

### [NEW] `src/tasktests/phase2/test_llm_factory.py`

```python
"""
LLMFactory 통합 테스트

각 Provider별 LLM 생성 및 FakeLLM 테스트.
실제 API 호출이 필요한 테스트는 환경변수 없으면 skip.
"""

import os
import pytest

from core.llm import LLMFactory, LLMStrategy, FakeLLM
from config.models import (
    OpenAILLMConfig,
    GeminiLLMConfig,
    OllamaLLMConfig,
)


class TestLLMFactoryFake:
    """FakeLLM 테스트 (외부 의존성 없음)"""

    def test_create_fake_default_response(self):
        """기본 응답으로 FakeLLM 생성"""
        llm = LLMFactory.create_fake()
        assert isinstance(llm, FakeLLM)

        response = llm.generate([{"role": "user", "content": "Hello"}])
        assert response.content == "This is a fake response."

    def test_create_fake_custom_response(self):
        """커스텀 응답으로 FakeLLM 생성"""
        llm = LLMFactory.create_fake(response="Custom answer")
        response = llm.generate([{"role": "user", "content": "Test"}])
        assert response.content == "Custom answer"


class TestLLMFactoryOpenAI:
    """OpenAI LLM Factory 테스트"""

    @pytest.fixture
    def api_key(self):
        key = os.getenv("OPENAI_API_KEY")
        if not key:
            pytest.skip("OPENAI_API_KEY not set")
        return key

    def test_create_openai_from_config(self, api_key):
        """Config로 OpenAI LLM 생성"""
        config = OpenAILLMConfig(model_name="gpt-4o-mini", api_key=api_key)
        llm = LLMFactory.create(config)

        assert llm.model_name == "gpt-4o-mini"

    def test_openai_generate(self, api_key):
        """OpenAI 실제 API 호출 테스트"""
        config = OpenAILLMConfig(model_name="gpt-4o-mini", api_key=api_key)
        llm = LLMFactory.create(config)

        response = llm.generate([
            {"role": "user", "content": "Say 'hello' only."}
        ], temperature=0.0, max_tokens=10)

        assert "hello" in response.content.lower()


class TestLLMFactoryGemini:
    """Gemini LLM Factory 테스트"""

    @pytest.fixture
    def api_key(self):
        key = os.getenv("GOOGLE_API_KEY")
        if not key:
            pytest.skip("GOOGLE_API_KEY not set")
        return key

    def test_create_gemini_from_config(self, api_key):
        """Config로 Gemini LLM 생성"""
        config = GeminiLLMConfig(model_name="gemini-1.5-flash", api_key=api_key)
        llm = LLMFactory.create(config)

        assert llm.model_name == "gemini-1.5-flash"


class TestLLMFactoryOllama:
    """Ollama LLM Factory 테스트 (로컬 서버 필요)"""

    def test_create_ollama_from_config(self):
        """Config로 Ollama LLM 생성 (인스턴스 생성만)"""
        config = OllamaLLMConfig(model_name="llama3")
        llm = LLMFactory.create(config)

        assert llm.model_name == "llama3"
        assert llm.base_url == "http://localhost:11434"


class TestLLMFactoryErrors:
    """Factory 에러 케이스 테스트"""

    def test_invalid_provider_raises_error(self):
        """잘못된 provider 에러"""
        # 직접 config를 조작하여 테스트
        config = OpenAILLMConfig()
        config.provider = "invalid"  # type: ignore

        with pytest.raises(ValueError, match="Unknown provider"):
            LLMFactory.create(config)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
```

---

## Verification Plan

### Automated Tests

```bash
# 전체 테스트 실행 (API 키 없으면 일부 skip)
cd /Users/imseungmin/work/portfolio/obsidian_RAG/obrag
python -m pytest src/tasktests/phase2/test_llm_factory.py -v

# FakeLLM만 테스트 (외부 의존성 없음)
python -m pytest src/tasktests/phase2/test_llm_factory.py::TestLLMFactoryFake -v
```

### Manual Verification

1. **OpenAI API 호출 확인** (OPENAI_API_KEY 설정 시):

   ```bash
   OPENAI_API_KEY=sk-... python -m pytest src/tasktests/phase2/test_llm_factory.py::TestLLMFactoryOpenAI -v
   ```

2. **Gemini API 호출 확인** (GOOGLE_API_KEY 설정 시):

   ```bash
   GOOGLE_API_KEY=... python -m pytest src/tasktests/phase2/test_llm_factory.py::TestLLMFactoryGemini -v
   ```

3. **Ollama 연동 확인** (로컬 서버 실행 시):

   ```bash
   # Ollama 서버 시작 후
   python -c "
   from core.llm import LLMFactory
   from config.models import OllamaLLMConfig

   config = OllamaLLMConfig(model_name='llama3')
   llm = LLMFactory.create(config)
   response = llm.generate([{'role': 'user', 'content': 'Hello'}])
   print(response.content)
   "
   ```

---

## 요약

| 항목            | 내용                                       |
| --------------- | ------------------------------------------ |
| **신규 파일**   | `src/core/llm/factory.py`                  |
| **수정 파일**   | `src/core/llm/__init__.py`                 |
| **테스트 파일** | `src/tasktests/phase2/test_llm_factory.py` |
| **참고 패턴**   | `EmbedderFactory` (동일 구조)              |
| **외부 의존성** | 없음 (기존 LLM 구현체 재사용)              |
| **예상 소요**   | 1-2시간                                    |
