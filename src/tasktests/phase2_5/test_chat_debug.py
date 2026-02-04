import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from api.main import app
from api.deps import get_session, get_rag_chain
from core.domain.chat import Topic, Session as ChatSession, Message as ChatMessage
from core.rag.retriever import RetrievalResult


@pytest.fixture(name="db_session")
def db_session_fixture():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


@pytest.fixture(name="mock_chain")
def mock_chain_fixture():
    chain = MagicMock()

    mock_response = MagicMock()
    mock_response.answer = "Debug Answer"
    mock_response.retrieval_result = RetrievalResult(
        chunks=[], query="debug", total_count=0
    )
    mock_response.model = "debug-llm"
    mock_response.usage = {"total_tokens": 1}
    chain.query.return_value = mock_response

    mock_hist_response = MagicMock()
    mock_hist_response.answer = "Debug Answer with History"
    mock_hist_response.retrieval_result = RetrievalResult(
        chunks=[], query="debug", total_count=0
    )
    mock_hist_response.model = "debug-llm"
    mock_hist_response.usage = {"total_tokens": 2}
    chain.query_with_history.return_value = mock_hist_response

    chain.stream_query.return_value = (
        RetrievalResult(chunks=[], query="debug", total_count=0),
        iter(["Hello", " ", "World"]),
    )
    chain._llm.model_name = "debug-llm"
    return chain


@pytest.fixture(name="client")
def client_fixture(db_session, mock_chain):
    def get_session_override():
        return db_session

    def get_chain_override():
        return mock_chain

    app.dependency_overrides[get_session] = get_session_override
    app.dependency_overrides[get_rag_chain] = get_chain_override

    with TestClient(app) as client:
        yield client

    app.dependency_overrides.clear()


def test_debug_chat_basic_flow(client, db_session):
    response = client.post("/chat", json={"question": "Hello"})
    assert response.status_code == 200

    data = response.json()
    assert data["answer"] == "Debug Answer"

    session_id = "debug-session"
    response = client.post(
        "/chat",
        json={"question": "Hi", "session_id": session_id},
    )
    assert response.status_code == 200

    response = client.post(
        "/chat",
        json={"question": "Follow up", "session_id": session_id},
    )
    assert response.status_code == 200

    db_session = db_session.get(ChatSession, session_id)
    assert db_session is not None
    assert len(db_session.messages) == 4


def test_debug_chat_stream_flow(client, db_session):
    session_id = "debug-stream"
    response = client.post(
        "/chat/stream",
        json={"question": "Stream", "session_id": session_id},
    )
    assert response.status_code == 200

    chunks = list(response.iter_lines())
    assert len(chunks) > 0

    db_session = db_session.get(ChatSession, session_id)
    assert db_session is not None
    assert len(db_session.messages) == 2
