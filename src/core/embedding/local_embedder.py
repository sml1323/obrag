"""
Local Embedding Implementation (Deprecated)

DEPRECATED: LocalEmbedder는 SentenceTransformerEmbedder로 대체되었습니다.
기존 코드 호환성을 위해 유지되며, 내부적으로 SentenceTransformerEmbedder를 사용합니다.
"""

import warnings
from typing import ClassVar, override

from .strategy import Vector
from .sentence_transformer_embedder import SentenceTransformerEmbedder


class LocalEmbedder:
    """
    로컬 임베딩 모델 구현체 (Deprecated).

    DEPRECATED: SentenceTransformerEmbedder를 직접 사용하세요.
    기존 코드 호환성을 위해 유지됩니다.
    """

    # 기존 모델명 -> HuggingFace 모델 ID 매핑
    MODEL_NAME_MAPPING: ClassVar[dict[str, str]] = {
        "bge-m3": "BAAI/bge-m3",
        "bge-large-zh": "BAAI/bge-large-zh-v1.5",
        "bge-base-en": "BAAI/bge-base-en-v1.5",
    }

    MODEL_DIMENSIONS: ClassVar[dict[str, int]] = {
        "bge-m3": 1024,
        "bge-large-zh": 1024,
        "bge-base-en": 768,
    }

    def __init__(self, model_name: str = "bge-m3") -> None:
        warnings.warn(
            (
                "LocalEmbedder is deprecated. Use SentenceTransformerEmbedder directly. "
                f"Example: SentenceTransformerEmbedder(model_name='{self.MODEL_NAME_MAPPING.get(model_name, model_name)}')"
            ),
            DeprecationWarning,
            stacklevel=2,
        )

        self.model_name: str = model_name
        self._dimension: int = self.MODEL_DIMENSIONS.get(model_name, 1024)

        # HuggingFace 모델 ID로 매핑
        hf_model_name = self.MODEL_NAME_MAPPING.get(model_name, model_name)
        self._delegate: SentenceTransformerEmbedder = SentenceTransformerEmbedder(
            model_name=hf_model_name
        )

    def embed(self, texts: list[str]) -> list[Vector]:
        """SentenceTransformerEmbedder에 위임"""
        return self._delegate.embed(texts)

    @property
    def dimension(self) -> int:
        return self._delegate.dimension

    @override
    def __repr__(self) -> str:
        return f"LocalEmbedder(model='{self.model_name}', dimension={self.dimension}, deprecated=True)"
