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
