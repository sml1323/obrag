from fastapi.testclient import TestClient
import pytest
from sqlmodel import Session, SQLModel, create_engine
from typing import Generator

from api.main import app
from api.deps import get_session
# Note: In real setup, we might want to override engine differently or use a test DB file.
# For simplicity, we are using the same engine but we could mock dependency.
from db.engine import engine
from core.domain.chat import Topic, Session as ChatSession, Message  # Ensure models are registered
from sqlalchemy.pool import StaticPool

@pytest.fixture(name="client")
def client_fixture():
    # Use a separate in-memory SQLite for testing to avoid polluting file DB?
    # Or just use the file DB but clean it?
    # Ideally, override dependency with in-memory DB.

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

def test_create_topic(client):
    response = client.post("/topics", json={"title": "New Topic"})
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "New Topic"
    assert "id" in data

def test_read_topics(client):
    client.post("/topics", json={"title": "Topic 1"})
    client.post("/topics", json={"title": "Topic 2"})
    
    response = client.get("/topics")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 2

def test_delete_topic(client):
    response = client.post("/topics", json={"title": "To Delete"})
    topic_id = response.json()["id"]
    
    del_response = client.delete(f"/topics/{topic_id}")
    assert del_response.status_code == 200
    
    # Verify deletion
    get_response = client.get("/topics")
    ids = [t["id"] for t in get_response.json()]
    assert topic_id not in ids
