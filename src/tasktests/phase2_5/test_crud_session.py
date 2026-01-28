from fastapi.testclient import TestClient
import pytest
from sqlmodel import Session, SQLModel, create_engine

from api.main import app
from api.deps import get_session
from core.domain.chat import Topic, Session as ChatSession, Message  # Ensure models are registered
from sqlalchemy.pool import StaticPool

@pytest.fixture(name="client")
def client_fixture():
    test_engine = create_engine(
        "sqlite://", 
        connect_args={"check_same_thread": False}, 
        poolclass=StaticPool
    )
    SQLModel.metadata.create_all(test_engine)

    def get_session_override():
        with Session(test_engine) as session:
            yield session

    app.dependency_overrides[get_session] = get_session_override
    yield TestClient(app)
    app.dependency_overrides.clear()

def test_create_session(client):
    response = client.post("/sessions", json={"id": "uuid-123", "title": "My Session", "topic_id": None})
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "uuid-123"
    assert data["title"] == "My Session"

def test_create_message(client):
    # 1. Create session first
    client.post("/sessions", json={"id": "uuid-123", "title": "My Session"})
    
    # 2. Add message
    msg_data = {"role": "user", "content": "Hello World"}
    response = client.post("/sessions/uuid-123/messages", json=msg_data)
    assert response.status_code == 200
    data = response.json()
    assert data["content"] == "Hello World"
    assert data["session_id"] == "uuid-123"
