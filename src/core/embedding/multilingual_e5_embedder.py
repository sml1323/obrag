"""
Multilingual E5 Embedding Implementation

Microsoft multilingual-e5-large-instruct를 사용한 EmbeddingStrategy 구현체.
한국어-영어 cross-lingual retrieval에 최적화.

E5 모델은 query/passage prefix가 중요:
- 쿼리: "query: {text}"
- 문서: "passage: {text}"
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


class MultilingualE5Embedder(EmbeddingStrategy):
    """
    Microsoft Multilingual E5 임베더.

    한국어-영어 cross-lingual retrieval에 최적화.
    E5 모델은 instruction prefix가 중요하며, query와 document에 다른 prefix 사용.

    사용법:
        embedder = MultilingualE5Embedder()  # 기본: multilingual-e5-large-instruct

        # 문서 임베딩 (passage prefix)
        doc_vectors = embedder.embed_documents(["문서1", "문서2"])

        # 쿼리 임베딩 (query prefix)
        query_vector = embedder.embed_query("검색어")

        # 또는 prefix를 직접 지정
        vectors = embedder.embed(["텍스트"], is_query=True)
    """

    DEFAULT_MODEL = "intfloat/multilingual-e5-large-instruct"

    MODEL_DIMENSIONS: ClassVar[dict[str, int]] = {
        "intfloat/multilingual-e5-large-instruct": 1024,
        "intfloat/multilingual-e5-large": 1024,
        "intfloat/multilingual-e5-base": 768,
        "intfloat/multilingual-e5-small": 384,
    }

    def __init__(self, model_name: str = DEFAULT_MODEL):
        """
        Args:
            model_name: HuggingFace 모델 ID (예: "intfloat/multilingual-e5-large-instruct")
        """
        self._model_name: str = model_name
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
        model = sentence_transformer(self._model_name)
        self._model = model

        try:
            self._dimension = model.get_sentence_embedding_dimension()
        except Exception:
            self._dimension = self.MODEL_DIMENSIONS.get(self._model_name, 1024)

    def _add_prefix(self, texts: list[str], is_query: bool) -> list[str]:
        """E5 모델에 필요한 prefix 추가"""
        if is_query:
            return [f"query: {t}" for t in texts]
        else:
            return [f"passage: {t}" for t in texts]

    @override
    def embed(self, texts: list[str], *, is_query: bool = False) -> list[Vector]:
        """
        텍스트 리스트를 벡터 리스트로 변환.

        Args:
            texts: 임베딩할 텍스트 리스트
            is_query: True면 쿼리용 prefix("query:") 추가,
                      False면 문서용 prefix("passage:") 추가

        Returns:
            임베딩 벡터 리스트
        """
        if not texts:
            return []

        self._load_model()
        assert self._model is not None

        prefixed_texts = self._add_prefix(texts, is_query)
        embeddings = self._model.encode(prefixed_texts, convert_to_numpy=True)
        return embeddings.tolist()

    def embed_query(self, query: str) -> Vector:
        """
        쿼리 전용 임베딩 (query prefix 자동 추가).

        Args:
            query: 검색 쿼리 문자열

        Returns:
            쿼리 임베딩 벡터
        """
        return self.embed([query], is_query=True)[0]

    def embed_documents(self, documents: list[str]) -> list[Vector]:
        """
        문서 전용 임베딩 (passage prefix 자동 추가).

        Args:
            documents: 임베딩할 문서 리스트

        Returns:
            문서 임베딩 벡터 리스트
        """
        return self.embed(documents, is_query=False)

    @property
    @override
    def dimension(self) -> int:
        """임베딩 벡터 차원"""
        if self._dimension is not None:
            return self._dimension
        return self.MODEL_DIMENSIONS.get(self._model_name, 1024)

    @property
    @override
    def model_name(self) -> str:
        """사용 중인 모델 이름"""
        return self._model_name

    @override
    def __repr__(self) -> str:
        return f"MultilingualE5Embedder(model='{self._model_name}', dimension={self.dimension})"
