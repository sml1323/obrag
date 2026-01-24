"""
LLM Factory

Config 기반으로 적절한 LLM을 생성하는 Factory 패턴 구현.
DI(의존성 주입) 원칙에 따라 LLM 교체를 용이하게 합니다.
"""

from typing import Union

from .strategy import LLMStrategy, FakeLLM
from .openai_llm import OpenAILLM
from .gemini_llm import GeminiLLM
from .ollama_llm import OllamaLLM

# Config imports
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from config.models import (
    OpenAILLMConfig,
    GeminiLLMConfig,
    OllamaLLMConfig,
    LLMConfig,
)


class LLMFactory:
    """
    Config 기반 LLM 팩토리.

    설정 객체를 받아 적절한 LLM 인스턴스를 생성합니다.

    사용법:
        # OpenAI LLM 생성
        config = OpenAILLMConfig(model_name="gpt-4o-mini")
        llm = LLMFactory.create(config)

        # Gemini LLM 생성
        config = GeminiLLMConfig(model_name="gemini-1.5-flash")
        llm = LLMFactory.create(config)

        # Ollama LLM 생성
        config = OllamaLLMConfig(model_name="llama3")
        llm = LLMFactory.create(config)

        # 테스트용 Fake LLM
        llm = LLMFactory.create_fake(response="Test response")
    """

    @staticmethod
    def create(config: LLMConfig) -> LLMStrategy:
        """
        Config 기반 LLM 생성.

        Args:
            config: OpenAILLMConfig, GeminiLLMConfig, 또는 OllamaLLMConfig

        Returns:
            LLMStrategy 프로토콜을 구현한 LLM 인스턴스

        Raises:
            ValueError: 알 수 없는 provider인 경우
            TypeError: config 타입이 provider와 불일치하는 경우
        """
        if config.provider == "openai":
            if not isinstance(config, OpenAILLMConfig):
                raise TypeError("OpenAI provider requires OpenAILLMConfig")
            return OpenAILLM(
                model_name=config.model_name,
                api_key=config.api_key,
            )

        elif config.provider == "gemini":
            if not isinstance(config, GeminiLLMConfig):
                raise TypeError("Gemini provider requires GeminiLLMConfig")
            return GeminiLLM(
                model_name=config.model_name,
                api_key=config.api_key,
            )

        elif config.provider == "ollama":
            if not isinstance(config, OllamaLLMConfig):
                raise TypeError("Ollama provider requires OllamaLLMConfig")
            return OllamaLLM(
                model_name=config.model_name,
                base_url=config.base_url,
            )

        else:
            raise ValueError(
                f"Unknown provider: {config.provider}. "
                "Supported providers: 'openai', 'gemini', 'ollama'"
            )

    @staticmethod
    def create_fake(response: str = "This is a fake response.") -> FakeLLM:
        """
        테스트용 Fake LLM 생성.

        Args:
            response: 반환할 고정 응답 문자열

        Returns:
            FakeLLM 인스턴스
        """
        return FakeLLM(response=response)
