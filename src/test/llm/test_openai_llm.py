"""
OpenAI LLM Integration Tests

OpenAI API 연동 테스트입니다.
실제 API 호출이 필요하며, OPENAI_API_KEY 환경변수가 설정되어 있어야 합니다.
"""

import os
import pytest
import sys
from pathlib import Path

# src 디렉토리를 path에 추가
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.llm import OpenAILLM, LLMResponse


@pytest.mark.integration
class TestOpenAILLMIntegration:
    """OpenAI LLM 통합 테스트 (실제 API 호출)"""
    
    @pytest.fixture
    def llm(self):
        """OpenAI LLM 인스턴스 생성"""
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            pytest.skip("OPENAI_API_KEY not set")
        return OpenAILLM(model_name="gpt-4o-mini", api_key=api_key)
    
    def test_simple_generation(self, llm):
        """간단한 응답 생성 테스트"""
        messages = [
            {"role": "user", "content": "Say 'Hello' and nothing else."}
        ]
        
        response = llm.generate(messages, temperature=0.0, max_tokens=10)
        
        assert isinstance(response, LLMResponse)
        assert "Hello" in response.content or "hello" in response.content.lower()
        assert response.model is not None
        assert response.usage["input_tokens"] > 0
        assert response.usage["output_tokens"] > 0
    
    def test_system_message(self, llm):
        """시스템 메시지 테스트"""
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "What is 2+2? Answer with just the number."}
        ]
        
        response = llm.generate(messages, temperature=0.0, max_tokens=10)
        
        assert isinstance(response, LLMResponse)
        assert "4" in response.content
    
    def test_model_name_property(self, llm):
        """모델 이름 속성 테스트"""
        assert llm.model_name == "gpt-4o-mini"


class TestOpenAILLMUnit:
    """OpenAI LLM 단위 테스트 (API 호출 없음)"""
    
    def test_model_name_access(self):
        """모델 이름 접근 테스트 (클라이언트 초기화 없이)"""
        # OpenAILLM 클래스가 import 가능한지 확인
        from core.llm import OpenAILLM
        assert OpenAILLM is not None
    
    def test_custom_api_key(self):
        """커스텀 API 키 테스트"""
        # API 키만 설정하고 실제 호출은 하지 않음
        llm = OpenAILLM(api_key="sk-test-fake-key")
        
        assert llm.model_name == "gpt-4o-mini"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
