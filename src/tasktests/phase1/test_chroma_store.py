"""
Phase 1: ChromaStore 테스트

이 테스트는 ChromaDB 벡터 저장소가 올바르게 동작하는지 검증합니다.
테스트 대상: src/db/chroma_store.py

주요 변경: FakeEmbedder를 사용하여 API 호출 없이 빠르게 테스트.
"""

import sys
from pathlib import Path

# 프로젝트 루트를 path에 추가
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

import pytest
import shutil

from core.preprocessing import Chunk
from core.embedding import FakeEmbedder, OpenAIEmbedder
from db import ChromaStore, create_store, store_chunks, search_chunks
from db.chroma_store import sanitize_collection_name, derive_collection_name


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def temp_db_path(tmp_path):
    """임시 ChromaDB 저장 경로"""
    db_path = tmp_path / "test_chroma_db"
    yield str(db_path)
    # 테스트 후 정리
    if db_path.exists():
        shutil.rmtree(db_path)


@pytest.fixture
def fake_embedder():
    """테스트용 FakeEmbedder"""
    return FakeEmbedder(dimension=8)


@pytest.fixture
def sample_chunks():
    """테스트용 샘플 청크"""
    return [
        Chunk(
            text="Python은 인터프리터 언어로 동적 타이핑을 지원합니다.",
            metadata={"source": "python_intro.md", "folder_path": "programming"},
        ),
        Chunk(
            text="FastAPI는 빠른 API 개발을 위한 Python 웹 프레임워크입니다.",
            metadata={"source": "fastapi.md", "folder_path": "programming/web"},
        ),
        Chunk(
            text="ChromaDB는 임베딩을 저장하고 검색하는 벡터 데이터베이스입니다.",
            metadata={"source": "chromadb.md", "folder_path": "database"},
        ),
    ]


@pytest.fixture
def store(temp_db_path, fake_embedder):
    """테스트용 ChromaStore 인스턴스 (FakeEmbedder 사용)"""
    return ChromaStore(
        persist_path=temp_db_path,
        collection_name="test_collection",
        embedder=fake_embedder,
    )


# ============================================================================
# Test: ChromaStore Basic
# ============================================================================


class TestChromaStoreBasic:
    """ChromaStore 기본 기능 테스트"""

    def test_store_initialization_with_fake_embedder(self, temp_db_path, fake_embedder):
        """FakeEmbedder로 저장소 초기화 성공"""
        store = ChromaStore(
            persist_path=temp_db_path,
            collection_name="test_init",
            embedder=fake_embedder,
        )
        assert store is not None
        assert store.collection_name == "test_init"
        assert store.embedder is fake_embedder

    def test_store_default_uses_openai(self, temp_db_path):
        """기본 임베더는 OpenAIEmbedder"""
        store = ChromaStore(
            persist_path=temp_db_path,
            collection_name="test_default",
        )
        assert isinstance(store.embedder, OpenAIEmbedder)

    def test_openai_embedder_requires_api_key(self, monkeypatch):
        """OpenAIEmbedder는 API 키 필요"""
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)

        with pytest.raises(ValueError, match="API key required"):
            OpenAIEmbedder()

    def test_get_stats_empty_collection(self, store):
        """빈 컬렉션 통계"""
        stats = store.get_stats()

        assert "name" in stats
        assert "count" in stats
        assert "embedder" in stats
        assert stats["count"] == 0


# ============================================================================
# Test: ChromaStore Operations
# ============================================================================


class TestChromaStoreOperations:
    """CRUD 연산 테스트"""

    def test_add_single_chunk(self, store, sample_chunks):
        """단일 청크 저장"""
        chunk = sample_chunks[0]
        count = store.add_chunks([chunk])

        assert count == 1
        assert store.get_stats()["count"] == 1

    def test_add_multiple_chunks(self, store, sample_chunks):
        """다중 청크 저장"""
        count = store.add_chunks(sample_chunks)

        assert count == 3
        assert store.get_stats()["count"] == 3

    def test_add_empty_list(self, store):
        """빈 리스트 저장"""
        count = store.add_chunks([])

        assert count == 0
        assert store.get_stats()["count"] == 0

    def test_clear_collection(self, store, sample_chunks):
        """컬렉션 초기화"""
        store.add_chunks(sample_chunks)
        assert store.get_stats()["count"] == 3

        store.clear()
        assert store.get_stats()["count"] == 0


# ============================================================================
# Test: ChromaStore Query
# ============================================================================


class TestChromaStoreQuery:
    """쿼리 및 유사도 검색 테스트"""

    def test_query_returns_results(self, store, sample_chunks):
        """쿼리 결과 반환"""
        store.add_chunks(sample_chunks)

        results = store.query("Python 프로그래밍", n_results=2)

        assert len(results) == 2
        assert "text" in results[0]
        assert "metadata" in results[0]
        assert "distance" in results[0]

    def test_query_with_n_results(self, store, sample_chunks):
        """n_results 파라미터"""
        store.add_chunks(sample_chunks)

        results = store.query("데이터베이스", n_results=1)
        assert len(results) == 1

        results = store.query("데이터베이스", n_results=3)
        assert len(results) == 3

    def test_query_empty_collection(self, store):
        """빈 컬렉션 쿼리"""
        results = store.query("검색어", n_results=5)
        assert results == []


# ============================================================================
# Test: Convenience Functions
# ============================================================================


