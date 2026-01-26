"""
Chat API Endpoint Tests

채팅 엔드포인트 테스트.
완전한 Mock을 사용하여 외부 의존성 없이 테스트.
"""

import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch
from dataclasses import dataclass
from typing import Iterator

import pytest

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


# ============================================================================
# Mock Classes (to avoid import chain issues)
# ============================================================================

@dataclass
class MockRetrievedChunk:
    """Mock RetrievedChunk."""
    content: str
    score: float
    metadata: dict


@dataclass  
class MockRetrievalResult:
    """Mock RetrievalResult."""
    chunks: list


@dataclass
class MockLLMResponse:
    """Mock LLMResponse."""
    content: str
    model: str
    usage: dict


class MockFakeLLM:
    """Mock FakeLLM."""
    def __init__(self, response: str = "Test response"):
        self._response = response
        self._model_name = "fake-llm"
    
    def generate(self, messages, *, temperature=0.7, max_tokens=None) -> MockLLMResponse:
        return MockLLMResponse(
            content=self._response,
            model=self._model_name,
            usage={"input_tokens": 10, "output_tokens": 5},
        )
    
    def stream_generate(self, messages, *, temperature=0.7, max_tokens=None) -> Iterator[str]:
        for word in self._response.split():
            yield word + " "
    
    @property
    def model_name(self) -> str:
        return self._model_name


@dataclass
class MockAppState:
    """Mock AppState."""
    chroma_store: MagicMock
    rag_chain: MagicMock


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def mock_retrieval_result():
    """Mock RetrievalResult."""
    return MockRetrievalResult(
        chunks=[
            MockRetrievedChunk(
                content="Test content 1",
                score=0.9,
                metadata={"source": "test1.md"},
            ),
            MockRetrievedChunk(
                content="Test content 2",
                score=0.8,
                metadata={"source": "test2.md"},
            ),
        ]
    )


@pytest.fixture
def mock_rag_chain(mock_retrieval_result):
    """Mock RAGChain."""
    chain = MagicMock()
    fake_llm = MockFakeLLM(response="This is a test answer.")
    
    # query() 모킹
    chain.query.return_value = MagicMock(
        answer="This is a test answer.",
        retrieval_result=mock_retrieval_result,
        model="fake-llm",
        usage={"input_tokens": 10, "output_tokens": 5},
    )
    
    # query_with_history() 모킹
    chain.query_with_history.return_value = MagicMock(
        answer="This is a test answer with history.",
        retrieval_result=mock_retrieval_result,
        model="fake-llm",
        usage={"input_tokens": 15, "output_tokens": 8},
    )
    
    # stream_query() 모킹
    def make_stream_gen():
        yield "This "
        yield "is "
        yield "streaming."
    
    chain.stream_query.return_value = (mock_retrieval_result, make_stream_gen())
    chain._llm = fake_llm
    
    return chain


@pytest.fixture
def mock_app_state(mock_rag_chain):
    """Mock AppState."""
    chroma_store = MagicMock()
    chroma_store.get_stats.return_value = {"documents": 10, "collection": "test"}
    
    return MockAppState(
        chroma_store=chroma_store,
        rag_chain=mock_rag_chain,
    )


@pytest.fixture
def client(mock_app_state):
    """테스트 클라이언트."""
    # Mock heavy dependencies before importing
    with patch.dict('sys.modules', {
        'chromadb': MagicMock(),
        'openai': MagicMock(),
        'google': MagicMock(),
        'google.genai': MagicMock(),
        'google.genai.types': MagicMock(),
    }):
        from api.main import create_app
        from fastapi.testclient import TestClient
        
        app = create_app()
        app.state.deps = mock_app_state
        
        return TestClient(app)


# ============================================================================
# Endpoint Existence Tests
# ============================================================================

