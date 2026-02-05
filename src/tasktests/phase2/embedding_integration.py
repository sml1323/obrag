"""
Phase 2: 임베딩 모델 통합 테스트

Task 1: LocalEmbedder skeleton 테스트
Task 2: EmbedderFactory 테스트
Task 3: OpenAI 임베딩 + ChromaStore 통합 테스트
"""

import os
import sys
import pytest
from pathlib import Path

# 프로젝트 루트를 path에 추가
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from core.embedding import (
    EmbeddingStrategy,
    FakeEmbedder,
    OpenAIEmbedder,
    LocalEmbedder,
    OllamaEmbedder,
    SentenceTransformerEmbedder,
    EmbedderFactory,
)
from config.models import (
    OpenAIEmbeddingConfig,
    LocalEmbeddingConfig,
    OllamaEmbeddingConfig,
    SentenceTransformerEmbeddingConfig,
)


# ============================================================================
# Task 1: LocalEmbedder Skeleton 테스트
# ============================================================================


class TestLocalEmbedder:
    """LocalEmbedder deprecated bridge 테스트"""

    def test_instance_creation(self):
        """인스턴스 생성 가능 (DeprecationWarning 발생)"""
        import warnings

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            embedder = LocalEmbedder()
            assert embedder.model_name == "bge-m3"
            # DeprecationWarning 발생 확인
            assert len(w) >= 1
            assert issubclass(w[0].category, DeprecationWarning)

    def test_custom_model_name(self):
        """커스텀 모델명 지정"""
        import warnings

        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            embedder = LocalEmbedder(model_name="bge-base-en")
            assert embedder.model_name == "bge-base-en"
            # dimension은 SentenceTransformerEmbedder에서 결정됨
            assert embedder.dimension > 0

    def test_repr_shows_deprecated(self):
        """repr에 deprecated 표시 확인"""
        import warnings

        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            embedder = LocalEmbedder()
            repr_str = repr(embedder)
            assert "LocalEmbedder" in repr_str
            assert "deprecated=True" in repr_str


# ============================================================================
# Task 2: EmbedderFactory 테스트
# ============================================================================


class TestEmbedderFactory:
    """EmbedderFactory 테스트"""

    def test_create_fake_embedder(self):
        """Fake 임베더 생성"""
        embedder = EmbedderFactory.create_fake(dimension=16)
        assert isinstance(embedder, FakeEmbedder)
        assert embedder.dimension == 16

        # 실제 임베딩 동작 확인
        vectors = embedder.embed(["hello", "world"])
        assert len(vectors) == 2
        assert len(vectors[0]) == 16

    def test_create_local_embedder_from_config(self):
        """Config으로 LocalEmbedder 생성"""
        config = LocalEmbeddingConfig(model_name="bge-m3")
        embedder = EmbedderFactory.create(config)

        assert isinstance(embedder, LocalEmbedder)
        assert embedder.model_name == "bge-m3"

    def test_create_openai_convenience_method(self):
        """OpenAI 편의 메서드 테스트 (API 키 없이)"""
        # API 키 없으면 ValueError 발생 예상
        # 환경변수에 키가 있으면 성공
        api_key = os.getenv("OPENAI_API_KEY")
        if api_key:
            embedder = EmbedderFactory.create_openai()
            assert isinstance(embedder, OpenAIEmbedder)
        else:
            with pytest.raises(ValueError):
                EmbedderFactory.create_openai()

    def test_create_from_openai_config(self):
        """OpenAIEmbeddingConfig으로 임베더 생성"""
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            pytest.skip("OPENAI_API_KEY not set")

        config = OpenAIEmbeddingConfig(model_name="text-embedding-3-small")
        embedder = EmbedderFactory.create(config)

        assert isinstance(embedder, OpenAIEmbedder)
        assert embedder.model_name == "text-embedding-3-small"

    def test_unknown_provider_raises_error(self):
        """알 수 없는 provider 에러"""
        with pytest.raises(ValueError):
            config = LocalEmbeddingConfig()
            config.provider = "unknown"  # type: ignore
            EmbedderFactory.create(config)

    def test_create_ollama_embedder_from_config(self):
        """OllamaEmbeddingConfig으로 임베더 생성"""
        config = OllamaEmbeddingConfig(model_name="nomic-embed-text")
        embedder = EmbedderFactory.create(config)

        assert isinstance(embedder, OllamaEmbedder)
        assert embedder.model_name == "nomic-embed-text"
        assert embedder.dimension == 768

    def test_create_sentence_transformer_embedder_from_config(self):
        """SentenceTransformerEmbeddingConfig으로 임베더 생성"""
        config = SentenceTransformerEmbeddingConfig(model_name="BAAI/bge-m3")
        embedder = EmbedderFactory.create(config)

        assert isinstance(embedder, SentenceTransformerEmbedder)
        assert embedder.model_name == "BAAI/bge-m3"


