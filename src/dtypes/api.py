"""
API Request/Response Schemas

ChatEndpoint를 위한 Pydantic 모델 정의.
"""

from pydantic import BaseModel, Field, field_validator
from typing import List, Optional


# ============================================================================
# Request Models
# ============================================================================

class ChatRequest(BaseModel):
    """채팅 요청 스키마."""
    
    question: str = Field(..., min_length=1, description="질문 내용")
    top_k: int = Field(default=5, ge=1, le=20, description="검색할 문서 수")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0, description="응답 다양성")
    max_tokens: Optional[int] = Field(default=None, ge=1, description="최대 토큰 수")


class ChatHistoryRequest(ChatRequest):
    """대화 이력 포함 채팅 요청."""
    
    history: List[dict] = Field(
        default_factory=list,
        description="대화 이력 [{'role': 'user'|'assistant', 'content': '...'}]"
    )
    
    @field_validator("history")
    @classmethod
    def validate_history(cls, v):
        for msg in v:
            if "role" not in msg or "content" not in msg:
                raise ValueError("Each history message must have 'role' and 'content'")
            if msg["role"] not in ("user", "assistant", "system"):
                raise ValueError(f"Invalid role: {msg['role']}")
        return v


# ============================================================================
# Response Models
# ============================================================================

class SourceChunk(BaseModel):
    """근거 문서 정보."""
    
    content: str
    source: str
    score: float


class ChatResponse(BaseModel):
    """채팅 응답 스키마."""
    
    answer: str
    sources: List[SourceChunk]
    model: str
    usage: dict


class StreamChunk(BaseModel):
    """스트리밍 청크."""
    
    content: str
    done: bool = False


class StreamStartResponse(BaseModel):
    """스트리밍 시작 응답 (sources 포함)."""
    
    sources: List[SourceChunk]
    model: str