class TestEndpointExistence:
    """엔드포인트 존재 확인 테스트."""
    
    def test_chat_endpoint_exists(self, client):
        """POST /chat 엔드포인트 존재 확인."""
        response = client.post("/chat", json={"question": "test"})
        assert response.status_code != 404
    
    def test_chat_stream_endpoint_exists(self, client):
        """POST /chat/stream 엔드포인트 존재 확인."""
        response = client.post("/chat/stream", json={"question": "test"})
        assert response.status_code != 404
    
    def test_chat_history_endpoint_exists(self, client):
        """POST /chat/history 엔드포인트 존재 확인."""
        response = client.post("/chat/history", json={"question": "test"})
        assert response.status_code != 404


# ============================================================================
# Response Format Tests
# ============================================================================

class TestChatEndpoint:
    """POST /chat 엔드포인트 테스트."""
    
    def test_chat_returns_valid_response(self, client):
        """정상 응답 형식 확인."""
        response = client.post("/chat", json={
            "question": "What is RAG?",
            "top_k": 3,
            "temperature": 0.5,
        })
        
        assert response.status_code == 200
        data = response.json()
        
        # ChatResponse 형식 검증
        assert "answer" in data
        assert "sources" in data
        assert "model" in data
        assert "usage" in data
    
    def test_chat_sources_format(self, client):
        """sources 형식 확인."""
        response = client.post("/chat", json={"question": "test"})
        data = response.json()
        
        assert isinstance(data["sources"], list)


class TestChatStreamEndpoint:
    """POST /chat/stream 엔드포인트 테스트."""
    
    def test_stream_returns_event_stream(self, client, mock_rag_chain, mock_retrieval_result):
        """SSE 응답 Content-Type 확인."""
        def stream_gen():
            yield "Test"
        mock_rag_chain.stream_query.return_value = (mock_retrieval_result, stream_gen())
        
        response = client.post("/chat/stream", json={"question": "test"})
        
        assert response.status_code == 200
        assert "text/event-stream" in response.headers["content-type"]
    
    def test_stream_returns_sse_format(self, client, mock_rag_chain, mock_retrieval_result):
        """SSE 형식 (data: ...) 확인."""
        def stream_gen():
            yield "Test"
        mock_rag_chain.stream_query.return_value = (mock_retrieval_result, stream_gen())
        
        response = client.post("/chat/stream", json={"question": "test"})
        
        content = response.text
        assert "data:" in content


class TestChatHistoryEndpoint:
    """POST /chat/history 엔드포인트 테스트."""
    
    def test_chat_history_with_valid_history(self, client):
        """대화 이력 포함 요청."""
        response = client.post("/chat/history", json={
            "question": "And what about LLM?",
            "history": [
                {"role": "user", "content": "What is RAG?"},
                {"role": "assistant", "content": "RAG is Retrieval-Augmented Generation."},
            ],
            "top_k": 3,
        })
        
        assert response.status_code == 200
        data = response.json()
        assert "answer" in data


# ============================================================================
# Input Validation Tests
# ============================================================================

class TestInputValidation:
    """입력 검증 테스트."""
    
    def test_empty_question_rejected(self, client):
        """빈 question 거부 (422 에러)."""
        response = client.post("/chat", json={"question": ""})
        assert response.status_code == 422
    
    def test_invalid_temperature_rejected(self, client):
        """잘못된 temperature 범위 거부."""
        response = client.post("/chat", json={
            "question": "test",
            "temperature": 3.0,  # 범위 초과 (0.0 ~ 2.0)
        })
        assert response.status_code == 422
    
    def test_invalid_top_k_rejected(self, client):
        """잘못된 top_k 값 거부."""
        response = client.post("/chat", json={
            "question": "test",
            "top_k": 0,  # 최소 1 이상
        })
        assert response.status_code == 422
    
    def test_invalid_history_format_rejected(self, client):
        """잘못된 history 형식 거부."""
        response = client.post("/chat/history", json={
            "question": "test",
            "history": [{"role": "invalid_role", "content": "test"}],
        })
        assert response.status_code == 422
