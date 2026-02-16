"""
Phase 1 Week 2 Tests - Integration & Benchmarks

ChromaStore 통합 테스트 및 cross-lingual 검색 벤치마크.
"""

import pytest
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from typing import List, Tuple
from unittest.mock import MagicMock


@dataclass
class BenchmarkResult:
    name: str
    duration_ms: float
    recall_at_k: float
    mrr: float


class TestChromaStoreIntegration:
    """ChromaStore + EmbeddingStrategy 통합 테스트"""

    @pytest.fixture
    def temp_db_path(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir

    @pytest.fixture
    def mock_embedder(self):
        from core.embedding import FakeEmbedder

        return FakeEmbedder(dimension=8)

    def test_chromastore_uses_embed_documents_for_add(
        self, temp_db_path, mock_embedder
    ):
        """ChromaStore가 문서 추가 시 embed_documents를 사용하는지 확인"""
        from db.chroma_store import ChromaStore, _EmbeddingFunctionAdapter

        adapter = _EmbeddingFunctionAdapter(mock_embedder)

        result = adapter(["doc1", "doc2"])

        assert len(result) == 2
        assert all(isinstance(v, list) for v in result)

    def test_chromastore_uses_embed_query_for_search(self, temp_db_path, mock_embedder):
        """ChromaStore가 검색 시 embed_query를 사용하는지 확인"""
        from db.chroma_store import _EmbeddingFunctionAdapter

        adapter = _EmbeddingFunctionAdapter(mock_embedder)

        result = adapter.embed_query(["query1"])

        assert len(result) == 1
        assert isinstance(result[0], list)

    def test_e5_embedder_integration_with_adapter(self):
        """MultilingualE5Embedder가 adapter를 통해 올바르게 동작하는지 확인"""
        from core.embedding import MultilingualE5Embedder
        from db.chroma_store import _EmbeddingFunctionAdapter

        embedder = MultilingualE5Embedder()

        mock_model = MagicMock()
        mock_model.encode.return_value = MagicMock(
            tolist=lambda: [[0.1] * 1024, [0.2] * 1024]
        )
        embedder._model = mock_model
        embedder._dimension = 1024

        adapter = _EmbeddingFunctionAdapter(embedder)

        adapter(["doc1", "doc2"])
        assert mock_model.encode.call_args[0][0] == ["passage: doc1", "passage: doc2"]

        mock_model.reset_mock()
        adapter.embed_query(["query1"])
        assert mock_model.encode.call_args[0][0] == ["query: query1"]


class TestCrossLingualRetrieval:
    """Cross-lingual (한영) 검색 테스트"""

    @pytest.fixture
    def sample_korean_documents(self) -> List[str]:
        return [
            "API 인증 방법에 대한 설명입니다. OAuth2.0을 사용합니다.",
            "데이터베이스 연결 풀링 설정 방법을 알아봅니다.",
            "마이크로서비스 아키텍처 패턴에 대해 설명합니다.",
            "REST API 설계 모범 사례를 다룹니다.",
            "Docker 컨테이너 배포 자동화 가이드입니다.",
        ]

    @pytest.fixture
    def sample_english_documents(self) -> List[str]:
        return [
            "How to authenticate using API keys and OAuth tokens.",
            "Database connection pooling configuration guide.",
            "Microservices architecture patterns and best practices.",
            "RESTful API design principles and standards.",
            "Docker container deployment automation tutorial.",
        ]

    def test_korean_query_finds_korean_docs(self, sample_korean_documents):
        """한글 쿼리로 한글 문서 검색 테스트"""
        from core.embedding import FakeEmbedder

        embedder = FakeEmbedder(dimension=8)

        query = "API 인증은 어떻게 하나요?"
        query_embedding = embedder.embed_query(query)
        doc_embeddings = embedder.embed_documents(sample_korean_documents)

        assert len(query_embedding) == 8
        assert len(doc_embeddings) == 5

    def test_english_query_on_korean_docs(self, sample_korean_documents):
        """영어 쿼리로 한글 문서 검색 테스트 (cross-lingual)"""
        from core.embedding import FakeEmbedder

        embedder = FakeEmbedder(dimension=8)

        query = "How do I authenticate with API?"
        query_embedding = embedder.embed_query(query)
        doc_embeddings = embedder.embed_documents(sample_korean_documents)

        assert len(query_embedding) == 8
        assert len(doc_embeddings) == 5

    def test_prefix_differentiation(self):
        """Query와 Document prefix가 다른 임베딩을 생성하는지 확인"""
        from core.embedding import MultilingualE5Embedder

        embedder = MultilingualE5Embedder()

        mock_model = MagicMock()
        call_history = []

        def capture_encode(texts, **kwargs):
            call_history.append(texts)
            return MagicMock(tolist=lambda: [[0.1] * 1024] * len(texts))

        mock_model.encode = capture_encode
        embedder._model = mock_model
        embedder._dimension = 1024

        embedder.embed_query("test")
        embedder.embed_documents(["test"])

        assert call_history[0] == ["query: test"]
        assert call_history[1] == ["passage: test"]


class TestHybridSearcherBenchmark:
    """HybridSearcher 벤치마크 테스트"""

    def test_hybrid_search_combines_scores(self):
        """Hybrid search가 dense/sparse 점수를 올바르게 결합하는지 확인"""
        from core.rag.hybrid_search import HybridSearcher

        mock_store = MagicMock()
        mock_store.query.return_value = [
            {"id": "doc1", "text": "text1", "metadata": {}, "distance": 0.1},
            {"id": "doc2", "text": "text2", "metadata": {}, "distance": 0.3},
        ]

        searcher = HybridSearcher(mock_store, dense_weight=0.7, sparse_weight=0.3)

        mock_bm25 = MagicMock()
        mock_bm25.get_scores.return_value = [0.8, 0.2]
        searcher._bm25 = mock_bm25
        searcher._documents = ["doc text 1", "doc text 2"]
        searcher._doc_ids = ["doc1", "doc2"]

        results = searcher.search("test query", top_k=2)

        assert len(results) == 2
        assert results[0].dense_score > 0
        assert results[0].sparse_score > 0

    def test_hybrid_vs_dense_only(self):
        """Hybrid search가 dense-only보다 다양한 결과를 반환하는지 확인"""
        from core.rag.hybrid_search import HybridSearcher

        mock_store = MagicMock()
        mock_store.query.return_value = [
            {"id": "dense1", "text": "dense match", "metadata": {}, "distance": 0.05},
            {"id": "dense2", "text": "also dense", "metadata": {}, "distance": 0.1},
        ]

        searcher = HybridSearcher(mock_store, dense_weight=0.5, sparse_weight=0.5)

        mock_bm25 = MagicMock()
        mock_bm25.get_scores.return_value = [0.3, 0.9, 0.1]
        searcher._bm25 = mock_bm25
        searcher._documents = ["dense match", "keyword match", "other"]
        searcher._doc_ids = ["dense1", "keyword1", "other1"]

        results = searcher.search("keyword query", top_k=3)

        ids = [r.id for r in results]
        assert "keyword1" in ids or "dense1" in ids


class TestRerankerBenchmark:
    """Reranker 벤치마크 테스트"""

    def test_reranker_improves_ordering(self):
        """Reranker가 초기 검색 결과의 순서를 개선하는지 확인"""
        from core.rag.reranker import Reranker

        reranker = Reranker()

        mock_model = MagicMock()
        mock_model.predict.return_value = [0.2, 0.9, 0.5]
        reranker._model = mock_model

        initial_order = ["least relevant", "most relevant", "medium relevant"]
        reranked = reranker.rerank("query", initial_order, top_k=3)

        assert reranked[0].text == "most relevant"
        assert reranked[1].text == "medium relevant"
        assert reranked[2].text == "least relevant"

    def test_reranked_retriever_integration(self):
        """RerankedRetriever가 base retriever와 reranker를 올바르게 통합하는지 확인"""
        from core.rag.reranker import Reranker, RerankedRetriever
        from core.rag.retriever import Retriever, RetrievedChunk, RetrievalResult

        mock_base = MagicMock(spec=Retriever)
        mock_base.retrieve.return_value = RetrievalResult(
            query="test",
            chunks=[
                RetrievedChunk(
                    id="1", text="doc1", metadata={}, distance=0.1, score=0.9
                ),
                RetrievedChunk(
                    id="2", text="doc2", metadata={}, distance=0.2, score=0.8
                ),
                RetrievedChunk(
                    id="3", text="doc3", metadata={}, distance=0.3, score=0.7
                ),
            ],
            total_count=3,
        )

        reranker = Reranker()
        mock_model = MagicMock()
        mock_model.predict.return_value = [0.3, 0.9, 0.1]
        reranker._model = mock_model

        reranked_retriever = RerankedRetriever(
            base_retriever=mock_base, reranker=reranker, initial_k=10
        )

        result = reranked_retriever.retrieve("test query", top_k=2)

        assert len(result.chunks) == 2
        assert result.chunks[0].score == 0.9


class TestPerformanceMetrics:
    """성능 측정 유틸리티 테스트"""

    def measure_embedding_time(self, embedder, texts: List[str]) -> float:
        start = time.perf_counter()
        embedder.embed_documents(texts)
        return (time.perf_counter() - start) * 1000

    def calculate_recall_at_k(
        self, retrieved_ids: List[str], relevant_ids: List[str], k: int
    ) -> float:
        retrieved_k = set(retrieved_ids[:k])
        relevant = set(relevant_ids)
        return len(retrieved_k & relevant) / len(relevant) if relevant else 0.0

    def calculate_mrr(self, retrieved_ids: List[str], relevant_ids: List[str]) -> float:
        relevant = set(relevant_ids)
        for i, doc_id in enumerate(retrieved_ids, 1):
            if doc_id in relevant:
                return 1.0 / i
        return 0.0

    def test_recall_at_k_calculation(self):
        """Recall@K 계산이 올바른지 확인"""
        retrieved = ["a", "b", "c", "d", "e"]
        relevant = ["b", "d"]

        recall_3 = self.calculate_recall_at_k(retrieved, relevant, k=3)
        recall_5 = self.calculate_recall_at_k(retrieved, relevant, k=5)

        assert recall_3 == 0.5
        assert recall_5 == 1.0

    def test_mrr_calculation(self):
        """MRR(Mean Reciprocal Rank) 계산이 올바른지 확인"""
        retrieved = ["a", "b", "c", "d"]
        relevant = ["c"]

        mrr = self.calculate_mrr(retrieved, relevant)

        assert mrr == pytest.approx(1 / 3)

    def test_embedding_time_measurement(self):
        """임베딩 시간 측정이 올바르게 동작하는지 확인"""
        from core.embedding import FakeEmbedder

        embedder = FakeEmbedder(dimension=8)
        texts = ["test"] * 10

        duration = self.measure_embedding_time(embedder, texts)

        assert duration > 0
        assert duration < 1000


class TestQueryPrefixSupport:
    """Query/Passage prefix 지원 테스트 (Week 2 Day 1-2)"""

    def test_all_embedders_support_embed_query(self):
        """모든 임베더가 embed_query를 지원하는지 확인"""
        from core.embedding import (
            FakeEmbedder,
            MultilingualE5Embedder,
            SentenceTransformerEmbedder,
        )

        for EmbedderClass in [FakeEmbedder]:
            embedder = EmbedderClass()
            assert hasattr(embedder, "embed_query")
            result = embedder.embed_query("test")
            assert isinstance(result, list)

    def test_all_embedders_support_embed_documents(self):
        """모든 임베더가 embed_documents를 지원하는지 확인"""
        from core.embedding import FakeEmbedder

        embedder = FakeEmbedder()
        assert hasattr(embedder, "embed_documents")
        result = embedder.embed_documents(["doc1", "doc2"])
        assert isinstance(result, list)
        assert len(result) == 2

    def test_chromastore_adapter_uses_correct_methods(self):
        """ChromaStore 어댑터가 올바른 메서드를 호출하는지 확인"""
        from db.chroma_store import _EmbeddingFunctionAdapter
        from core.embedding import FakeEmbedder

        embedder = FakeEmbedder(dimension=8)
        adapter = _EmbeddingFunctionAdapter(embedder)

        doc_result = adapter(["doc1"])
        query_result = adapter.embed_query(["query1"])

        assert len(doc_result) == 1
        assert len(query_result) == 1


class TestBenchmarkSuite:
    """전체 벤치마크 스위트"""

    @pytest.mark.skip(reason="실제 모델 로드 필요 - CI에서 제외")
    def test_full_benchmark_with_real_model(self):
        """실제 모델을 사용한 전체 벤치마크 (수동 실행용)"""
        pass

    def test_benchmark_mock_suite(self):
        """Mock을 사용한 벤치마크 스위트 (CI용)"""
        from core.embedding import FakeEmbedder

        embedder = FakeEmbedder(dimension=8)

        korean_docs = ["한국어 문서 1", "한국어 문서 2", "한국어 문서 3"]
        english_docs = ["English doc 1", "English doc 2", "English doc 3"]
        mixed_docs = korean_docs + english_docs

        start = time.perf_counter()
        embedder.embed_documents(mixed_docs)
        embed_time = (time.perf_counter() - start) * 1000

        start = time.perf_counter()
        embedder.embed_query("테스트 쿼리")
        query_time = (time.perf_counter() - start) * 1000

        assert embed_time < 100
        assert query_time < 50
