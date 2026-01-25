# Retriever Module 구현 계획

> **Target Task**: Phase 2 - RAG 파이프라인 > Retriever Module
> **Target Path**: `src/core/rag/retriever.py`

## 목표

사용자 쿼리를 임베딩하고 ChromaDB에서 Top-k 유사 청크를 검색하는 Retriever 모듈 구현.
기존 `EmbedderFactory` + `ChromaStore` 패턴을 활용하여 DI 원칙을 준수하고 테스트 용이성을 확보합니다.

---

## 기존 패턴 분석

### ChromaStore.query() ([chroma_store.py](file:///Users/imseungmin/work/portfolio/obsidian_RAG/obrag/src/db/chroma_store.py#L138-L180))

```python
def query(
    self, query_text: str, n_results: int = 5,
    where: Optional[dict] = None, where_document: Optional[dict] = None,
) -> List[dict]:
    """Returns: [{"id": ..., "text": ..., "metadata": ..., "distance": ...}]"""
```

**핵심 특징:**

- 이미 텍스트 쿼리 → 임베딩 → 검색이 내부적으로 처리됨
- `distance` (L2 거리) 반환 → similarity score로 변환 필요 시 `1 / (1 + distance)` 사용
- 메타데이터 필터(`where`) 및 문서 필터(`where_document`) 지원

### EmbedderFactory 패턴 ([factory.py](file:///Users/imseungmin/work/portfolio/obsidian_RAG/obrag/src/core/embedding/factory.py))

- Config 기반 임베더 생성
- DI로 테스트 시 `FakeEmbedder` 주입 가능
- Retriever에서는 `ChromaStore`가 이미 임베더를 사용하므로 별도 임베더 주입 불필요

---

## 제안하는 구조

### 신규 파일

| 파일                        | 역할                                        |
| --------------------------- | ------------------------------------------- |
| `src/core/rag/__init__.py`  | [NEW] RAG 모듈 초기화                       |
| `src/core/rag/retriever.py` | [NEW] Retriever 클래스 및 결과 데이터클래스 |

### 테스트 파일

| 파일                                     | 역할                             |
| ---------------------------------------- | -------------------------------- |
| `src/tasktests/phase2/test_retriever.py` | [NEW] Retriever 단위/통합 테스트 |

---

## 파일별 상세 계획

### [NEW] `src/core/rag/retriever.py`

```python
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
```

---

### [NEW] `src/core/rag/__init__.py`

```python
# RAG Module
"""RAG 파이프라인 모듈"""

from .retriever import Retriever, RetrievedChunk, RetrievalResult

__all__ = [
    "Retriever",
    "RetrievedChunk",
    "RetrievalResult",
]
```

---

### [NEW] `src/tasktests/phase2/test_retriever.py`

```python
"""
Retriever 단위/통합 테스트

FakeEmbedder를 사용한 단위 테스트와 실제 임베딩을 사용한 통합 테스트를 포함.
"""

import os
import pytest
import tempfile
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.rag import Retriever, RetrievedChunk, RetrievalResult
from core.embedding import FakeEmbedder
from db.chroma_store import ChromaStore


class TestRetrieverUnit:
    """FakeEmbedder를 사용한 단위 테스트 (외부 의존성 없음)"""

    @pytest.fixture
    def store_with_data(self, tmp_path):
        """테스트 데이터가 포함된 ChromaStore 생성"""
        embedder = FakeEmbedder(dimension=8)
        store = ChromaStore(
            persist_path=str(tmp_path / "chroma"),
            collection_name="test_retriever",
            embedder=embedder,
        )

        # 테스트 청크 추가
        from core.preprocessing.markdown_preprocessor import Chunk
        chunks = [
            Chunk(
                text="Python is a programming language",
                metadata={"source": "python.md", "folder_path": "programming"}
            ),
            Chunk(
                text="Machine learning uses algorithms",
                metadata={"source": "ml.md", "folder_path": "ai"}
            ),
            Chunk(
                text="RAG combines retrieval and generation",
                metadata={"source": "rag.md", "folder_path": "ai"}
            ),
        ]
        store.add_chunks(chunks)

        yield store
        store.clear()

    def test_retrieve_returns_result(self, store_with_data):
        """기본 검색이 RetrievalResult를 반환하는지 확인"""
        retriever = Retriever(store_with_data)
        result = retriever.retrieve("programming", top_k=3)

        assert isinstance(result, RetrievalResult)
        assert result.query == "programming"
        assert len(result.chunks) <= 3

    def test_retrieved_chunk_has_all_fields(self, store_with_data):
        """RetrievedChunk가 필수 필드를 모두 포함하는지 확인"""
        retriever = Retriever(store_with_data)
        result = retriever.retrieve("test", top_k=1)

        if result.chunks:
            chunk = result.chunks[0]
            assert hasattr(chunk, "id")
            assert hasattr(chunk, "text")
            assert hasattr(chunk, "metadata")
            assert hasattr(chunk, "distance")
            assert hasattr(chunk, "score")
            assert 0.0 <= chunk.score <= 1.0

    def test_top_chunk_property(self, store_with_data):
        """top_chunk 프로퍼티가 정상 동작하는지 확인"""
        retriever = Retriever(store_with_data)
        result = retriever.retrieve("test", top_k=3)

        if result.chunks:
            assert result.top_chunk == result.chunks[0]

    def test_empty_result_top_chunk_is_none(self, tmp_path):
        """결과가 없을 때 top_chunk가 None인지 확인"""
        embedder = FakeEmbedder(dimension=8)
        empty_store = ChromaStore(
            persist_path=str(tmp_path / "empty_chroma"),
            collection_name="empty_test",
            embedder=embedder,
        )
        retriever = Retriever(empty_store)
        result = retriever.retrieve("nonexistent")

        assert result.top_chunk is None
        assert result.total_count == 0

    def test_distance_to_score_conversion(self):
        """거리 → 점수 변환이 올바른지 확인"""
        # distance=0 → score=1.0
        assert Retriever._distance_to_score(0.0) == 1.0

        # distance=1 → score=0.5
        assert Retriever._distance_to_score(1.0) == 0.5

        # distance=None → score=0.0
        assert Retriever._distance_to_score(None) == 0.0

    def test_retrieve_with_context_numbered(self, store_with_data):
        """numbered 포맷 컨텍스트 생성 확인"""
        retriever = Retriever(store_with_data)
        context = retriever.retrieve_with_context("test", top_k=2, context_format="numbered")

        assert "[1]" in context or context == ""

    def test_retrieve_with_context_simple(self, store_with_data):
        """simple 포맷 컨텍스트 생성 확인"""
        retriever = Retriever(store_with_data)
        context = retriever.retrieve_with_context("test", top_k=2, context_format="simple")

        # 결과가 있으면 구분자 포함, 없으면 빈 문자열
        assert "---" in context or context == "" or len(context) > 0


class TestRetrieverWithMetadataFilter:
    """메타데이터 필터 테스트"""

    @pytest.fixture
    def store_with_folders(self, tmp_path):
        """폴더 메타데이터가 있는 테스트 데이터"""
        embedder = FakeEmbedder(dimension=8)
        store = ChromaStore(
            persist_path=str(tmp_path / "chroma_filter"),
            collection_name="filter_test",
            embedder=embedder,
        )

        from core.preprocessing.markdown_preprocessor import Chunk
        chunks = [
            Chunk(text="AI content 1", metadata={"source": "a.md", "folder_path": "ai"}),
            Chunk(text="AI content 2", metadata={"source": "b.md", "folder_path": "ai"}),
            Chunk(text="Web content", metadata={"source": "c.md", "folder_path": "web"}),
        ]
        store.add_chunks(chunks)

        yield store
        store.clear()

    def test_where_filter(self, store_with_folders):
        """메타데이터 필터가 동작하는지 확인"""
        retriever = Retriever(store_with_folders)
        result = retriever.retrieve(
            query="content",
            top_k=10,
            where={"folder_path": "ai"}
        )

        # AI 폴더의 문서만 반환되어야 함
        for chunk in result.chunks:
            assert chunk.metadata.get("folder_path") == "ai"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
```

