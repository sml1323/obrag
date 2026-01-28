from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from typing import List

from api.deps import get_session
from core.domain.chat import Topic

router = APIRouter(prefix="/topics", tags=["topics"])

@router.post("", response_model=Topic)
def create_topic(topic: Topic, session: Session = Depends(get_session)):
    session.add(topic)
    session.commit()
    session.refresh(topic)
    return topic

@router.get("", response_model=List[Topic])
def read_topics(session: Session = Depends(get_session)):
    topics = session.exec(select(Topic)).all()
    return topics

@router.delete("/{topic_id}")
def delete_topic(topic_id: int, session: Session = Depends(get_session)):
    topic = session.get(Topic, topic_id)
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")
    session.delete(topic)
    session.commit()
    return {"ok": True}
