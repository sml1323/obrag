"""
FastAPI Application Entry Point

Lifespan 관리, CORS 설정, 라우터 등록을 담당합니다.
"""

from contextlib import asynccontextmanager
from importlib import import_module
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .deps import init_app_state


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
    engine_module = import_module("db.engine")
    engine_module.create_db_and_tables()
    app.state.deps = init_app_state()

    # Auto-configure vault_path from env var (Docker support)
    import os
    vault_path_env = os.getenv("VAULT_PATH")
    if vault_path_env:
        from sqlmodel import Session as DBSession
        from core.domain.settings import Settings
        engine = engine_module.engine
        with DBSession(engine) as session:
            settings = session.get(Settings, 1)
            if not settings:
                settings = Settings(id=1, vault_path=vault_path_env)
                session.add(settings)
            elif settings.vault_path != vault_path_env:
                settings.vault_path = vault_path_env
                session.add(settings)
            session.commit()
        print(f"[init] vault_path auto-configured: {vault_path_env}")

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
        allow_origins=[
            "http://localhost:3000",
            "http://frontend:3000",
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 라우터 등록
    from .routers import (
        chat,
        embedding,
        health,
        para,
        project,
        session,
        settings,
        sync,
        topic,
        vault,
    )

    app.include_router(chat.router)
    app.include_router(embedding.router)
    app.include_router(health.router)
    app.include_router(para.router)
    app.include_router(project.router)
    app.include_router(session.router)
    app.include_router(settings.router)
    app.include_router(sync.router)
    app.include_router(topic.router)
    app.include_router(vault.router)

    return app


# 앱 인스턴스 (uvicorn에서 직접 import용)
app = create_app()
