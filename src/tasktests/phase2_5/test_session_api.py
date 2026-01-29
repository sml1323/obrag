from fastapi.testclient import TestClient
import pytest
from sqlmodel import Session, SQLModel, create_engine, select
import uuid

from api.main import app
from api.deps import get_session
from core.domain.chat import Topic, Session as ChatSession, Message
from sqlalchemy.pool import StaticPool

@pytest.fixture(name="engine")
def engine_fixture():
    engine = create_engine(
        "sqlite://", 
        connect_args={"check_same_thread": False}, 
        poolclass=StaticPool
    )
    SQLModel.metadata.create_all(engine)
    return engine

@pytest.fixture(name="client")
def client_fixture(engine):
    def get_session_override():
        with Session(engine) as session:
            yield session

    app.dependency_overrides[get_session] = get_session_override
    yield TestClient(app)
    app.dependency_overrides.clear()

def test_list_sessions(client):
    # Create sessions
    s1_id = str(uuid.uuid4())
    client.post("/sessions", json={"id": s1_id, "title": "Session 1"})
    
    s2_id = str(uuid.uuid4())
    client.post("/sessions", json={"id": s2_id, "title": "Session 2"})

    response = client.get("/sessions")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 2
    # Verify order (desc by created_at) is implicitly checked if we assume the last created shows first if timestamps differ.
    # But in fast tests, timestamps might be identical.
    ids = [s["id"] for s in data]
    assert s1_id in ids
    assert s2_id in ids

def test_list_sessions_filter_topic(client, engine):
    # Create topic
    with Session(engine) as session:
        topic = Topic(title="Test Topic")
        session.add(topic)
        session.commit()
        session.refresh(topic)
        topic_id = topic.id
    
    # Create session linked to topic
    s1_id = str(uuid.uuid4())
    client.post("/sessions", json={"id": s1_id, "title": "Topic Session", "topic_id": topic_id})
    
    # Create session not in topic
    s2_id = str(uuid.uuid4())
    client.post("/sessions", json={"id": s2_id, "title": "No Topic Session"})
    
    # Filter
    response = client.get(f"/sessions?topic_id={topic_id}")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["id"] == s1_id

def test_get_session_detail(client):
    s_id = str(uuid.uuid4())
    client.post("/sessions", json={"id": s_id, "title": "Details"})
    
    response = client.get(f"/sessions/{s_id}")
    assert response.status_code == 200
    assert response.json()["title"] == "Details"
    
    # 404
    response = client.get(f"/sessions/non-existent")
    assert response.status_code == 404

def test_delete_session(client, engine):
    s_id = str(uuid.uuid4())
    client.post("/sessions", json={"id": s_id, "title": "To Delete"})
    
    # Add message
    client.post(f"/sessions/{s_id}/messages", json={"role": "user", "content": "hi"})
    
    # Delete
    response = client.delete(f"/sessions/{s_id}")
    assert response.status_code == 200
    
    # Verify 404
    response = client.get(f"/sessions/{s_id}")
    assert response.status_code == 404
    
    # Verify messages deleted in DB
    with Session(engine) as session:
        msgs = session.exec(select(Message).where(Message.session_id == s_id)).all()
        assert len(msgs) == 0

def test_list_messages(client):
    s_id = str(uuid.uuid4())
    client.post("/sessions", json={"id": s_id, "title": "Chat"})
    
    client.post(f"/sessions/{s_id}/messages", json={"role": "user", "content": "msg1"})
    client.post(f"/sessions/{s_id}/messages", json={"role": "assistant", "content": "msg2"})
    
    response = client.get(f"/sessions/{s_id}/messages")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["content"] == "msg1"
    assert data[1]["content"] == "msg2"
    
    # 404
    response = client.get("/sessions/wrong-id/messages")
    assert response.status_code == 404
