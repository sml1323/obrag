# FastAPI App Foundation 구현 계획

> **Target Task**: Phase 2 - FastAPI 백엔드 > App Foundation
> **Target Path**: `src/api/`

## 목표

FastAPI 애플리케이션의 기초를 구축합니다:

- **Lifespan 관리**: 앱 시작/종료 시 리소스(ChromaStore, LLM) 초기화/정리
- **의존성 주입(DI)**: RAGChain, ChromaStore 등 핵심 객체를 엔드포인트에 주입
- **CORS 설정**: 프론트엔드(React) 연동을 위한 Cross-Origin 허용

---

## 기존 패턴 분석

### 1. LLMFactory 패턴 (`src/core/llm/factory.py`)

- Config 기반 인스턴스 생성
- `create()` 정적 메서드로 의존성 생성
- `create_fake()` 로 테스트용 Mock 지원

### 2. RAGChain Composition (`src/core/rag/chain.py`)

- Retriever + LLMStrategy를 외부에서 주입받음
- 명확한 책임 분리 패턴

### 3. ChromaStore (`src/db/chroma_store.py`)

- `persist_path`, `collection_name`, `embedder`를 생성자로 받음
- 상태 확인용 `get_stats()` 메서드 제공

---

## 제안하는 구조

```
src/api/
├── __init__.py       # [NEW] 모듈 export
├── main.py           # [NEW] FastAPI 앱, Lifespan, CORS
└── deps.py           # [NEW] 의존성 주입 함수
```

---

## 파일별 상세 계획

### 1. `src/api/main.py` [NEW]

```python
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

    return app


# 앱 인스턴스 (uvicorn에서 직접 import용)
app = create_app()
```

### 2. `src/api/deps.py` [NEW]

```python
"""
Dependency Injection Module

FastAPI 엔드포인트에 주입할 의존성을 정의합니다.
"""

from dataclasses import dataclass
from typing import Optional
from pathlib import Path
import os

from dotenv import load_dotenv

# .env 파일 로드 (src/.env)
_env_path = Path(__file__).parent.parent / ".env"
load_dotenv(_env_path)

from fastapi import Request
from core.rag import RAGChain, Retriever
from core.llm import LLMFactory
from core.embedding import EmbedderFactory
from db.chroma_store import ChromaStore
from config.models import OpenAILLMConfig, OpenAIEmbeddingConfig


# ============================================================================
# App State
# ============================================================================

@dataclass
class AppState:
    """앱 전역 상태 (Lifespan에서 초기화)."""

    chroma_store: ChromaStore
    rag_chain: RAGChain


def init_app_state(
    chroma_path: str = "./chroma_db",
    collection_name: str = "obsidian_notes",
) -> AppState:
    """
    앱 상태 초기화.

    환경변수에서 설정을 읽고 필요한 객체들을 생성합니다.

    Args:
        chroma_path: ChromaDB 저장 경로
        collection_name: 컬렉션 이름

    Returns:
        초기화된 AppState
    """
    # 1. Embedder 생성
    embed_config = OpenAIEmbeddingConfig(
        model_name=os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
    )
    embedder = EmbedderFactory.create(embed_config)

    # 2. ChromaStore 생성
    chroma_store = ChromaStore(
        persist_path=chroma_path,
        collection_name=collection_name,
        embedder=embedder,
    )

    # 3. LLM 생성
    llm_config = OpenAILLMConfig(
        model_name=os.getenv("LLM_MODEL", "gpt-4o-mini")
    )
    llm = LLMFactory.create(llm_config)

    # 4. Retriever + RAGChain 생성
    retriever = Retriever(chroma_store)
    rag_chain = RAGChain(retriever=retriever, llm=llm)

    return AppState(
        chroma_store=chroma_store,
        rag_chain=rag_chain,
    )


# ============================================================================
# Dependency Functions
# ============================================================================

def get_app_state(request: Request) -> AppState:
    """요청에서 앱 상태 가져오기."""
    return request.app.state.deps


def get_rag_chain(request: Request) -> RAGChain:
    """RAGChain 의존성 주입."""
    return request.app.state.deps.rag_chain


def get_chroma_store(request: Request) -> ChromaStore:
    """ChromaStore 의존성 주입."""
    return request.app.state.deps.chroma_store
```

