import pytest
from unittest.mock import MagicMock
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine, select
from sqlmodel.pool import StaticPool

from api.main import app
from api.deps import get_session, get_rag_chain
from core.rag.retriever import RetrievalResult
from dtypes.api import SourceChunk

# Import models to register them
from core.domain.chat import Topic, Session as ChatSession, Message as ChatMessage

@pytest.fixture(name="session")
def session_fixture():
    engine = create_engine(
        "sqlite://", 
        connect_args={"check_same_thread": False}, 
        poolclass=StaticPool
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session

@pytest.fixture(name="mock_chain")
def mock_chain_fixture():
    chain = MagicMock()
    
    # Mock query
    mock_response = MagicMock()
    mock_response.answer = "Mock Answer"
    mock_response.retrieval_result = RetrievalResult(chunks=[], query="mock", total_count=0)
    mock_response.model = "mock-gpt"
    mock_response.usage = {"total_tokens": 10}
    chain.query.return_value = mock_response

    # Mock query_with_history matches signature
    mock_hist_response = MagicMock()
    mock_hist_response.answer = "Mock Answer with History"
    mock_hist_response.retrieval_result = RetrievalResult(chunks=[], query="mock", total_count=0)
    mock_hist_response.model = "mock-gpt"
    mock_hist_response.usage = {"total_tokens": 15}
    chain.query_with_history.return_value = mock_hist_response

    # Mock stream_query
    chain.stream_query.return_value = (
        RetrievalResult(chunks=[], query="mock", total_count=0),
        iter(["Chunk1", " ", "Chunk2"])
    )
    chain._llm.model_name = "mock-gpt"
    return chain

@pytest.fixture(name="client")
def client_fixture(session, mock_chain):
    def get_session_override():
        return session
    
    def get_chain_override():
        return mock_chain

    app.dependency_overrides[get_session] = get_session_override
    app.dependency_overrides[get_rag_chain] = get_chain_override
    
    with TestClient(app) as client:
        yield client
    
    app.dependency_overrides.clear()

def test_chat_persistence_basic(client, session, mock_chain):
    """Session ID 없이 호출 시 저장 안됨 확인"""
    response = client.post("/chat", json={"question": "Hello"})
    assert response.status_code == 200
    
    # DB Empty
    assert len(session.exec(select(ChatSession)).all()) == 0
    assert len(session.exec(select(ChatMessage)).all()) == 0

def test_chat_persistence_stateful(client, session, mock_chain):
    """Session ID로 호출 시 저장 및 재사용 확인"""
    session_id = "test-session-1"
    
    # 1. First Call
    response = client.post("/chat", json={"question": "Hi", "session_id": session_id})
    assert response.status_code == 200
    assert response.json()["answer"] == "Mock Answer"
    
    # Verify Save
    db_session = session.get(ChatSession, session_id)
    assert db_session is not None
    assert len(db_session.messages) == 2  # User + Assistant
    assert db_session.messages[0].role == "user"
    assert db_session.messages[0].content == "Hi"
    assert db_session.messages[1].role == "assistant"
    assert db_session.messages[1].content == "Mock Answer"
    
    # 2. Second Call
    response = client.post("/chat", json={"question": "Follow up", "session_id": session_id})
    assert response.status_code == 200
    assert response.json()["answer"] == "Mock Answer with History"
    
    # Verify query_with_history called
    mock_chain.query_with_history.assert_called()
    call_args = mock_chain.query_with_history.call_args
    history_arg = call_args[1].get('history')
    assert len(history_arg) == 2
    assert history_arg[0]['role'] == 'user'
    assert history_arg[0]['content'] == 'Hi'
    
    # Verify DB has 4 messages now
    session.refresh(db_session)
    assert len(db_session.messages) == 4

def test_chat_persistence_stream(client, session, mock_chain):
    """스트리밍 응답 완료 후 DB 저장 확인."""
    session_id = "test-session-stream"
    
    response = client.post(
        "/chat/stream", 
        json={"question": "Stream me", "session_id": session_id}
    )
    assert response.status_code == 200
    
    # Consume stream
    chunks = list(response.iter_lines())
    assert len(chunks) > 0
    
    # Verify DB Save
    db_session = session.get(ChatSession, session_id)
    assert db_session is not None
    assert len(db_session.messages) == 2
    assert db_session.messages[1].content == "Chunk1 Chunk2"
