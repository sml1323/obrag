"""
Gemini LLM Implementation (Skeleton)

Google Gemini API를 사용한 LLMStrategy 구현체.
추후 구현 예정.
"""

from typing import List, Optional

from .strategy import LLMResponse, Message


class GeminiLLM:
    """
    Gemini LLM 구현체 (Skeleton).
    
    추후 구현 예정. 현재는 NotImplementedError를 발생시킵니다.
    """
    
    def __init__(self, model_name: str = "gemini-1.5-flash"):
        """
        Args:
            model_name: 사용할 Gemini 모델 이름
        """
        self._model_name = model_name
    
    def generate(
        self,
        messages: List[Message],
        *,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        """Gemini API 호출 (미구현)"""
        raise NotImplementedError("GeminiLLM is not implemented yet")
    
    @property
    def model_name(self) -> str:
        return self._model_name
