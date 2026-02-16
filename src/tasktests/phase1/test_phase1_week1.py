"""
Phase 1 Week 1 Components Tests

MultilingualE5Embedder, HybridSearcher, Reranker 테스트.
"""

import pytest
from unittest.mock import MagicMock, patch


class TestMultilingualE5Embedder:
    """MultilingualE5Embedder 테스트"""

    def test_embed_query_adds_query_prefix(self):
        """embed_query가 query: prefix를 추가하는지 확인"""
        from core.embedding import MultilingualE5Embedder

        embedder = MultilingualE5Embedder()

        mock_model = MagicMock()
        mock_model.encode.return_value = MagicMock(tolist=lambda: [[0.1] * 1024])
        embedder._model = mock_model
        embedder._dimension = 1024

        embedder.embed_query("test query")

        mock_model.encode.assert_called_once()
        call_args = mock_model.encode.call_args[0][0]
        assert call_args == ["query: test query"]

    def test_embed_documents_adds_passage_prefix(self):
        """embed_documents가 passage: prefix를 추가하는지 확인"""
        from core.embedding import MultilingualE5Embedder

        embedder = MultilingualE5Embedder()

        mock_model = MagicMock()
        mock_model.encode.return_value = MagicMock(
            tolist=lambda: [[0.1] * 1024, [0.2] * 1024]
        )
        embedder._model = mock_model
        embedder._dimension = 1024

        embedder.embed_documents(["doc1", "doc2"])

        mock_model.encode.assert_called_once()
        call_args = mock_model.encode.call_args[0][0]
        assert call_args == ["passage: doc1", "passage: doc2"]

    def test_dimension_property(self):
        """dimension 속성이 올바르게 반환되는지 확인"""
        from core.embedding import MultilingualE5Embedder

        embedder = MultilingualE5Embedder()
        assert embedder.dimension == 1024

        embedder2 = MultilingualE5Embedder(model_name="intfloat/multilingual-e5-base")
        assert embedder2.dimension == 768

    def test_model_name_property(self):
        """model_name 속성이 올바르게 반환되는지 확인"""
        from core.embedding import MultilingualE5Embedder

        embedder = MultilingualE5Embedder()
        assert embedder.model_name == "intfloat/multilingual-e5-large-instruct"

        custom_embedder = MultilingualE5Embedder(model_name="custom-model")
        assert custom_embedder.model_name == "custom-model"


class TestHybridSearcher:
    """HybridSearcher 테스트"""

    def test_init_validates_weights(self):
        """weights 검증이 올바르게 동작하는지 확인"""
        from core.rag.hybrid_search import HybridSearcher

        mock_store = MagicMock()

        with pytest.raises(ValueError):
            HybridSearcher(mock_store, dense_weight=0.5, sparse_weight=0.3)

        with pytest.raises(ValueError):
            HybridSearcher(mock_store, dense_weight=1.5, sparse_weight=0.5)

    def test_index_documents_creates_bm25_index(self):
        """index_documents가 BM25 인덱스를 생성하는지 확인"""
        from core.rag.hybrid_search import HybridSearcher

        mock_store = MagicMock()
        searcher = HybridSearcher(mock_store)

        assert not searcher.is_indexed

        with patch("core.rag.hybrid_search.HybridSearcher._load_bm25") as mock_load:
            mock_bm25_class = MagicMock()
            mock_load.return_value = mock_bm25_class

            searcher.index_documents(["doc1", "doc2"], ["id1", "id2"])

            assert searcher.is_indexed
            assert searcher.document_count == 2

    def test_search_requires_indexing(self):
        """search가 인덱싱 없이 호출되면 에러 발생"""
        from core.rag.hybrid_search import HybridSearcher

        mock_store = MagicMock()
        searcher = HybridSearcher(mock_store)

        with pytest.raises(RuntimeError, match="index_documents"):
            searcher.search("query")


class TestReranker:
    """Reranker 테스트"""

    def test_rerank_empty_documents(self):
        """빈 문서 리스트에 대해 빈 결과 반환"""
        from core.rag.reranker import Reranker

        reranker = Reranker()
        result = reranker.rerank("query", [])

        assert result == []

    def test_rerank_sorts_by_score(self):
        """rerank가 점수로 정렬하는지 확인"""
        from core.rag.reranker import Reranker

        reranker = Reranker()

        mock_model = MagicMock()
        mock_model.predict.return_value = [0.3, 0.9, 0.1]
        reranker._model = mock_model

        result = reranker.rerank("query", ["low", "high", "lowest"], top_k=3)

        assert len(result) == 3
        assert result[0].text == "high"
        assert result[0].score == 0.9
        assert result[1].text == "low"
        assert result[2].text == "lowest"

    def test_rerank_respects_top_k(self):
        """rerank가 top_k를 준수하는지 확인"""
        from core.rag.reranker import Reranker

        reranker = Reranker()

        mock_model = MagicMock()
        mock_model.predict.return_value = [0.5, 0.8, 0.3, 0.9, 0.1]
        reranker._model = mock_model

        result = reranker.rerank("query", ["a", "b", "c", "d", "e"], top_k=2)

        assert len(result) == 2
        assert result[0].score == 0.9
        assert result[1].score == 0.8


class TestEmbeddingStrategyProtocol:
    """EmbeddingStrategy 프로토콜 준수 테스트"""

    def test_fake_embedder_has_embed_query(self):
        """FakeEmbedder가 embed_query를 구현하는지 확인"""
        from core.embedding import FakeEmbedder

        embedder = FakeEmbedder()
        result = embedder.embed_query("test")

        assert isinstance(result, list)
        assert len(result) == 8

    def test_fake_embedder_has_embed_documents(self):
        """FakeEmbedder가 embed_documents를 구현하는지 확인"""
        from core.embedding import FakeEmbedder

        embedder = FakeEmbedder()
        result = embedder.embed_documents(["doc1", "doc2"])

        assert isinstance(result, list)
        assert len(result) == 2


class TestEmbedderFactory:
    """EmbedderFactory 테스트"""

    def test_create_multilingual_e5(self):
        """multilingual_e5 provider로 MultilingualE5Embedder 생성"""
        from core.embedding import EmbedderFactory, MultilingualE5Embedder
        from config.models import MultilingualE5EmbeddingConfig

        config = MultilingualE5EmbeddingConfig()
        embedder = EmbedderFactory.create(config)

        assert isinstance(embedder, MultilingualE5Embedder)
        assert embedder.model_name == "intfloat/multilingual-e5-large-instruct"

    def test_create_multilingual_e5_custom_model(self):
        """커스텀 모델로 MultilingualE5Embedder 생성"""
        from core.embedding import EmbedderFactory, MultilingualE5Embedder
        from config.models import MultilingualE5EmbeddingConfig

        config = MultilingualE5EmbeddingConfig(
            model_name="intfloat/multilingual-e5-base"
        )
        embedder = EmbedderFactory.create(config)

        assert isinstance(embedder, MultilingualE5Embedder)
        assert embedder.model_name == "intfloat/multilingual-e5-base"
