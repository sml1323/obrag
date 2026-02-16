"""
Chat Router

RAG 기반 채팅 엔드포인트를 제공합니다.
"""

import json
from typing import AsyncGenerator

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse

from api.deps import get_rag_chain, get_session
from core.domain.chat import Session, Message, Topic
from core.rag import RAGChain
from core.llm import LLMFactory
from config.models import OpenAILLMConfig, GeminiLLMConfig, OllamaLLMConfig
from sqlmodel import Session as DBSession
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
            content=chunk.text,
            source=chunk.metadata.get("source", "unknown"),
            score=chunk.score,
            relative_path=chunk.metadata.get("relative_path"),
        )
        for chunk in retrieval_result.chunks
    ]


def _get_or_create_session(db: DBSession, session_id: str):
    session = db.get(Session, session_id)
    if not session:
        session = Session(id=session_id, title=f"Chat {session_id[:8]}")
        db.add(session)
        db.commit()
        db.refresh(session)
    return session


def _load_history(db: DBSession, session_id: str) -> list[dict]:
    session = db.get(Session, session_id)
    if not session:
        return []
    messages = sorted(session.messages, key=lambda m: m.created_at)
    return [{"role": m.role, "content": m.content} for m in messages]


def _save_message(db: DBSession, session_id: str, role: str, content: str):
    """세션에 메시지 저장."""
    msg = Message(session_id=session_id, role=role, content=content)
    db.add(msg)
    db.commit()


def _validate_api_key(provider: str, api_key: str | None) -> None:
    """API 키 유효성 검사."""
    if provider == "openai":
        if not api_key:
            raise HTTPException(
                status_code=400,
                detail="OpenAI API key is required. Please configure it in Settings.",
            )
        if not api_key.startswith("sk-"):
            raise HTTPException(
                status_code=400,
                detail="Invalid OpenAI API key format. API key must start with 'sk-'. Please update in Settings.",
            )
    elif provider == "gemini":
        if not api_key:
            raise HTTPException(
                status_code=400,
                detail="Gemini API key is required. Please configure it in Settings.",
            )


def _get_dynamic_chain(
    request: ChatRequest, default_chain: RAGChain, db: DBSession
) -> RAGChain:
    """요청에 따른 동적 체인 생성. DB settings fallback."""
    from core.domain.settings import Settings

    db_settings = db.get(Settings, 1)

    provider = request.llm_provider or (
        db_settings.llm_provider if db_settings else None
    )
    model = request.llm_model or (db_settings.llm_model if db_settings else None)
    api_key = request.api_key or (db_settings.llm_api_key if db_settings else None)

    if not provider:
        return default_chain

    _validate_api_key(provider, api_key)

    try:
        if provider == "openai":
            valid_models = [
                "gpt-4o",
                "gpt-4o-mini",
                "gpt-4-turbo",
                "gpt-5-mini",
                "gpt-5-nano",
            ]
            if model not in valid_models:
                model = "gpt-4o-mini"
            config = OpenAILLMConfig(model_name=model, api_key=api_key)
        elif provider == "gemini":
            valid_models = ["gemini-1.5-pro", "gemini-1.5-flash"]
            if model not in valid_models:
                model = "gemini-1.5-flash"
            config = GeminiLLMConfig(
                model_name=model,
                api_key=api_key,
            )
        elif provider == "ollama":
            ollama_endpoint = (
                db_settings.ollama_endpoint if db_settings else "http://localhost:11434"
            )
            config = OllamaLLMConfig(
                model_name=model or "llama3",
                base_url=ollama_endpoint,
            )
        else:
            return default_chain

        llm = LLMFactory.create(config)
        return RAGChain(retriever=default_chain._retriever, llm=llm)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create LLM: {str(e)}")


# ============================================================================
# Endpoints
# ============================================================================


@router.post("", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    chain: RAGChain = Depends(get_rag_chain),
    db: DBSession = Depends(get_session),
) -> ChatResponse:
    """
    단일 질의 RAG 응답.

    동기 방식으로 전체 응답을 한 번에 반환합니다.
    """
    history = []

    # Dynamic Chain Selection
    active_chain = _get_dynamic_chain(request, chain, db)

    if request.session_id:
        _get_or_create_session(db, request.session_id)
        history = _load_history(db, request.session_id)
        _save_message(db, request.session_id, "user", request.question)

    if history:
        response = active_chain.query_with_history(
            request.question,
            history=history,
            top_k=request.top_k,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
        )
    else:
        response = active_chain.query(
            request.question,
            top_k=request.top_k,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
        )

    if request.session_id:
        _save_message(db, request.session_id, "assistant", response.answer)

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
    db: DBSession = Depends(get_session),
) -> StreamingResponse:
    """
    SSE 스트리밍 응답.

    Server-Sent Events 형식으로 실시간 응답을 스트리밍합니다.
    첫 번째 이벤트에서 sources 정보를, 이후 이벤트에서 응답 텍스트를 전송합니다.
    """
    history = []

    # Dynamic Chain Selection
    active_chain = _get_dynamic_chain(request, chain, db)

    if request.session_id:
        _get_or_create_session(db, request.session_id)
        history = _load_history(db, request.session_id)
        _save_message(db, request.session_id, "user", request.question)

    retrieval_result, generator = active_chain.stream_query(
        request.question,
        history=history if history else None,
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
            "model": active_chain._llm.model_name,
        }
        yield f"data: {json.dumps(start_data)}\n\n"

        full_content = []
        # 텍스트 청크 스트리밍
        for chunk in generator:
            full_content.append(chunk)
            chunk_data = {"type": "content", "content": chunk}
            yield f"data: {json.dumps(chunk_data)}\n\n"

        usage = getattr(active_chain._llm, "_last_stream_usage", None) or {}
        yield f"data: {json.dumps({'type': 'done', 'usage': usage})}\n\n"

        if request.session_id:
            _save_message(db, request.session_id, "assistant", "".join(full_content))

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
