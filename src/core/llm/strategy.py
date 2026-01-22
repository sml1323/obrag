"""
LLM Strategy Pattern

LLM 호출을 위한 Protocol 및 테스트용 FakeLLM 구현.
의존성 주입을 통해 테스트 용이성과 LLM 교체 유연성 확보.
"""

from dataclasses import dataclass
from typing import List, Optional, Protocol


# ============================================================================
# Type Aliases
# ============================================================================

Message = dict  # {"role": "user"|"assistant"|"system", "content": str}


# ============================================================================
# Data Classes
# ============================================================================

@dataclass
class LLMResponse:
    """LLM 응답 데이터"""
    content: str
    model: str
    usage: dict  # {"input_tokens": int, "output_tokens": int}


# ============================================================================
# Protocol Definition
# ============================================================================

class LLMStrategy(Protocol):
    """
    LLM 전략 Protocol.
    
    모든 LLM 구현체는 이 프로토콜을 구현해야 합니다.
    """
    
    def generate(
        self,
        messages: List[Message],
        *,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        """
        메시지 기반 응답 생성.
        
        Args:
            messages: 대화 메시지 리스트
            temperature: 응답 다양성 (0.0 ~ 2.0)
            max_tokens: 최대 토큰 수 (None이면 모델 기본값)
        
        Returns:
            LLMResponse 객체
        """
        ...
    
    @property
    def model_name(self) -> str:
        """사용 중인 모델 이름"""
        ...


# ============================================================================
# Fake LLM (Testing)
# ============================================================================

class FakeLLM:
    """
    테스트용 가짜 LLM.
    
    실제 API 호출 없이 빠르게 테스트 가능.
    응답 내용을 직접 지정할 수 있어 예측 가능한 테스트 작성에 유용.
    """
    
    def __init__(self, response: str = "This is a fake response."):
        """
        Args:
            response: 반환할 고정 응답 문자열
        """
        self._response = response
        self._model_name = "fake-llm"
    
    def generate(
        self,
        messages: List[Message],
        *,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        """고정된 응답을 반환"""
        return LLMResponse(
            content=self._response,
            model=self._model_name,
            usage={"input_tokens": 10, "output_tokens": 5}
        )
    
    @property
    def model_name(self) -> str:
        return self._model_name
