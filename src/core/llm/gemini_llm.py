"""
Gemini LLM Implementation

Google Gemini API를 사용한 LLMStrategy 구현체.
"""

from typing import List, Optional

from google import genai
from google.genai import types

from .strategy import LLMResponse, Message


class GeminiLLM:
    """
    Google Gemini LLM 구현체.
    
    Gemini 모델을 사용한 텍스트 생성.
    """
    
    def __init__(
        self,
        model_name: str = "gemini-2.0-flash",
        api_key: Optional[str] = None,
    ):
        """
        Args:
            model_name: 사용할 Gemini 모델 이름
            api_key: Gemini API 키 (None이면 환경변수 GOOGLE_API_KEY 사용)
        """
        self._model_name = model_name
        self._client = genai.Client(api_key=api_key)
    
    def generate(
        self,
        messages: List[Message],
        *,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        """
        Gemini API 호출.
        
        Args:
            messages: 대화 메시지 리스트 (OpenAI 형식)
            temperature: 응답 다양성 (0.0 ~ 2.0)
            max_tokens: 최대 토큰 수
        
        Returns:
            LLMResponse 객체
        """
        # OpenAI 형식 메시지를 Gemini 형식으로 변환
        contents, system_instruction = self._convert_messages(messages)
        
        # Gemini 설정 구성
        config = types.GenerateContentConfig(
            temperature=temperature,
            max_output_tokens=max_tokens,
            system_instruction=system_instruction,
        )
        
        response = self._client.models.generate_content(
            model=self._model_name,
            contents=contents,
            config=config,
        )
        
        return LLMResponse(
            content=response.text or "",
            model=self._model_name,
            usage={
                "input_tokens": response.usage_metadata.prompt_token_count if response.usage_metadata else 0,
                "output_tokens": response.usage_metadata.candidates_token_count if response.usage_metadata else 0,
            }
        )
    
    def _convert_messages(self, messages: List[Message]) -> tuple[list, Optional[str]]:
        """
        OpenAI 형식 메시지를 Gemini 형식으로 변환.
        
        Args:
            messages: OpenAI 형식 메시지 리스트
        
        Returns:
            (contents, system_instruction) 튜플
        """
        contents = []
        system_instruction = None
        
        for msg in messages:
            role = msg["role"]
            content = msg["content"]
            
            if role == "system":
                system_instruction = content
            elif role == "user":
                contents.append(types.Content(
                    role="user",
                    parts=[types.Part(text=content)]
                ))
            elif role == "assistant":
                contents.append(types.Content(
                    role="model",
                    parts=[types.Part(text=content)]
                ))
        
        return contents, system_instruction
    
    @property
    def model_name(self) -> str:
        return self._model_name
