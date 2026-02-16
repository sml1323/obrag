"""
Reranker Module

Cross-Encoder 기반 재순위화로 검색 정밀도 향상.
"""

from dataclasses import dataclass
from typing import TYPE_CHECKING, List, Optional, Protocol

if TYPE_CHECKING:
    from .retriever import Retriever, RetrievalResult, RetrievedChunk


class _CrossEncoderLike(Protocol):
    def predict(self, pairs: list[tuple[str, str]]) -> list[float]: ...


class _CrossEncoderCtor(Protocol):
    def __call__(self, model_name: str) -> _CrossEncoderLike: ...


@dataclass
class RankedDocument:
    text: str
    score: float
    original_index: int


class Reranker:
    """
    Cross-Encoder 기반 재순위화.

    초기 검색 결과를 더 정밀하게 정렬합니다.
    Query-Document 쌍을 직접 비교하여 관련성 점수 계산.

    사용법:
        reranker = Reranker()
        ranked = reranker.rerank("검색어", ["문서1", "문서2", ...], top_k=5)
    """

    DEFAULT_MODEL = "cross-encoder/ms-marco-MiniLM-L-6-v2"

    def __init__(self, model_name: str = DEFAULT_MODEL):
        self._model_name = model_name
        self._model: Optional[_CrossEncoderLike] = None

    def _load_model(self) -> None:
        if self._model is not None:
            return
        try:
            from sentence_transformers import CrossEncoder

            self._model = CrossEncoder(self._model_name)
        except ImportError as exc:
            raise ImportError(
                "sentence-transformers 패키지가 필요합니다. 설치: pip install sentence-transformers"
            ) from exc

    def rerank(
        self,
        query: str,
        documents: List[str],
        top_k: int = 5,
    ) -> List[RankedDocument]:
        if not documents:
            return []

        self._load_model()
        assert self._model is not None

        pairs = [(query, doc) for doc in documents]
        scores = self._model.predict(pairs)

        ranked = [
            RankedDocument(text=doc, score=float(score), original_index=i)
            for i, (doc, score) in enumerate(zip(documents, scores))
        ]
        ranked.sort(key=lambda x: x.score, reverse=True)
        return ranked[:top_k]

    @property
    def model_name(self) -> str:
        return self._model_name


class RerankedRetriever:
    """Reranking을 적용한 Retriever 래퍼"""

    def __init__(
        self,
        base_retriever: "Retriever",
        reranker: Reranker,
        initial_k: int = 20,
    ):
        self._base = base_retriever
        self._reranker = reranker
        self._initial_k = initial_k

    def retrieve(
        self,
        query: str,
        top_k: int = 5,
    ) -> "RetrievalResult":
        from .retriever import RetrievalResult, RetrievedChunk

        initial_result = self._base.retrieve(query, top_k=self._initial_k)

        if not initial_result.chunks:
            return initial_result

        documents = [c.text for c in initial_result.chunks]
        ranked = self._reranker.rerank(query, documents, top_k=top_k)

        reranked_chunks: List[RetrievedChunk] = []
        for ranked_doc in ranked:
            original_chunk = initial_result.chunks[ranked_doc.original_index]
            reranked_chunks.append(
                RetrievedChunk(
                    id=original_chunk.id,
                    text=original_chunk.text,
                    metadata=original_chunk.metadata,
                    distance=original_chunk.distance,
                    score=ranked_doc.score,
                )
            )

        return RetrievalResult(
            query=query,
            chunks=reranked_chunks,
            total_count=len(reranked_chunks),
        )
