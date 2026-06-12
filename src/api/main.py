"""
FastAPI Application Entry Point

Lifespan 관리, CORS 설정, 라우터 등록을 담당합니다.
"""

import os
import secrets
from contextlib import asynccontextmanager
from importlib import import_module
from typing import AsyncGenerator

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from .deps import init_app_state


# 토큰 인증을 적용하지 않는 공개 경로 (헬스체크 / API 문서)
_PUBLIC_PATHS = {"/health", "/openapi.json", "/docs", "/redoc"}


def _is_public_path(path: str) -> bool:
    # "/docs" 자체와 "/docs/..." 만 공개. "/docsEVIL" 같은 과대매칭 방지.
    return path in _PUBLIC_PATHS or path == "/docs" or path.startswith("/docs/")


async def _token_auth_dispatch(request: Request, call_next):
    """
    선택적 Bearer 토큰 인증.

    OBRAG_API_TOKEN 환경변수가 설정된 경우에만 토큰을 요구한다(기본 OFF → 동작 변화 없음).
    CORS preflight(OPTIONS)와 공개 경로는 항상 통과. 비교는 상수시간(secrets).
    """
    token = os.getenv("OBRAG_API_TOKEN")
    if token and request.method != "OPTIONS" and not _is_public_path(request.url.path):
        provided = request.headers.get("Authorization", "")
        if not secrets.compare_digest(provided, f"Bearer {token}"):
            return JSONResponse(status_code=401, content={"detail": "Unauthorized"})
    return await call_next(request)


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

    # 미들웨어 등록 순서 주의: 나중에 추가한 것이 더 바깥쪽(요청 시 먼저 실행).
    # 인증을 먼저 등록하고 CORS 를 나중에 등록해 CORS 를 최외곽으로 둔다.
    # → preflight(OPTIONS)는 CORS 가 처리해 인증에 닿지 않고,
    #   인증이 반환하는 401 응답에도 CORS 헤더가 정상 부착된다.
    app.add_middleware(BaseHTTPMiddleware, dispatch=_token_auth_dispatch)

    # CORS 설정 (최외곽)
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
