# Phase 3 Frontend Integration Plan

> **Target Task**: Phase 3 - Frontend UI (Dashboard)
> **Target Path**: `src/core`, `src/api`, `front/lib`, `front/app`

## 목표

Backend의 `Project` API와 Frontend의 `ParaDashboard`를 연동하여 실제 데이터를 대시보드에 표시합니다.
이를 위해 Backend 모델에 `progress`, `file_count` 필드를 추가하고, Frontend에는 API Client 및 Data Hook을 구현합니다.

---

## 기존 패턴 분석

- **Backend Model**: `SQLModel` 기반의 `Project` 엔티티 (`src/core/domain/project.py`).
- **Scanner**: `src/core/project/scanner.py`에서 폴더를 스캔하여 메타데이터 업데이트.
- **Frontend**: Next.js App Router, `useState` + `localStorage`로 Mock Data 관리 중.
- **API Communication**: `front/lib`에 API 클라이언트 부재.

---

## 제안하는 구조

### Backend Changes

1.  **`src/core/domain/project.py`**:
    - `progress`: int (0-100, default 0) 필드 추가.
    - `file_count`: int (default 0) 필드 추가.
2.  **`src/api/schemas/project.py`**:
    - `ProjectRead`에 `progress`, `file_count` 추가.
    - `ProjectUpdate`에 `progress` 추가 (사용자가 슬라이더로 업데이트 가능).
3.  **`src/core/project/scanner.py`**:
    - 스캔 시 `scanned_files`의 개수를 `project.file_count`에 업데이트하는 로직 추가.

### Frontend Changes

1.  **`front/lib/api.ts`** (New):
    - `fetch` wrapper 또는 `axios` 인스턴스 생성.
    - Backend API 호출 함수 (`fetchProjects`, `updateProjectProgress`) 구현.
2.  **`front/hooks/use-projects.ts`** (New):
    - `SWR` 또는 `React Query` (없으면 `useEffect` 기반 커스텀 훅) 사용하여 프로젝트 목록 상태 관리.
3.  **`front/app/page.tsx`**:
    - `useState` Mock Data 로직 제거.
    - `useProjects` 훅 연동.
    - `handleUpdateParaProgress`를 API 호출로 변경.

> Note: Frontend `ParaProject` 인터페이스의 `files` 필드는 현재 Backend에서 제공하지 않으므로 당분간 빈 배열(`[]`)로 처리합니다.

---

## 파일별 상세 계획

### 1. `src/core/domain/project.py`

```python
class Project(SQLModel, table=True):
    # ... existing fields ...
    progress: int = Field(default=0, description="Project progress (0-100)")
    file_count: int = Field(default=0, description="Number of markdown files in the project")
```

### 2. `src/core/project/scanner.py`

```python
def scan_project(self, project: Project) -> bool:
    # ... existing logic ...
    scanner = FolderScanner(...)
    scanned_files = scanner.scan()

    # Update file count
    if project.file_count != len(scanned_files):
        project.file_count = len(scanned_files)
        updated = True

    # ... mtime update logic ...
```

### 3. `front/lib/api-client.ts`

```typescript
// Simple fetch wrapper
const API_BASE = "http://localhost:8000/api"; // or configured env

export async function getProjects(): Promise<Project[]> {
  const res = await fetch(`${API_BASE}/projects`);
  if (!res.ok) throw new Error("Failed to fetch projects");
  return res.json();
}

export async function updateProjectProgress(
  id: string,
  progress: number,
): Promise<Project> {
  const res = await fetch(`${API_BASE}/projects/${id}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ progress }),
  });
  return res.json();
}
```

### 4. `front/app/page.tsx`

Refactor to use async data fetching.

---

## Verification Plan

### Automated Tests

1.  **Backend Unit Tests**:
    - `src/tasktests/phase3/test_project_model.py`: `progress`, `file_count` 필드 동작 확인.
    - `src/tasktests/phase3/test_project_scanner.py`: 스캔 후 `file_count`가 정확한지 확인.
    - `src/tasktests/phase3/test_project_api.py`: `PATCH /projects/{id}`로 `progress` 업데이트 확인.

### Manual Verification

1.  Backend 서버 실행 (`poetry run python -m src.api.main`).
2.  Frontend 실행 (`npm run dev` in `front/`).
3.  대시보드 접속.
4.  실제 DB에 있는 프로젝트가 카드로 표시되는지 확인.
    - `file_count`가 맞게 나오는지 확인.
    - Progress 슬라이더 조절 시 DB에 반영되는지 확인 (새로고침 후 유지).

---

## 요약

| File                          | Changes                            |
| :---------------------------- | :--------------------------------- |
| `src/core/domain/project.py`  | `progress`, `file_count` 필드 추가 |
| `src/api/schemas/project.py`  | Schema 업데이트                    |
| `src/core/project/scanner.py` | `file_count` 업데이트 로직 추가    |
| `front/lib/api-client.ts`     | [NEW] API 클라이언트 구현          |
| `front/app/page.tsx`          | Mock Data 제거 및 실제 API 연동    |
