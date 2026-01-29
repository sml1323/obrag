# Project API & Business Logic 구현 계획

> **Target Task**: Phase 3 - Project Dashboard > API & Business Logic
> **Target Path**: `src/api/routers/project.py`

## 목표

- 사용자가 프로젝트를 등록/관리할 수 있는 CRUD API 구현
- 프로젝트의 '유기(Stale)' 상태를 판별하는 비즈니스 로직 구현 (30일 미수정 기준)
- **Refinement**: 프로젝트 변경 감지(`Scanner`) 대상을 `.md` 파일로 한정하여 정확한 "지식 활동" 추적
- API 응답 시 계산된 메타데이터(`is_stale`, `days_since_modification`) 포함

---

## 기존 패턴 분석

- **Router 패턴**: `src/api/routers/` 내에 도메인별 라우터 분리 (`chat.py`, `session.py` 등)
- **DTO 패턴**: `SQLModel`을 `Response_model`로 직접 사용하거나, 별도 Pydantic 모델로 분리 (`SessionUpdate` 등)
- **Dependency Injection**: `SessionDep`을 통해 DB 세션 주입
- **Scanner**: `ProjectScanner`가 이미 구현되어 있으나, 모든 파일(`*`)을 스캔하도록 설정되어 있어 수정 필요

---

## 제안하는 구조

### 1. Schema 정의 (`src/api/schemas/project.py`) [NEW]

- `ProjectCreate`: 프로젝트 등록 요청 (path, name)
- `ProjectUpdate`: 프로젝트 정보 수정 (name, description, is_active)
- `ProjectRead`: API 응답용 스키마. `Project` 모델 상속 + Computed Fields (`is_stale`, `days_inactive`)

### 2. Scanner Refinement (`src/core/project/scanner.py`) [MODIFY]

- **변경**: `extensions=["*"]` → `extensions=[".md"]`
- **이유**: 사용자가 "MD 파일 수정 일자 기준"을 기대함. 불필요한 시스템 파일(.DS_Store 등) 변경으로 인한 날짜 갱신 방지.

### 3. Business Logic (`src/core/project/status.py`) [NEW]

- `ProjectStatusCalculator`: `last_modified_at`을 기준으로 Stale 여부 및 경과 일수 계산 로직 캡슐화

### 4. API Router (`src/api/routers/project.py`) [NEW]

- `POST /projects`: 프로젝트 등록 (폴더 경로 검증 포함)
- `GET /projects`: 프로젝트 목록 조회 (Active/All 필터, Stale 필터)
- `GET /projects/{id}`: 상세 조회 (Computed Status 포함)
- `PATCH /projects/{id}`: 정보 수정 (Active/Archive 토글)
- `DELETE /projects/{id}`: 삭제

---

## 파일별 상세 계획

### `src/core/project/scanner.py` [Refinement]

```python
# Before
scanner = FolderScanner(root_path=project_path, extensions=["*"])

# After
scanner = FolderScanner(root_path=project_path, extensions=[".md"])
```

### `src/api/schemas/project.py`

```python
class ProjectRead(Project):
    is_stale: bool
    days_inactive: int
```

### `src/core/project/status.py`

```python
class ProjectStatus:
    @staticmethod
    def calculate_staleness(project: Project) -> tuple[bool, int]:
        # last_modified_at 기준 30일 경과 확인
        # return (is_stale, days_inactive)
        pass
```

### `src/api/routers/project.py`

```python
@router.post("/", response_model=ProjectRead)
def create_project(project_in: ProjectCreate, session: SessionDep):
    # 경로 유효성 검사 (Scanner 활용 가능?)
    pass

@router.get("/", response_model=list[ProjectRead])
def list_projects(
    session: SessionDep,
    stale_only: bool = False
):
    pass
```

---

## Verification Plan

### Automated Tests (`src/tasktests/phase3/test_project_api.py`)

- **Scanner Test**: `.md` 파일만 수정했을 때 `last_modified_at` 갱신, `.txt` 수정 시 갱신 안됨 확인
- **Stale Logic Test**: 과거 날짜(`last_modified_at`)를 가진 프로젝트 생성 후 `is_stale`=True 확인
- **CRUD Test**: 생성 -> 목록 조회 -> 수정 -> 삭제 흐름 검증

---

## 요약

| 구분        | 파일 경로                                  | 비고        |
| ----------- | ------------------------------------------ | ----------- |
| **Schema**  | `src/api/schemas/project.py`               | [NEW]       |
| **Scanner** | `src/core/project/scanner.py`              | [MODIFY]    |
| **Logic**   | `src/core/project/status.py`               | [NEW]       |
| **Router**  | `src/api/routers/project.py`               | [NEW]       |
| **Main**    | `src/api/main.py`                          | Router 등록 |
| **Test**    | `src/tasktests/phase3/test_project_api.py` | [NEW]       |
