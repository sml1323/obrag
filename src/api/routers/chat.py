"""
Chat Router

RAG 기반 채팅 엔드포인트를 제공합니다.
"""

import json
from typing import AsyncGenerator

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from api.deps import get_rag_chain
from core.rag import RAGChain
from dtypes.api import (
    ChatRequest,
    ChatHistoryRequest,
    ChatResponse,
    SourceChunk,
)


router = APIRouter(prefix="/chat", tags=["chat"])


# ============================================================================
# Helper Functions
# ============================================================================

def _convert_retrieval_to_sources(retrieval_result) -> list[SourceChunk]:
    """RetrievalResult를 SourceChunk 리스트로 변환."""
    return [
        SourceChunk(
            content=chunk.content,
            source=chunk.metadata.get("source", "unknown"),
            score=chunk.score,
        )
        for chunk in retrieval_result.chunks
    ]


# ============================================================================
# Endpoints
# ============================================================================

@router.post("", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    chain: RAGChain = Depends(get_rag_chain),
) -> ChatResponse:
    """
    단일 질의 RAG 응답.
    
    동기 방식으로 전체 응답을 한 번에 반환합니다.
    """
    response = chain.query(
        request.question,
        top_k=request.top_k,
        temperature=request.temperature,
        max_tokens=request.max_tokens,
    )
    
    return ChatResponse(
        answer=response.answer,
        sources=_convert_retrieval_to_sources(response.retrieval_result),
        model=response.model,
        usage=response.usage,
    )


@router.post("/stream")
async def chat_stream(
    request: ChatRequest,
    chain: RAGChain = Depends(get_rag_chain),
) -> StreamingResponse:
    """
    SSE 스트리밍 응답.
    
    Server-Sent Events 형식으로 실시간 응답을 스트리밍합니다.
    첫 번째 이벤트에서 sources 정보를, 이후 이벤트에서 응답 텍스트를 전송합니다.
    """
    retrieval_result, generator = chain.stream_query(
        request.question,
        top_k=request.top_k,
        temperature=request.temperature,
        max_tokens=request.max_tokens,
    )
    
    sources = _convert_retrieval_to_sources(retrieval_result)
    
    async def event_generator() -> AsyncGenerator[str, None]:
        # 첫 번째 이벤트: sources 정보
        start_data = {
            "type": "start",
            "sources": [s.model_dump() for s in sources],
            "model": chain._llm.model_name,
        }
        yield f"data: {json.dumps(start_data)}\n\n"
        
        # 텍스트 청크 스트리밍
        for chunk in generator:
            chunk_data = {"type": "content", "content": chunk}
            yield f"data: {json.dumps(chunk_data)}\n\n"
        
        # 완료 이벤트
        yield f"data: {json.dumps({'type': 'done'})}\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )


@router.post("/history", response_model=ChatResponse)
async def chat_with_history(
    request: ChatHistoryRequest,
    chain: RAGChain = Depends(get_rag_chain),
) -> ChatResponse:
    """
    대화 이력 포함 멀티턴.
    
    이전 대화 컨텍스트를 유지하며 응답합니다.
    """
    response = chain.query_with_history(
        request.question,
        history=request.history,
        top_k=request.top_k,
        temperature=request.temperature,
    )
    
    return ChatResponse(
        answer=response.answer,
        sources=_convert_retrieval_to_sources(response.retrieval_result),
        model=response.model,
        usage=response.usage,
    )
