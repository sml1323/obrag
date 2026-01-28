from sqlmodel import SQLModel, Field, Relationship
from typing import List, Optional
from datetime import datetime

class Topic(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

    sessions: List["Session"] = Relationship(back_populates="topic")

class Session(SQLModel, table=True):
    id: str = Field(primary_key=True)  # uuid
    topic_id: Optional[int] = Field(default=None, foreign_key="topic.id")
    title: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

    topic: Optional[Topic] = Relationship(back_populates="sessions")
    messages: List["Message"] = Relationship(back_populates="session")

class Message(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    session_id: str = Field(foreign_key="session.id")
    role: str  # user, assistant, system
    content: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

    session: Optional[Session] = Relationship(back_populates="messages")
