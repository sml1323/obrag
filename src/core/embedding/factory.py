"""
Embedder Factory

Config 기반으로 적절한 임베더를 생성하는 Factory 패턴 구현.
DI(의존성 주입) 원칙에 따라 임베더 교체를 용이하게 합니다.
"""

from typing import Union

from .strategy import EmbeddingStrategy, FakeEmbedder
from .openai_embedder import OpenAIEmbedder
from .local_embedder import LocalEmbedder
from .ollama_embedder import OllamaEmbedder
from .sentence_transformer_embedder import SentenceTransformerEmbedder
from .multilingual_e5_embedder import MultilingualE5Embedder

# Config imports
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from config.models import (
    OpenAIEmbeddingConfig,
    LocalEmbeddingConfig,
    OllamaEmbeddingConfig,
    SentenceTransformerEmbeddingConfig,
    MultilingualE5EmbeddingConfig,
)


# ============================================================================
# Type Aliases
# ============================================================================

EmbeddingConfig = Union[
    OpenAIEmbeddingConfig,
    LocalEmbeddingConfig,
    OllamaEmbeddingConfig,
    SentenceTransformerEmbeddingConfig,
    MultilingualE5EmbeddingConfig,
]


# ============================================================================
# Embedder Factory
# ============================================================================


class EmbedderFactory:
    """
    Config 기반 임베더 팩토리.

    설정 객체를 받아 적절한 임베더 인스턴스를 생성합니다.

    사용법:
        # OpenAI 임베더 생성
        config = OpenAIEmbeddingConfig(model_name="text-embedding-3-small")
        embedder = EmbedderFactory.create(config)

        # 로컬 임베더 생성 (현재 NotImplementedError)
        config = LocalEmbeddingConfig(model_name="bge-m3")
        embedder = EmbedderFactory.create(config)

        # 테스트용 Fake 임베더
        embedder = EmbedderFactory.create_fake(dimension=8)
    """

    @staticmethod
    def create(config: EmbeddingConfig) -> EmbeddingStrategy:
        """
        Config 기반 임베더 생성.

        Args:
            config: 임베딩 설정 객체

        Returns:
            EmbeddingStrategy 프로토콜을 구현한 임베더

        Raises:
            ValueError: 알 수 없는 provider인 경우
            TypeError: 설정 객체 타입이 올바르지 않은 경우
        """
        if config.provider == "openai":
            if not isinstance(config, OpenAIEmbeddingConfig):
                raise TypeError("OpenAI provider requires OpenAIEmbeddingConfig")
            return OpenAIEmbedder(
                model_name=config.model_name,
                api_key=config.api_key,
            )

        elif config.provider == "local":
            if not isinstance(config, LocalEmbeddingConfig):
                raise TypeError("Local provider requires LocalEmbeddingConfig")
            return LocalEmbedder(
                model_name=config.model_name,
            )

        elif config.provider == "ollama":
            if not isinstance(config, OllamaEmbeddingConfig):
                raise TypeError("Ollama provider requires OllamaEmbeddingConfig")
            return OllamaEmbedder(
                model_name=config.model_name,
                base_url=config.base_url,
            )

        elif config.provider == "sentence_transformers":
            if not isinstance(config, SentenceTransformerEmbeddingConfig):
                raise TypeError(
                    "SentenceTransformer provider requires SentenceTransformerEmbeddingConfig"
                )
            return SentenceTransformerEmbedder(
                model_name=config.model_name,
            )

        elif config.provider == "multilingual_e5":
            if not isinstance(config, MultilingualE5EmbeddingConfig):
                raise TypeError(
                    "MultilingualE5 provider requires MultilingualE5EmbeddingConfig"
                )
            return MultilingualE5Embedder(
                model_name=config.model_name,
            )

        else:
            raise ValueError(
                f"Unknown provider: {config.provider}. "
                "Supported providers: 'openai', 'local', 'ollama', 'sentence_transformers', 'multilingual_e5'"
            )

    @staticmethod
    def create_fake(dimension: int = 8) -> FakeEmbedder:
        """
        테스트용 Fake 임베더 생성.

        Args:
            dimension: 임베딩 벡터 차원

        Returns:
            FakeEmbedder 인스턴스
        """
        return FakeEmbedder(dimension=dimension)

    @staticmethod
    def create_openai(
        model_name: str = "text-embedding-3-small",
        api_key: str | None = None,
    ) -> OpenAIEmbedder:
        """
        OpenAI 임베더 직접 생성 (편의 메서드).

        Args:
            model_name: OpenAI 임베딩 모델 이름
            api_key: API 키 (없으면 환경변수에서 로드)

        Returns:
            OpenAIEmbedder 인스턴스
        """
        return OpenAIEmbedder(model_name=model_name, api_key=api_key)