# ============================================================================
# Task 3: OpenAI + ChromaStore 통합 테스트
# ============================================================================


@pytest.mark.skipif(not os.getenv("OPENAI_API_KEY"), reason="OPENAI_API_KEY not set")
class TestOpenAIIntegration:
    """OpenAI 임베딩 실제 호출 및 ChromaStore 통합 테스트"""

    def test_openai_embed_single_text(self):
        """OpenAI 단일 텍스트 임베딩"""
        embedder = OpenAIEmbedder()
        vectors = embedder.embed(["Hello, world!"])

        assert len(vectors) == 1
        assert len(vectors[0]) == 1536  # text-embedding-3-small dimension
        assert all(isinstance(v, float) for v in vectors[0])

    def test_openai_embed_multiple_texts(self):
        """OpenAI 다중 텍스트 임베딩"""
        embedder = OpenAIEmbedder()
        texts = ["Python programming", "Machine learning", "Vector database"]
        vectors = embedder.embed(texts)

        assert len(vectors) == 3
        for vec in vectors:
            assert len(vec) == 1536

    def test_openai_empty_input(self):
        """빈 입력 처리"""
        embedder = OpenAIEmbedder()
        vectors = embedder.embed([])
        assert vectors == []

    def test_chromastore_with_openai(self, tmp_path):
        """ChromaStore + OpenAI 통합 테스트"""
        from db.chroma_store import ChromaStore

        # OpenAI 임베더로 ChromaStore 생성
        embedder = OpenAIEmbedder()
        store = ChromaStore(
            persist_path=str(tmp_path / "chroma_db"),
            collection_name="test_openai",
            embedder=embedder,
        )

        # 간단한 Chunk 객체 생성
        from dataclasses import dataclass

        @dataclass
        class MockChunk:
            text: str
            metadata: dict

        chunks = [
            MockChunk(
                text="Python is a programming language", metadata={"source": "test.md"}
            ),
            MockChunk(
                text="Machine learning uses algorithms", metadata={"source": "test.md"}
            ),
            MockChunk(
                text="Vector databases store embeddings", metadata={"source": "test.md"}
            ),
        ]

        # 청크 추가
        count = store.add_chunks(chunks)
        assert count == 3

        # 유사도 검색
        results = store.query("What is Python?", n_results=2)
        assert len(results) <= 2
        assert any("Python" in r["text"] for r in results)

        # 통계 확인
        stats = store.get_stats()
        assert stats["count"] == 3

    def test_chromastore_query_similarity(self, tmp_path):
        """ChromaStore 유사도 검색 품질 테스트"""
        from db.chroma_store import ChromaStore
        from dataclasses import dataclass

        @dataclass
        class MockChunk:
            text: str
            metadata: dict

        embedder = OpenAIEmbedder()
        store = ChromaStore(
            persist_path=str(tmp_path / "chroma_similarity"),
            collection_name="similarity_test",
            embedder=embedder,
        )

        # 다양한 주제의 청크
        chunks = [
            MockChunk(
                text="FastAPI는 Python 웹 프레임워크입니다",
                metadata={"topic": "web", "source": "test.md"},
            ),
            MockChunk(
                text="ChromaDB는 벡터 데이터베이스입니다",
                metadata={"topic": "db", "source": "test.md"},
            ),
            MockChunk(
                text="React는 JavaScript UI 라이브러리입니다",
                metadata={"topic": "frontend", "source": "test.md"},
            ),
            MockChunk(
                text="PostgreSQL은 관계형 데이터베이스입니다",
                metadata={"topic": "db", "source": "test.md"},
            ),
        ]

        store.add_chunks(chunks)

        # 데이터베이스 관련 쿼리 → DB 관련 청크가 상위에 나와야 함
        results = store.query("데이터베이스 종류", n_results=2)
        topics = [r["metadata"].get("topic") for r in results]
        assert "db" in topics, f"Expected 'db' topic in results, got: {topics}"


# ============================================================================
# 실행
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
