"""
LLMFactory 통합 테스트

각 Provider별 LLM 생성 및 FakeLLM 테스트.
실제 API 호출이 필요한 테스트는 환경변수 없으면 skip.
"""

import os
import pytest

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.llm import LLMFactory, LLMStrategy, FakeLLM
from core.llm.openai_llm import OpenAILLM
from core.llm.gemini_llm import GeminiLLM
from core.llm.ollama_llm import OllamaLLM
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

        assert isinstance(llm, OpenAILLM)
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

        assert isinstance(llm, GeminiLLM)
        assert llm.model_name == "gemini-1.5-flash"


class TestLLMFactoryOllama:
    """Ollama LLM Factory 테스트 (로컬 서버 필요)"""

    def test_create_ollama_from_config(self):
        """Config로 Ollama LLM 생성 (인스턴스 생성만)"""
        config = OllamaLLMConfig(model_name="llama3")
        llm = LLMFactory.create(config)

        assert isinstance(llm, OllamaLLM)
        assert llm.model_name == "llama3"
        assert llm.base_url == "http://localhost:11434"

    def test_create_ollama_custom_url(self):
        """커스텀 base_url로 Ollama LLM 생성"""
        config = OllamaLLMConfig(model_name="mistral", base_url="http://192.168.1.100:11434")
        llm = LLMFactory.create(config)

        assert llm.model_name == "mistral"
        assert llm.base_url == "http://192.168.1.100:11434"


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
