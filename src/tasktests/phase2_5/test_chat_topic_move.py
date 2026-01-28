from fastapi.testclient import TestClient
import pytest
from sqlmodel import Session, SQLModel, create_engine
from sqlalchemy.pool import StaticPool

from api.main import app
from api.deps import get_session
from core.domain.chat import Topic, Session as ChatSession

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

def test_create_session_with_valid_topic(client):
    # 1. Create Topic
    t_resp = client.post("/topics", json={"title": "Test Topic"})
    topic_id = t_resp.json()["id"]
    
    # 2. Create Session with Topic
    response = client.post("/sessions", json={
        "id": "sess-1", 
        "title": "Topic Session", 
        "topic_id": topic_id
    })
    assert response.status_code == 200
    data = response.json()
    assert data["topic_id"] == topic_id

def test_create_session_with_invalid_topic(client):
    response = client.post("/sessions", json={
        "id": "sess-2", 
        "title": "Invalid Topic Session", 
        "topic_id": 999
    })
    assert response.status_code == 404

def test_move_session_to_topic(client):
    # 1. Create Session without Topic
    client.post("/sessions", json={"id": "sess-3", "title": "No Topic Session"})
    
    # 2. Create Topic
    t_resp = client.post("/topics", json={"title": "New Topic"})
    topic_id = t_resp.json()["id"]
    
    # 3. Move Session to Topic
    response = client.patch("/sessions/sess-3", json={"topic_id": topic_id})
    assert response.status_code == 200
    assert response.json()["topic_id"] == topic_id

def test_remove_session_from_topic(client):
    # 1. Create Topic & Session with Topic
    t_resp = client.post("/topics", json={"title": "Test Topic"})
    topic_id = t_resp.json()["id"]
    
    client.post("/sessions", json={"id": "sess-4", "title": "Topic Session", "topic_id": topic_id})
    
    # 2. Remove Topic (topic_id = None)
    response = client.patch("/sessions/sess-4", json={"topic_id": None})
    assert response.status_code == 200
    assert response.json()["topic_id"] is None

def test_move_session_to_invalid_topic(client):
    # 1. Create Session
    client.post("/sessions", json={"id": "sess-5", "title": "Test Session"})
    
    # 2. Move to invalid topic
    response = client.patch("/sessions/sess-5", json={"topic_id": 999})
    assert response.status_code == 404

def test_update_session_title(client):
    # 1. Create Session
    client.post("/sessions", json={"id": "sess-6", "title": "Old Title"})
    
    # 2. Update Title
    response = client.patch("/sessions/sess-6", json={"title": "New Title"})
    assert response.status_code == 200
    assert response.json()["title"] == "New Title"
