"""
Sentence Transformer Embedding Implementation

HuggingFace sentence-transformers 라이브러리를 사용한 EmbeddingStrategy 구현체.
로컬에서 실행되며, 다양한 사전학습 모델 지원.
"""

from types import ModuleType
from typing import ClassVar, Protocol, cast, override

from .strategy import EmbeddingStrategy, Vector


class _ArrayLike(Protocol):
    def tolist(self) -> list[list[float]]: ...


class _SentenceTransformerLike(Protocol):
    def encode(self, texts: list[str], *, convert_to_numpy: bool) -> _ArrayLike: ...

    def get_sentence_embedding_dimension(self) -> int: ...


class _SentenceTransformerCtor(Protocol):
    def __call__(self, model_name: str) -> _SentenceTransformerLike: ...


class SentenceTransformerEmbedder(EmbeddingStrategy):
    """
    Sentence Transformer 임베딩 구현체.

    HuggingFace sentence-transformers 모델을 사용하여 임베딩 생성.
    최초 사용 시 모델을 다운로드하며, 이후 캐시된 모델 사용.

    사용법:
        embedder = SentenceTransformerEmbedder()  # 기본: BAAI/bge-m3
        embedder = SentenceTransformerEmbedder(model_name="dragonkue/BGE-m3-ko")
        vectors = embedder.embed(["Hello", "World"])
    """

    MODEL_DIMENSIONS: ClassVar[dict[str, int]] = {
        "BAAI/bge-m3": 1024,
        "dragonkue/BGE-m3-ko": 1024,
    }

    def __init__(self, model_name: str = "BAAI/bge-m3"):
        """
        Args:
            model_name: HuggingFace 모델 ID (예: "BAAI/bge-m3")
        """
        self.model_name: str = model_name
        self._model: _SentenceTransformerLike | None = None
        self._dimension: int | None = None

    def _load_model(self) -> None:
        """모델 로드 (최초 1회)"""
        if self._model is not None:
            return
        try:
            import importlib

            module: ModuleType = importlib.import_module("sentence_transformers")
        except ModuleNotFoundError as exc:
            raise ImportError(
                "sentence-transformers 패키지가 필요합니다. 설치: pip install sentence-transformers"
            ) from exc
        sentence_transformer = cast(
            _SentenceTransformerCtor, module.SentenceTransformer
        )
        model = sentence_transformer(self.model_name)
        self._model = model

        try:
            self._dimension = model.get_sentence_embedding_dimension()
        except Exception:
            self._dimension = self.MODEL_DIMENSIONS.get(self.model_name, 1024)

    @override
    def embed(self, texts: list[str]) -> list[Vector]:
        """
        텍스트 리스트를 벡터 리스트로 변환.

        Args:
            texts: 임베딩할 텍스트 리스트

        Returns:
            임베딩 벡터 리스트
        """
        if not texts:
            return []

        self._load_model()
        assert self._model is not None
        embeddings = self._model.encode(texts, convert_to_numpy=True)
        return embeddings.tolist()

    @property
    @override
    def dimension(self) -> int:
        """임베딩 벡터 차원"""
        if self._dimension is not None:
            return self._dimension
        return self.MODEL_DIMENSIONS.get(self.model_name, 1024)

    @override
    def __repr__(self) -> str:
        return f"SentenceTransformerEmbedder(model='{self.model_name}', dimension={self.dimension})"
