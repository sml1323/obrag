import pytest
from sqlmodel import Session, select, SQLModel

from db.engine import engine, create_db_and_tables
from core.domain.chat import Topic, Session as ChatSession, Message

# Use in-memory DB for testing
@pytest.fixture(name="session")
def session_fixture():
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session
    SQLModel.metadata.drop_all(engine)

def test_create_tables(session):
    # Just verify tables exist by trying to insert and select
    topic = Topic(title="Test Topic")
    session.add(topic)
    session.commit()
    
    chat_session = ChatSession(id="test-session-id", title="Test Session", topic_id=topic.id)
    session.add(chat_session)
    session.commit()
    
    message = Message(session_id="test-session-id", role="user", content="Hello")
    session.add(message)
    session.commit()

    # Query
    topics = session.exec(select(Topic)).all()
    assert len(topics) == 1
    assert topics[0].title == "Test Topic"
