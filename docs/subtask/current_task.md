# Sync & Health Endpoints 구현 계획

> **Target Task**: Phase 2 - FastAPI 백엔드 > Sync & Health Endpoints
> **Target Path**: `src/api/routers/`

## 목표

- **증분 동기화 API**: 클라이언트 요청으로 파일 변경 사항을 감지하고 Vector DB에 반영하는 `/sync/trigger` 엔드포인트 구현
- **상태 모니터링**: 서버 상태와 DB 정보를 확인할 수 있는 `/health`, `/status` 엔드포인트 구현
- **의존성 주입**: `IncrementalSyncer`를 API 계층에서 사용할 수 있도록 `AppState`에 통합

---

## 기존 패턴 분석

- **Router**: `src/api/routers/chat.py`와 같이 기능별 Router 분리 (`APIRouter` 사용)
- **Dependency**: `src/api/deps.py`의 `AppState`를 통해 Singleton 객체(`ChromaStore`, `RAGChain`) 관리
- **Sync Logic**: `src/core/sync/incremental_syncer.py`에 이미 구현되어 있으며 `create_syncer` 헬퍼 함수 존재

---

## 제안하는 구조

### App State 확장 (`src/api/deps.py`)

- `AppState`에 `syncer: IncrementalSyncer` 필드 추가
- `init_app_state`에서 `OBSIDIAN_PATH` 환경변수를 읽어 `create_syncer`로 초기화
- `get_syncer` 의존성 함수 추가

### New Routers

#### [NEW] `src/api/routers/sync.py`

- `POST /sync/trigger`
  - 동기적 작업이므로 `run_in_threadpool` 또는 일반 `def` 라우터로 정의 (FastAPI가 스레드풀에서 실행)
  - `IncrementalSyncer.sync()` 호출
  - 결과로 `SyncResult` 반환

#### [NEW] `src/api/routers/health.py`

- `GET /health`
  - 단순 200 OK 반환 (Liveness Probe용)
- `GET /status`
  - DB 상태(문서 수 등)와 마지막 동기화 시간 등 반환

### Router Registration (`src/api/main.py`)

- `sync`, `health` 라우터 등록

---

## 파일별 상세 계획

### 1. `src/api/deps.py` [MODIFY]

```python
# .env 로드 부분에 OBSIDIAN_PATH 추가
# AppState 클래스에 syncer 필드 추가
@dataclass
class AppState:
    ...
    syncer: IncrementalSyncer

# init_app_state 함수 수정
def init_app_state(...) -> AppState:
    ...
    # 5. IncrementalSyncer 생성
    obsidian_path = os.getenv("OBSIDIAN_PATH", "./docs") # 기본값 설정
    syncer = create_syncer(root_path=obsidian_path, chroma_store=chroma_store)

    return AppState(..., syncer=syncer)

# get_syncer 함수 추가
def get_syncer(request: Request) -> IncrementalSyncer:
    return request.app.state.deps.syncer
```

### 2. `src/api/routers/sync.py` [NEW]

```python
from fastapi import APIRouter, Depends
from api.deps import get_sync_registry, get_syncer # Registry는 필요시 추가
from core.sync.incremental_syncer import IncrementalSyncer, SyncResult

router = APIRouter(prefix="/sync", tags=["sync"])

@router.post("/trigger", response_model=SyncResult)
def trigger_sync(syncer: IncrementalSyncer = Depends(get_syncer)):
    """증분 동기화 트리거"""
    return syncer.sync()
```

### 3. `src/api/routers/health.py` [NEW]

```python
from fastapi import APIRouter, Depends
from api.deps import get_chroma_store
from db.chroma_store import ChromaStore

router = APIRouter(tags=["health"])

@router.get("/health")
async def health_check():
    return {"status": "healthy"}

@router.get("/status")
async def get_status(store: ChromaStore = Depends(get_chroma_store)):
    # ChromaStore 구현에 따라 get_stats() 활용 (main.py의 기존 로직 이동)
    return {
        "status": "ready",
        "db": store.get_stats(),
    }
```

### 4. `src/api/main.py` [MODIFY]

- 기존 `@app.get("/health")`, `@app.get("/status")` 제거 (health 라우터로 이동)
- `app.include_router(sync.router)`
- `app.include_router(health.router)`

### 5. `src/tasktests/phase2/test_api_sync.py` [NEW]

- `/sync/trigger` 호출 테스트
- `Mock(IncrementalSyncer)`를 주입하여 실제 파일 스캔 없이 동작 확인
- `/health`, `/status` 응답 확인

---

## Verification Plan

### Automated Tests

1. **단위 테스트 실행**:
   ```bash
   pytest src/tasktests/phase2/test_api_sync.py -v
   ```

### Manual Verification

1. **서버 실행**: `uvicorn src.api.main:app --reload`
2. **Docs 확인**: `http://localhost:8000/docs` 접속
3. **Sync Trigger**: Swagger UI에서 `/sync/trigger` 실행 후 결과 확인

---

## 요약

| 구분              | 내용                                                                                            |
| ----------------- | ----------------------------------------------------------------------------------------------- |
| **New Files**     | `src/api/routers/sync.py`, `src/api/routers/health.py`, `src/tasktests/phase2/test_api_sync.py` |
| **Modified**      | `src/api/deps.py`, `src/api/main.py`                                                            |
| **Dependencies**  | `IncrementalSyncer` (Core)                                                                      |
| **Test Coverage** | API Endpoint Mock Test                                                                          |
