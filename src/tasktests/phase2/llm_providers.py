"""
LLM Provider 구현체 테스트

GeminiLLM, OllamaLLM 구현체의 기본 동작을 테스트합니다.
API 키 또는 서버 연결이 없는 경우 해당 테스트를 건너뜁니다.
"""

import os
import pytest
from unittest.mock import Mock, patch, MagicMock

# src 경로 추가
import sys
from pathlib import Path

src_path = Path(__file__).parent.parent.parent
sys.path.insert(0, str(src_path))

from core.llm import LLMResponse, GeminiLLM, OllamaLLM


# ============================================================================
# GeminiLLM Tests
# ============================================================================

class TestGeminiLLM:
    """GeminiLLM 구현체 테스트"""
    
    def test_model_name_property(self):
        """model_name 속성이 올바르게 반환되는지 테스트"""
        with patch("core.llm.gemini_llm.genai.Client"):
            llm = GeminiLLM(model_name="gemini-2.0-flash")
            assert llm.model_name == "gemini-2.0-flash"
    
    def test_generate_with_mock(self):
        """Mock을 사용한 generate() 메서드 테스트"""
        with patch("core.llm.gemini_llm.genai.Client") as mock_client_cls:
            # Mock 설정
            mock_client = MagicMock()
            mock_client_cls.return_value = mock_client
            
            mock_response = MagicMock()
            mock_response.text = "Hello from Gemini!"
            mock_response.usage_metadata = MagicMock()
            mock_response.usage_metadata.prompt_token_count = 10
            mock_response.usage_metadata.candidates_token_count = 5
            
            mock_client.models.generate_content.return_value = mock_response
            
            # 테스트 실행
            llm = GeminiLLM(model_name="gemini-2.0-flash", api_key="test-key")
            messages = [{"role": "user", "content": "Hi"}]
            result = llm.generate(messages)
            
            # 검증
            assert isinstance(result, LLMResponse)
            assert result.content == "Hello from Gemini!"
            assert result.model == "gemini-2.0-flash"
            assert result.usage["input_tokens"] == 10
            assert result.usage["output_tokens"] == 5
    
    def test_convert_messages_with_system(self):
        """system 메시지 변환 테스트"""
        with patch("core.llm.gemini_llm.genai.Client"):
            llm = GeminiLLM()
            messages = [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Hello"},
                {"role": "assistant", "content": "Hi there!"},
                {"role": "user", "content": "How are you?"},
            ]
            
            contents, system_instruction = llm._convert_messages(messages)
            
            assert system_instruction == "You are a helpful assistant."
            assert len(contents) == 3  # user, assistant, user
    
    @pytest.mark.skipif(
        not os.getenv("GOOGLE_API_KEY"),
        reason="GOOGLE_API_KEY not set"
    )
    def test_integration_real_api(self):
        """실제 Gemini API 호출 테스트 (API 키 필요)"""
        llm = GeminiLLM()
        messages = [{"role": "user", "content": "Say 'test' only."}]
        
        result = llm.generate(messages, temperature=0.0, max_tokens=10)
        
        assert isinstance(result, LLMResponse)
        assert len(result.content) > 0
        print(f"\n[Gemini Response] {result.content}")
        print(f"[Usage] input={result.usage['input_tokens']}, output={result.usage['output_tokens']}")


# ============================================================================
# OllamaLLM Tests
# ============================================================================

class TestOllamaLLM:
    """OllamaLLM 구현체 테스트"""
    
    def test_model_name_property(self):
        """model_name 속성이 올바르게 반환되는지 테스트"""
        with patch("core.llm.ollama_llm.OpenAI"):
            llm = OllamaLLM(model_name="llama3.2")
            assert llm.model_name == "llama3.2"
    
    def test_base_url_property(self):
        """base_url 속성이 올바르게 반환되는지 테스트"""
        with patch("core.llm.ollama_llm.OpenAI"):
            llm = OllamaLLM(base_url="http://custom:8080/v1")
            assert llm.base_url == "http://custom:8080/v1"
    
    def test_generate_with_mock(self):
        """Mock을 사용한 generate() 메서드 테스트"""
        with patch("core.llm.ollama_llm.OpenAI") as mock_openai_cls:
            # Mock 설정
            mock_client = MagicMock()
            mock_openai_cls.return_value = mock_client
            
            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.content = "Hello from Ollama!"
            mock_response.model = "llama3.2"
            mock_response.usage = MagicMock()
            mock_response.usage.prompt_tokens = 8
            mock_response.usage.completion_tokens = 4
            
            mock_client.chat.completions.create.return_value = mock_response
            
            # 테스트 실행
            llm = OllamaLLM(model_name="llama3.2")
            messages = [{"role": "user", "content": "Hi"}]
            result = llm.generate(messages)
            
            # 검증
            assert isinstance(result, LLMResponse)
            assert result.content == "Hello from Ollama!"
            assert result.model == "llama3.2"
            assert result.usage["input_tokens"] == 8
            assert result.usage["output_tokens"] == 4
    
    def test_openai_client_initialized_with_correct_params(self):
        """OpenAI 클라이언트가 올바른 파라미터로 초기화되는지 테스트"""
        with patch("core.llm.ollama_llm.OpenAI") as mock_openai_cls:
            OllamaLLM(
                model_name="llama3.2",
                base_url="http://localhost:11434/v1"
            )
            
            mock_openai_cls.assert_called_once_with(
                base_url="http://localhost:11434/v1",
                api_key="ollama",
            )
    
    @pytest.mark.skipif(True, reason="Requires local Ollama server running")
    def test_integration_real_server(self):
        """실제 Ollama 서버 호출 테스트 (서버 실행 필요)"""
        llm = OllamaLLM()
        messages = [{"role": "user", "content": "Say 'test' only."}]
        
        result = llm.generate(messages, temperature=0.0, max_tokens=10)
        
        assert isinstance(result, LLMResponse)
        assert len(result.content) > 0
        print(f"\n[Ollama Response] {result.content}")
        print(f"[Usage] input={result.usage['input_tokens']}, output={result.usage['output_tokens']}")


# ============================================================================
# 실행
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
