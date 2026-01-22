"""
Ollama LLM Implementation (Skeleton)

로컬 Ollama 서버를 사용한 LLMStrategy 구현체.
추후 구현 예정.
"""

from typing import List, Optional

from .strategy import LLMResponse, Message


class OllamaLLM:
    """
    Ollama LLM 구현체 (Skeleton).
    
    로컬 Ollama 서버를 통해 LLM 호출.
    추후 구현 예정. 현재는 NotImplementedError를 발생시킵니다.
    """
    
    def __init__(
        self,
        model_name: str = "llama3",
        base_url: str = "http://localhost:11434",
    ):
        """
        Args:
            model_name: 사용할 Ollama 모델 이름
            base_url: Ollama 서버 URL
        """
        self._model_name = model_name
        self._base_url = base_url
    
    def generate(
        self,
        messages: List[Message],
        *,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        """Ollama API 호출 (미구현)"""
        raise NotImplementedError("OllamaLLM is not implemented yet")
    
    @property
    def model_name(self) -> str:
        return self._model_name
