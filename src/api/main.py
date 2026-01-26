"""
FastAPI Application Entry Point

Lifespan 관리, CORS 설정, 라우터 등록을 담당합니다.
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .deps import AppState, init_app_state


# ============================================================================
# Lifespan
# ============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    앱 시작/종료 시 리소스 관리.

    Startup:
        - ChromaStore 초기화
        - Embedder 로드
        - LLM 클라이언트 준비
        - RAGChain 구성

    Shutdown:
        - 리소스 정리
    """
    # Startup
    app.state.deps = init_app_state()

    yield

    # Shutdown (필요시 정리 로직)
    app.state.deps = None


# ============================================================================
# App Factory
# ============================================================================

def create_app() -> FastAPI:
    """FastAPI 앱 팩토리."""

    app = FastAPI(
        title="Obsidian RAG API",
        description="Obsidian 노트 기반 RAG 채팅 API",
        version="0.1.0",
        lifespan=lifespan,
    )

    # CORS 설정
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # 개발 환경용, 프로덕션에서는 특정 origin만 허용
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Health check 엔드포인트
    @app.get("/health")
    async def health_check():
        return {"status": "healthy"}

    @app.get("/status")
    async def get_status():
        """앱 상태 및 DB 정보 반환."""
        deps = app.state.deps
        if deps and deps.chroma_store:
            return {
                "status": "ready",
                "db": deps.chroma_store.get_stats(),
            }
        return {"status": "initializing"}

    # 라우터 등록
    from .routers import chat
    app.include_router(chat.router)

    return app


# 앱 인스턴스 (uvicorn에서 직접 import용)
app = create_app()