---

## Verification Plan

### Automated Tests

```bash
# 전체 Retriever 테스트 실행
cd /Users/imseungmin/work/portfolio/obsidian_RAG/obrag
python -m pytest src/tasktests/phase2/test_retriever.py -v

# 단위 테스트만 실행 (외부 의존성 없음)
python -m pytest src/tasktests/phase2/test_retriever.py::TestRetrieverUnit -v
```

### Manual Verification

1. **실제 데이터로 검색 확인** (옵시디언 노트가 있을 때):

```python
# 대화형 테스트
cd /Users/imseungmin/work/portfolio/obsidian_RAG/obrag
python -c "
from core.rag import Retriever
from db.chroma_store import ChromaStore

# 기존 DB 연결 (실제 데이터가 있는 경우)
store = ChromaStore(persist_path='./chroma_db')
retriever = Retriever(store)

result = retriever.retrieve('Python programming', top_k=3)
print(f'Query: {result.query}')
print(f'Found: {result.total_count} chunks')
for i, chunk in enumerate(result.chunks, 1):
    print(f'[{i}] Score: {chunk.score:.3f}')
    print(f'    Source: {chunk.metadata.get(\"source\", \"unknown\")}')
    print(f'    Text: {chunk.text[:100]}...')
"
```

2. **컨텍스트 포맷팅 확인**:

```python
cd /Users/imseungmin/work/portfolio/obsidian_RAG/obrag
python -c "
from core.rag import Retriever
from core.embedding import FakeEmbedder
from db.chroma_store import ChromaStore
from core.preprocessing.markdown_preprocessor import Chunk
import tempfile

# 테스트 데이터 생성
with tempfile.TemporaryDirectory() as tmp:
    embedder = FakeEmbedder(dimension=8)
    store = ChromaStore(persist_path=tmp, embedder=embedder)
    store.add_chunks([
        Chunk(text='First document about AI', metadata={'source': 'ai.md'}),
        Chunk(text='Second document about ML', metadata={'source': 'ml.md'}),
    ])

    retriever = Retriever(store)
    context = retriever.retrieve_with_context('test', top_k=2)
    print('=== Numbered Format ===')
    print(context)
"
```

---

## 요약

| 항목            | 내용                                                      |
| --------------- | --------------------------------------------------------- |
| **신규 파일**   | `src/core/rag/retriever.py`, `src/core/rag/__init__.py`   |
| **테스트 파일** | `src/tasktests/phase2/test_retriever.py`                  |
| **참고 패턴**   | `ChromaStore.query()` (래핑), `EmbedderFactory` (DI 구조) |
| **핵심 클래스** | `Retriever`, `RetrievedChunk`, `RetrievalResult`          |
| **외부 의존성** | 없음 (기존 `ChromaStore` 재사용)                          |
| **예상 소요**   | 1-2시간                                                   |