class TestConvenienceFunctions:
    """편의 함수 테스트"""

    def test_create_store_with_embedder(self, temp_db_path, fake_embedder):
        """create_store 함수 (embedder 지정)"""
        store = create_store(
            persist_path=temp_db_path,
            collection_name="convenience_test",
            embedder=fake_embedder,
        )
        assert isinstance(store, ChromaStore)
        assert store.embedder is fake_embedder

    def test_store_chunks_function(self, temp_db_path, sample_chunks, fake_embedder):
        """store_chunks 함수"""
        count = store_chunks(
            sample_chunks,
            persist_path=temp_db_path,
            collection_name="store_test",
            embedder=fake_embedder,
        )
        assert count == 3

    def test_search_chunks_function(self, temp_db_path, sample_chunks, fake_embedder):
        """search_chunks 함수"""
        # 먼저 저장
        store_chunks(
            sample_chunks,
            persist_path=temp_db_path,
            collection_name="search_test",
            embedder=fake_embedder,
        )

        # 검색
        results = search_chunks(
            "Python",
            n_results=2,
            persist_path=temp_db_path,
            collection_name="search_test",
            embedder=fake_embedder,
        )
        assert len(results) == 2


# ============================================================================
# Test: EmbeddingStrategy Pattern
# ============================================================================


class TestEmbeddingStrategyPattern:
    """EmbeddingStrategy 패턴 테스트"""

    def test_fake_embedder_produces_vectors(self, fake_embedder):
        """FakeEmbedder가 벡터 생성"""
        vectors = fake_embedder.embed(["hello", "world"])

        assert len(vectors) == 2
        assert len(vectors[0]) == fake_embedder.dimension
        assert all(isinstance(v, float) for v in vectors[0])

    def test_fake_embedder_deterministic(self, fake_embedder):
        """FakeEmbedder는 결정론적"""
        v1 = fake_embedder.embed(["test"])
        v2 = fake_embedder.embed(["test"])

        assert v1 == v2

    def test_store_accepts_custom_embedder(self, temp_db_path):
        """ChromaStore가 커스텀 임베더 수용"""
        custom_embedder = FakeEmbedder(dimension=16)
        store = ChromaStore(
            persist_path=temp_db_path,
            collection_name="custom_embed",
            embedder=custom_embedder,
        )

        assert store.embedder.dimension == 16


# ============================================================================
# Test: Integration with FolderScanner
# ============================================================================


class TestIntegrationWithFolderScanner:
    """FolderScanner → ChromaStore 통합 테스트"""

    @pytest.fixture
    def testdoc_path(self):
        """testdoc 폴더 경로"""
        return project_root / "testdoc" / "note"

    def test_scan_and_store_integration(
        self, temp_db_path, fake_embedder, testdoc_path
    ):
        """스캔 → 저장 통합 테스트 (FakeEmbedder)"""
        from core.sync import scan_and_process_folder

        if not testdoc_path.exists():
            pytest.skip("testdoc/note 폴더가 없습니다")

        chunks = scan_and_process_folder(testdoc_path, min_size=50, max_size=500)

        if not chunks:
            pytest.skip("청크가 생성되지 않았습니다")

        store = ChromaStore(
            persist_path=temp_db_path,
            collection_name="integration_test",
            embedder=fake_embedder,
        )

        count = store.add_chunks(chunks)
        assert count > 0
        assert store.get_stats()["count"] == count

    def test_scan_store_query_flow(self, temp_db_path, fake_embedder, testdoc_path):
        """전체 파이프라인: 스캔 → 저장 → 쿼리"""
        from core.sync import scan_and_process_folder

        if not testdoc_path.exists():
            pytest.skip("testdoc/note 폴더가 없습니다")

        chunks = scan_and_process_folder(testdoc_path, min_size=50, max_size=500)
        if not chunks:
            pytest.skip("청크가 없습니다")

        store = ChromaStore(
            persist_path=temp_db_path,
            collection_name="flow_test",
            embedder=fake_embedder,
        )

        store.add_chunks(chunks)
        results = store.query("test", n_results=3)

        assert isinstance(results, list)
        if results:
            assert "text" in results[0]
            assert "metadata" in results[0]


# ============================================================================
# Test: Collection Name Utilities
# ============================================================================


class TestCollectionNameUtilities:
    def test_sanitize_converts_to_lowercase(self):
        assert sanitize_collection_name("MyCollection") == "mycollection"

    def test_sanitize_replaces_slash_with_underscore(self):
        assert sanitize_collection_name("BAAI/bge-m3") == "baai_bge-m3"

    def test_sanitize_removes_invalid_chars(self):
        assert sanitize_collection_name("test@#$%name") == "test_name"

    def test_sanitize_removes_consecutive_underscores(self):
        assert sanitize_collection_name("test___name") == "test_name"

    def test_sanitize_removes_consecutive_dots(self):
        assert sanitize_collection_name("test..name") == "test.name"

    def test_sanitize_strips_leading_trailing_special_chars(self):
        assert sanitize_collection_name("___test_name___") == "test_name"

    def test_sanitize_handles_short_names(self):
        result = sanitize_collection_name("ab")
        assert len(result) >= 3

    def test_sanitize_handles_long_names(self):
        long_name = "a" * 100
        result = sanitize_collection_name(long_name)
        assert len(result) <= 63

    def test_sanitize_handles_ipv4_pattern(self):
        result = sanitize_collection_name("192.168.1.1")
        assert not result.startswith("192")

    def test_derive_collection_name_combines_base_and_model(self):
        result = derive_collection_name("obsidian_notes", "text-embedding-3-small")
        assert result == "obsidian_notes_text-embedding-3-small"

    def test_derive_collection_name_sanitizes_model_name(self):
        result = derive_collection_name("obsidian_notes", "BAAI/bge-m3")
        assert result == "obsidian_notes_baai_bge-m3"

    def test_derive_collection_name_handles_complex_model_names(self):
        result = derive_collection_name("notes", "dragonkue/BGE-m3-ko")
        assert "/" not in result
        assert result == "notes_dragonkue_bge-m3-ko"


# ============================================================================
# Run Tests
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