### 3. `src/api/__init__.py` [NEW]

```python
"""
API Module

FastAPI 애플리케이션 및 의존성 export.
"""

from .main import app, create_app
from .deps import AppState, get_app_state, get_rag_chain, get_chroma_store
```

### 4. `src/tasktests/phase2/test_api_foundation.py` [NEW]

```python
"""FastAPI App Foundation 테스트"""

import pytest
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from fastapi.testclient import TestClient


class TestAppCreation:
    """앱 생성 테스트"""

    def test_create_app_returns_fastapi_instance(self):
        """create_app()이 FastAPI 인스턴스를 반환하는지 확인"""
        from api.main import create_app
        from fastapi import FastAPI

        app = create_app()
        assert isinstance(app, FastAPI)

    def test_app_has_cors_middleware(self):
        """CORS 미들웨어가 설정되었는지 확인"""
        from api.main import create_app

        app = create_app()
        middleware_names = [m.cls.__name__ for m in app.user_middleware]
        assert "CORSMiddleware" in middleware_names


class TestHealthEndpoint:
    """헬스체크 엔드포인트 테스트"""

    @pytest.fixture
    def client(self):
        from api.main import create_app
        app = create_app()
        # Lifespan을 건너뛰고 테스트용 상태 설정
        return TestClient(app, raise_server_exceptions=False)

    def test_health_returns_200(self, client):
        """GET /health가 200을 반환하는지 확인"""
        response = client.get("/health")
        assert response.status_code == 200

    def test_health_returns_healthy_status(self, client):
        """GET /health가 healthy 상태를 반환하는지 확인"""
        response = client.get("/health")
        assert response.json() == {"status": "healthy"}


class TestAppState:
    """AppState 테스트"""

    def test_app_state_dataclass(self):
        """AppState가 올바른 필드를 가지는지 확인"""
        from api.deps import AppState
        import dataclasses

        assert dataclasses.is_dataclass(AppState)
        fields = {f.name for f in dataclasses.fields(AppState)}
        assert "chroma_store" in fields
        assert "rag_chain" in fields


class TestDependencyFunctions:
    """의존성 주입 함수 테스트"""

    def test_get_rag_chain_exists(self):
        """get_rag_chain 함수가 존재하는지 확인"""
        from api.deps import get_rag_chain
        assert callable(get_rag_chain)

    def test_get_chroma_store_exists(self):
        """get_chroma_store 함수가 존재하는지 확인"""
        from api.deps import get_chroma_store
        assert callable(get_chroma_store)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
```

---

## Verification Plan

### Automated Tests

1. **단위 테스트 실행**

   ```bash
   uv run pytest src/tasktests/phase2/test_api_foundation.py -v
   ```

2. **임포트 확인**

   ```bash
   uv run python -c "from src.api import app, create_app; print('Import OK')"
   ```

3. **전체 Phase 2 테스트** (기존 테스트와의 호환성 확인)
   ```bash
   uv run pytest src/tasktests/phase2/ -v
   ```

### Manual Verification

4. **로컬 서버 실행** (OPENAI_API_KEY 필요)
   ```bash
   cd src && uv run uvicorn api.main:app --reload --port 8000
   ```
5. **헬스체크 확인**
   ```bash
   curl http://localhost:8000/health
   # 예상 응답: {"status":"healthy"}
   ```

---

## 요약

| 항목            | 내용                                                        |
| --------------- | ----------------------------------------------------------- |
| **신규 파일**   | `src/api/main.py`, `src/api/deps.py`, `src/api/__init__.py` |
| **테스트 파일** | `src/tasktests/phase2/test_api_foundation.py`               |
| **핵심 클래스** | `AppState`                                                  |
| **핵심 함수**   | `create_app()`, `init_app_state()`, `lifespan()`            |
| **의존성 함수** | `get_rag_chain()`, `get_chroma_store()`, `get_app_state()`  |
| **엔드포인트**  | `GET /health`, `GET /status`                                |
