from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select, desc
from typing import List, Optional

from api.deps import get_session
from core.domain.chat import Session as ChatSession, Message, Topic
from dtypes.api import SessionUpdate

router = APIRouter(prefix="/sessions", tags=["sessions"])

@router.post("", response_model=ChatSession)
def create_session(chat_session: ChatSession, session: Session = Depends(get_session)):
    if chat_session.topic_id is not None:
        topic = session.get(Topic, chat_session.topic_id)
        if not topic:
            raise HTTPException(status_code=404, detail="Topic not found")
            
    session.add(chat_session)
    session.commit()
    session.refresh(chat_session)
    return chat_session

@router.patch("/{session_id}", response_model=ChatSession)
def update_session(session_id: str, update_data: SessionUpdate, session: Session = Depends(get_session)):
    chat_session = session.get(ChatSession, session_id)
    if not chat_session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    data = update_data.model_dump(exclude_unset=True)
    
    if "topic_id" in data and data["topic_id"] is not None:
        topic = session.get(Topic, data["topic_id"])
        if not topic:
            raise HTTPException(status_code=404, detail="Topic not found")
            
    for key, value in data.items():
        setattr(chat_session, key, value)
        
    session.add(chat_session)
    session.commit()
    session.refresh(chat_session)
    return chat_session

@router.post("/{session_id}/messages", response_model=Message)
def create_message(session_id: str, message: Message, session: Session = Depends(get_session)):
    # Verify session exists
    chat_session = session.get(ChatSession, session_id)
    if not chat_session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    message.session_id = session_id
    session.add(message)
    session.commit()
    session.refresh(message)
    return message

@router.get("", response_model=List[ChatSession])
def read_sessions(
    topic_id: Optional[int] = None,
    offset: int = 0,
    limit: int = 100,
    session: Session = Depends(get_session)
):
    query = select(ChatSession)
    if topic_id is not None:
        query = query.where(ChatSession.topic_id == topic_id)
    
    query = query.order_by(desc(ChatSession.created_at)).offset(offset).limit(limit)
    return session.exec(query).all()

@router.get("/{session_id}", response_model=ChatSession)
def read_session(session_id: str, session: Session = Depends(get_session)):
    chat_session = session.get(ChatSession, session_id)
    if not chat_session:
        raise HTTPException(status_code=404, detail="Session not found")
    return chat_session

@router.delete("/{session_id}")
def delete_session(session_id: str, session: Session = Depends(get_session)):
    chat_session = session.get(ChatSession, session_id)
    if not chat_session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Manual cascade delete for messages
    messages = session.exec(select(Message).where(Message.session_id == session_id)).all()
    for message in messages:
        session.delete(message)
        
    session.delete(chat_session)
    session.commit()
    return {"ok": True}

@router.get("/{session_id}/messages", response_model=List[Message])
def read_session_messages(session_id: str, session: Session = Depends(get_session)):
    # Check if session exists first? Or just return empty list?
    # Usually better to 404 if session doesn't exist.
    chat_session = session.get(ChatSession, session_id)
    if not chat_session:
        raise HTTPException(status_code=404, detail="Session not found")
        
    query = select(Message).where(Message.session_id == session_id).order_by(Message.created_at)
    return session.exec(query).all()
