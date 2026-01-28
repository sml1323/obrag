from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session
from typing import List

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
