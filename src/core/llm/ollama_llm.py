"""
Ollama LLM Implementation

로컬 Ollama 서버를 사용한 LLMStrategy 구현체.
OpenAI 호환 API를 활용하여 구현.
"""

from typing import Iterator, List, Optional

from openai import OpenAI

from .strategy import LLMResponse, Message


class OllamaLLM:
    """
    Ollama LLM 구현체.
    
    로컬 Ollama 서버를 통해 LLM 호출.
    OpenAI 호환 API를 사용하므로 추가 의존성 없이 구현.
    """
    
    def __init__(
        self,
        model_name: str = "llama3.2",
        base_url: str = "http://localhost:11434/v1",
    ):
        """
        Args:
            model_name: 사용할 Ollama 모델 이름
            base_url: Ollama 서버 URL (OpenAI 호환 엔드포인트)
        """
        self._model_name = model_name
        self._base_url = base_url
        self._client = OpenAI(
            base_url=base_url,
            api_key="ollama",  # 필수이지만 Ollama에서 무시됨
        )
    
    def generate(
        self,
        messages: List[Message],
        *,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        """
        Ollama API 호출 (OpenAI 호환).
        
        Args:
            messages: 대화 메시지 리스트
            temperature: 응답 다양성 (0.0 ~ 2.0)
            max_tokens: 최대 토큰 수
        
        Returns:
            LLMResponse 객체
        """
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
    
    def stream_generate(
        self,
        messages: List[Message],
        *,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> Iterator[str]:
        """
        Ollama 스트리밍 응답 생성 (OpenAI 호환).
        
        Args:
            messages: 대화 메시지 리스트
            temperature: 응답 다양성
            max_tokens: 최대 토큰 수
        
        Yields:
            응답 텍스트 청크
        """
        response = self._client.chat.completions.create(
            model=self._model_name,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True,
        )
        
        for chunk in response:
            if chunk.choices and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
    
    @property
    def model_name(self) -> str:
        return self._model_name
    
    @property
    def base_url(self) -> str:
        return self._base_url
