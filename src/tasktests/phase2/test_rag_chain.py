"""RAGChain 단위 테스트"""

import pytest
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.rag.chain import RAGChain, RAGResponse
from core.rag.prompt import CONCISE_TEMPLATE
from core.llm.strategy import FakeLLM


class MockChromaStore:
    """테스트용 Mock ChromaStore"""

    def query(self, query_text, n_results=5, **kwargs):
        return [
            {
                "id": "chunk_1",
                "text": "RAG는 Retrieval Augmented Generation의 약자입니다.",
                "metadata": {"source": "rag_intro.md"},
                "distance": 0.5,
            },
            {
                "id": "chunk_2",
                "text": "RAG는 검색과 생성을 결합합니다.",
                "metadata": {"source": "rag_details.md"},
                "distance": 0.8,
            },
        ]


class TestRAGChain:
    """RAGChain 기본 테스트"""

    @pytest.fixture
    def chain(self):
        from core.rag import Retriever
        store = MockChromaStore()
        retriever = Retriever(store)
        llm = FakeLLM(response="This is the answer about RAG.")
        return RAGChain(retriever=retriever, llm=llm)

    def test_query_returns_rag_response(self, chain):
        """query()가 RAGResponse를 반환하는지 확인"""
        response = chain.query("What is RAG?")

        assert isinstance(response, RAGResponse)
        assert response.answer == "This is the answer about RAG."
        assert response.model == "fake-llm"

    def test_query_includes_retrieval_result(self, chain):
        """검색 결과가 포함되는지 확인"""
        response = chain.query("What is RAG?")

        assert response.retrieval_result is not None
        assert response.retrieval_result.total_count == 2

    def test_query_includes_usage(self, chain):
        """토큰 사용량이 포함되는지 확인"""
        response = chain.query("What is RAG?")

        assert response.usage is not None
        assert "input_tokens" in response.usage
        assert "output_tokens" in response.usage

    def test_query_with_top_k(self, chain):
        """top_k 파라미터 전달 확인"""
        response = chain.query("Test", top_k=1)
        # MockStore는 항상 2개 반환하지만 파라미터가 전달되는지만 확인
        assert response.retrieval_result is not None

    def test_custom_template(self):
        """커스텀 템플릿 적용 확인"""
        from core.rag import Retriever
        store = MockChromaStore()
        retriever = Retriever(store)
        llm = FakeLLM()

        chain = RAGChain(
            retriever=retriever,
            llm=llm,
            template=CONCISE_TEMPLATE
        )

        assert chain.prompt_builder.template.name == "concise"


class TestRAGChainWithHistory:
    """멀티턴 대화 테스트"""

    @pytest.fixture
    def chain(self):
        from core.rag import Retriever
        store = MockChromaStore()
        retriever = Retriever(store)
        llm = FakeLLM(response="Follow-up answer")
        return RAGChain(retriever=retriever, llm=llm)

    def test_query_with_history(self, chain):
        """대화 이력 포함 질의 확인"""
        history = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi!"},
        ]
        response = chain.query_with_history(
            question="What is RAG?",
            history=history
        )

        assert response.answer == "Follow-up answer"

    def test_query_with_empty_history(self, chain):
        """빈 이력도 정상 동작하는지 확인"""
        response = chain.query_with_history(
            question="What is RAG?",
            history=[]
        )

        assert response.answer == "Follow-up answer"

    def test_query_with_none_history(self, chain):
        """history=None도 정상 동작하는지 확인"""
        response = chain.query_with_history(
            question="What is RAG?",
            history=None
        )

        assert response.answer == "Follow-up answer"


class TestRAGResponse:
    """RAGResponse 데이터클래스 테스트"""

    def test_rag_response_fields(self):
        """RAGResponse가 모든 필드를 포함하는지 확인"""
        from core.rag import RetrievalResult

        result = RetrievalResult(query="test", chunks=[], total_count=0)
        response = RAGResponse(
            answer="Test answer",
            retrieval_result=result,
            model="test-model",
            usage={"input_tokens": 10, "output_tokens": 5}
        )

        assert response.answer == "Test answer"
        assert response.model == "test-model"
        assert response.usage["input_tokens"] == 10


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
