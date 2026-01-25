"""
Retriever Module

쿼리 임베딩 → ChromaDB Top-k 검색 → 결과 포맷팅을 담당하는 모듈.
"""

from dataclasses import dataclass
from typing import List, Optional, Dict, Any

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from db.chroma_store import ChromaStore


# ============================================================================
# Data Classes
# ============================================================================

@dataclass
class RetrievedChunk:
    """검색된 청크 정보를 담는 데이터클래스."""

    id: str                  # 청크 고유 ID
    text: str                # 청크 본문
    metadata: Dict[str, Any] # 메타데이터 (source, folder_path, headers 등)
    distance: float          # L2 거리 (낮을수록 유사)
    score: float             # 유사도 점수 (0~1, 높을수록 유사)


@dataclass
class RetrievalResult:
    """검색 결과 전체를 담는 데이터클래스."""

    query: str                      # 원본 쿼리
    chunks: List[RetrievedChunk]    # 검색된 청크 목록
    total_count: int                # 검색된 청크 수

    @property
    def top_chunk(self) -> Optional[RetrievedChunk]:
        """가장 관련성 높은 청크 반환."""
        return self.chunks[0] if self.chunks else None


# ============================================================================
# Retriever Class
# ============================================================================

class Retriever:
    """
    ChromaDB 기반 문서 검색기.

    사용법:
        # 기본 사용
        store = ChromaStore()
        retriever = Retriever(store)
        result = retriever.retrieve("What is RAG?", top_k=5)

        for chunk in result.chunks:
            print(f"[{chunk.score:.3f}] {chunk.text[:100]}...")

        # 메타데이터 필터링
        result = retriever.retrieve(
            query="Python tutorial",
            top_k=3,
            where={"folder_path": {"$contains": "programming"}}
        )
    """

    def __init__(self, store: ChromaStore):
        """
        Args:
            store: ChromaDB 벡터 스토어 인스턴스
        """
        self._store = store

    def retrieve(
        self,
        query: str,
        top_k: int = 5,
        where: Optional[Dict[str, Any]] = None,
        where_document: Optional[Dict[str, Any]] = None,
    ) -> RetrievalResult:
        """
        쿼리와 유사한 청크를 검색합니다.

        Args:
            query: 검색 쿼리 문자열
            top_k: 반환할 최대 결과 수
            where: 메타데이터 필터 (예: {"source": "note.md"})
            where_document: 문서 내용 필터 (예: {"$contains": "keyword"})

        Returns:
            RetrievalResult 객체 (검색된 청크 목록 포함)
        """
        # ChromaStore.query() 호출
        raw_results = self._store.query(
            query_text=query,
            n_results=top_k,
            where=where,
            where_document=where_document,
        )

        # 결과 변환
        chunks = [
            RetrievedChunk(
                id=r["id"],
                text=r["text"] or "",
                metadata=r["metadata"] or {},
                distance=r["distance"] or 0.0,
                score=self._distance_to_score(r["distance"]),
            )
            for r in raw_results
        ]

        return RetrievalResult(
            query=query,
            chunks=chunks,
            total_count=len(chunks),
        )

    @staticmethod
    def _distance_to_score(distance: Optional[float]) -> float:
        """
        L2 거리를 0~1 유사도 점수로 변환.

        공식: score = 1 / (1 + distance)
        - distance=0 → score=1.0 (완전 일치)
        - distance=∞ → score→0 (전혀 유사하지 않음)
        """
        if distance is None:
            return 0.0
        return 1.0 / (1.0 + distance)

    def retrieve_with_context(
        self,
        query: str,
        top_k: int = 5,
        context_format: str = "numbered",
    ) -> str:
        """
        검색 결과를 프롬프트에 주입할 수 있는 컨텍스트 문자열로 반환.

        Args:
            query: 검색 쿼리
            top_k: 반환할 최대 결과 수
            context_format: "numbered" | "simple"

        Returns:
            포맷팅된 컨텍스트 문자열
        """
        result = self.retrieve(query, top_k=top_k)

        if not result.chunks:
            return ""

        if context_format == "numbered":
            lines = []
            for i, chunk in enumerate(result.chunks, 1):
                source = chunk.metadata.get("source", "unknown")
                lines.append(f"[{i}] Source: {source}")
                lines.append(chunk.text)
                lines.append("")
            return "\n".join(lines).strip()

        else:  # simple
            return "\n\n---\n\n".join(c.text for c in result.chunks)
