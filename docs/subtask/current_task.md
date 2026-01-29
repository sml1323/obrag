# [Project Data Layer] 구현 계획 (Revised)

> **Target Task**: Phase 3 - Project Data Layer (Project 테이블 Schema 정의 및 CRUD)
> **Target Path**: `src/core/domain/project.py`

## 목표

사용자가 Vault 내의 특정 폴더를 "프로젝트"로 지정하여 관리할 수 있도록, `Project` 엔티티의 스키마를 정의하고 CRUD를 구현합니다.
초기 기획(`Project/` 폴더 자동 스캔)에서 **"사용자가 원하는 폴더를 프로젝트로 등록(Selection)"**하는 방식으로 변경되었습니다.

---

## 기존 패턴 분석

- `src/core/domain/chat.py`: SQLModel 기반 기본 엔티티 정의 (`id`, `created_at` 등 공통 패턴).
- 프로젝트는 파일 시스템의 폴더와 1:1로 매핑되는 개념.
- **변경 사항**: 특정 루트 폴더(`Project/`)를 강제하지 않고, `path`를 Unique Key로 하여 임의의 깊이에 있는 폴더도 프로젝트로 승격 가능해야 함.

---

## 제안하는 구조

### `src/core/domain/project.py`

DB 스키마는 "등록된 프로젝트" 정보를 저장합니다.

```python
from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime

class Project(SQLModel, table=True):
    # 기본 식별자
    id: Optional[int] = Field(default=None, primary_key=True)

    # 프로젝트 정의
    name: str = Field(index=True)           # 표시 이름 (기본값: 폴더명, 사용자 변경 가능)
    path: str = Field(unique=True, index=True) # Vault 내 상대 경로 (예: "Study/CS101")
    description: Optional[str] = None       # 프로젝트 설명

    # 관리 상태
    is_active: bool = Field(default=True)   # 보관(Archive) 여부

    # 메타데이터 (Dashboard Stale 감지용)
    last_modified_at: datetime = Field(default_factory=datetime.utcnow) # 폴더 내 파일 최신 수정일
    created_at: datetime = Field(default_factory=datetime.utcnow)       # 프로젝트 등록일
```

### CRUD 로직 (`src/api/routers/project.py` 예정)

이번 Task는 **Data Layer(Model)**에 집중하되, 추후 API에서 다음 기능이 필요함을 인지합니다:

1. `POST /projects`: 특정 `path`를 프로젝트로 등록.
2. `GET /projects`: 등록된 프로젝트 목록 조회.

---

## 파일별 상세 계획

### [NEW] `src/core/domain/project.py`

- 위 스키마 정의 구현.

### [NEW] `src/tasktests/phase3/test_project_model.py`

- 프로젝트 모델 생성, 조회, 중복 `path` 방지 제약조건 테스트.

---

## Verification Plan

### Automated Tests

`pytest src/tasktests/phase3/test_project_model.py`

1. **Project Registration**: `path="Archive/ProjectA"` 등으로 생성 테스트.
2. **Uniqueness**: 동일 `path` 등록 시 `IntegrityError` 발생 확인.
3. **Optional Fields**: `description` 등 선택 필드 동작 확인.

---

## 요약

| 구분          | 내용                                                                       |
| :------------ | :------------------------------------------------------------------------- |
| **생성 파일** | `src/core/domain/project.py`, `src/tasktests/phase3/test_project_model.py` |
| **주요 변경** | `Project/` 루트 고정 해제 → 임의 폴더 등록 지원 (`path` 중심)              |
| **의존성**    | `sqlmodel`                                                                 |
