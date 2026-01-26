"""
OpenAI LLM Implementation

OpenAI Chat Completion API를 사용한 LLMStrategy 구현체.
"""

from typing import Iterator, List, Optional

from openai import OpenAI

from .strategy import LLMResponse, Message


class OpenAILLM:
    """
    OpenAI LLM 구현체.
    
    GPT 모델을 사용한 텍스트 생성.
    """
    
    def __init__(
        self,
        model_name: str = "gpt-4o-mini",
        api_key: Optional[str] = None,
    ):
        """
        Args:
            model_name: 사용할 OpenAI 모델 이름
            api_key: OpenAI API 키 (None이면 환경변수 OPENAI_API_KEY 사용)
        """
        self._model_name = model_name
        self._client = OpenAI(api_key=api_key)
    
    def generate(
        self,
        messages: List[Message],
        *,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        """
        OpenAI Chat Completion API 호출.
        
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
        OpenAI 스트리밍 응답 생성.
        
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
