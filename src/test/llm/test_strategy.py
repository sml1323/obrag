"""
LLM Strategy Unit Tests

FakeLLM과 LLMResponse 데이터 구조를 테스트합니다.
"""

import pytest
import sys
from pathlib import Path

# src 디렉토리를 path에 추가
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.llm import LLMStrategy, LLMResponse, FakeLLM, Message
from config.models import OpenAILLMConfig, GeminiLLMConfig, OllamaLLMConfig


class TestLLMResponse:
    """LLMResponse 데이터 구조 테스트"""
    
    def test_create_response(self):
        """LLMResponse 생성 테스트"""
        response = LLMResponse(
            content="Hello, world!",
            model="gpt-4o-mini",
            usage={"input_tokens": 10, "output_tokens": 5}
        )
        
        assert response.content == "Hello, world!"
        assert response.model == "gpt-4o-mini"
        assert response.usage["input_tokens"] == 10
        assert response.usage["output_tokens"] == 5


class TestFakeLLM:
    """FakeLLM 테스트"""
    
    def test_default_response(self):
        """기본 응답 테스트"""
        llm = FakeLLM()
        messages = [{"role": "user", "content": "Hello"}]
        
        response = llm.generate(messages)
        
        assert response.content == "This is a fake response."
        assert response.model == "fake-llm"
        assert "input_tokens" in response.usage
        assert "output_tokens" in response.usage
    
    def test_custom_response(self):
        """커스텀 응답 테스트"""
        custom_text = "Custom response for testing"
        llm = FakeLLM(response=custom_text)
        messages = [{"role": "user", "content": "Test"}]
        
        response = llm.generate(messages)
        
        assert response.content == custom_text
    
    def test_model_name_property(self):
        """모델 이름 속성 테스트"""
        llm = FakeLLM()
        assert llm.model_name == "fake-llm"
    
    def test_with_parameters(self):
        """파라미터 전달 테스트"""
        llm = FakeLLM()
        messages = [
            {"role": "system", "content": "You are helpful."},
            {"role": "user", "content": "Hello"}
        ]
        
        response = llm.generate(
            messages,
            temperature=0.5,
            max_tokens=100
        )
        
        # FakeLLM은 파라미터를 무시하지만 에러 없이 동작해야 함
        assert response.content == "This is a fake response."


class TestLLMStrategyProtocol:
    """LLMStrategy Protocol 준수 테스트"""
    
    def test_fake_llm_implements_protocol(self):
        """FakeLLM이 LLMStrategy 프로토콜을 준수하는지 테스트"""
        llm = FakeLLM()
        
        # Protocol 메서드 존재 확인
        assert hasattr(llm, 'generate')
        assert hasattr(llm, 'model_name')
        assert callable(llm.generate)


class TestLLMConfig:
    """LLM Config 테스트"""
    
    def test_openai_config_default(self):
        """OpenAI Config 기본값 테스트"""
        config = OpenAILLMConfig()
        
        assert config.provider == "openai"
        assert config.model_name == "gpt-4o-mini"
        assert config.api_key is None
    
    def test_openai_config_custom(self):
        """OpenAI Config 커스텀 값 테스트"""
        config = OpenAILLMConfig(
            model_name="gpt-4o",
            api_key="sk-test-key"
        )
        
        assert config.model_name == "gpt-4o"
        assert config.api_key == "sk-test-key"
    
    def test_openai_config_invalid_model(self):
        """OpenAI Config 잘못된 모델명 테스트"""
        with pytest.raises(ValueError, match="Invalid OpenAI LLM model"):
            OpenAILLMConfig(model_name="invalid-model")
    
    def test_openai_config_invalid_api_key(self):
        """OpenAI Config 잘못된 API 키 테스트"""
        with pytest.raises(ValueError, match="must start with"):
            OpenAILLMConfig(api_key="invalid-key")
    
    def test_gemini_config_default(self):
        """Gemini Config 기본값 테스트"""
        config = GeminiLLMConfig()
        
        assert config.provider == "gemini"
        assert config.model_name == "gemini-1.5-flash"
    
    def test_gemini_config_invalid_model(self):
        """Gemini Config 잘못된 모델명 테스트"""
        with pytest.raises(ValueError, match="Invalid Gemini LLM model"):
            GeminiLLMConfig(model_name="invalid-model")
    
    def test_ollama_config_default(self):
        """Ollama Config 기본값 테스트"""
        config = OllamaLLMConfig()
        
        assert config.provider == "ollama"
        assert config.model_name == "llama3"
        assert config.base_url == "http://localhost:11434"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
