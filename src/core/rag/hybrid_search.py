"""
Hybrid Search Module

Dense (Vector) + Sparse (BM25) 하이브리드 검색 구현.
"""

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Protocol

if TYPE_CHECKING:
    from db.chroma_store import ChromaStore


class _BM25Like(Protocol):
    def get_scores(self, query: list[str]) -> list[float]: ...


class _BM25OkapiCtor(Protocol):
    def __call__(self, corpus: list[list[str]]) -> _BM25Like: ...


@dataclass
class HybridSearchResult:
    id: str
    text: str
    metadata: Dict[str, Any]
    score: float
    dense_score: float
    sparse_score: float


class HybridSearcher:
    """
    Dense (Vector) + Sparse (BM25) 하이브리드 검색.

    사용법:
        searcher = HybridSearcher(vector_store)
        searcher.index_documents(documents, ids)
        results = searcher.search("검색어", top_k=10)
    """

    def __init__(
        self,
        vector_store: "ChromaStore",
        dense_weight: float = 0.7,
        sparse_weight: float = 0.3,
    ):
        if not (0 <= dense_weight <= 1 and 0 <= sparse_weight <= 1):
            raise ValueError("Weights must be between 0 and 1")
        if abs(dense_weight + sparse_weight - 1.0) > 0.01:
            raise ValueError("Weights should sum to 1.0")

        self._vector_store = vector_store
        self._dense_weight = dense_weight
        self._sparse_weight = sparse_weight
        self._bm25: Optional[_BM25Like] = None
        self._documents: List[str] = []
        self._doc_ids: List[str] = []

    def _load_bm25(self) -> _BM25OkapiCtor:
        try:
            from rank_bm25 import BM25Okapi

            return BM25Okapi
        except ImportError as exc:
            raise ImportError(
                "rank-bm25 패키지가 필요합니다. 설치: pip install rank-bm25"
            ) from exc

    def _tokenize(self, text: str) -> list[str]:
        return text.lower().split()

    def index_documents(self, documents: List[str], ids: List[str]) -> None:
        if len(documents) != len(ids):
            raise ValueError("documents와 ids 길이가 일치해야 합니다")

        self._documents = documents
        self._doc_ids = ids

        BM25Okapi = self._load_bm25()
        tokenized = [self._tokenize(doc) for doc in documents]
        self._bm25 = BM25Okapi(tokenized)

    def search(self, query: str, top_k: int = 10) -> List[HybridSearchResult]:
        if self._bm25 is None:
            raise RuntimeError("index_documents()를 먼저 호출하세요")

        dense_results = self._vector_store.query(query, n_results=top_k * 2)
        dense_scores = {
            r["id"]: 1 / (1 + r["distance"]) if r["distance"] else 0.0
            for r in dense_results
        }
        dense_texts = {r["id"]: r["text"] for r in dense_results}
        dense_metadata = {r["id"]: r["metadata"] for r in dense_results}

        tokenized_query = self._tokenize(query)
        bm25_scores_raw = self._bm25.get_scores(tokenized_query)

        max_bm25 = max(bm25_scores_raw) if max(bm25_scores_raw) > 0 else 1.0
        sparse_scores = {
            self._doc_ids[i]: score / max_bm25
            for i, score in enumerate(bm25_scores_raw)
        }

        all_ids = set(dense_scores.keys()) | set(sparse_scores.keys())
        combined: List[HybridSearchResult] = []

        for doc_id in all_ids:
            d_score = dense_scores.get(doc_id, 0.0)
            s_score = sparse_scores.get(doc_id, 0.0)
            final_score = self._dense_weight * d_score + self._sparse_weight * s_score

            text = dense_texts.get(doc_id, "")
            metadata = dense_metadata.get(doc_id, {})

            if not text and doc_id in self._doc_ids:
                idx = self._doc_ids.index(doc_id)
                text = self._documents[idx]

            combined.append(
                HybridSearchResult(
                    id=doc_id,
                    text=text,
                    metadata=metadata,
                    score=final_score,
                    dense_score=d_score,
                    sparse_score=s_score,
                )
            )

        combined.sort(key=lambda x: x.score, reverse=True)
        return combined[:top_k]

    @property
    def is_indexed(self) -> bool:
        return self._bm25 is not None

    @property
    def document_count(self) -> int:
        return len(self._documents)
