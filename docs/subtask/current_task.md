# [Phase 2.5] 주제(Topic) 기반 대화 생성 및 이동(Move) 구현 계획

> **Target Task**: Phase 2.5 - 주제 내 대화 생성 및 기존 대화 이동(Move) 기능
> **Target Path**: `src/api`, `src/dtypes`

## 목표

- 대화 세션 생성 시 특정 주제(`topic_id`)를 지정할 수 있도록 지원
- 기존 대화 세션을 다른 주제로 이동하거나, 주제에서 제거하는 기능(Move) 구현
- 잘못된 `topic_id`에 대한 유효성 검사 추가

---

## 기존 패턴 분석

- **Domain Model**: `core.domain.chat.Session` 모델은 이미 `topic_id` 필드를 가지고 있음.
- **API Pattern**: `src/api/routers/session.py`는 `Session` 객체를 직접 받아 생성하지만, `topic_id` 유효성 검증 로직은 부재함.
- **DTO**: `src/dtypes/api.py`에는 `ChatRequest` 등 요청 모델이 있으나, Session Update를 위한 모델은 없음.

---

## 제안하는 구조

### 1. DTO 추가 (`src/dtypes/api.py`)

- `SessionUpdate` 클래스 추가 (Pydantic BaseModel)
  - `topic_id`: `Optional[int]` (Nullable 허용하여 주제 해제 지원)
  - `title`: `Optional[str]` (제목 변경도 같이 지원하면 유용함)

### 2. API 엔드포인트 확장 (`src/api/routers/session.py`)

- **Move (Update)**: `PATCH /sessions/{session_id}`
  - `SessionUpdate` 스키마 사용
  - `topic_id` 변경 시 해당 Topic 존재 여부 검증 (FK 오류 방지)
- **Create**: `POST /sessions` (기존 수정)
  - `topic_id`가 입력된 경우, 해당 Topic 존재 여부 사전 검증 추가

---

## 파일별 상세 계획

### `src/dtypes/api.py`

```python
class SessionUpdate(BaseModel):
    """세션 정보 수정 요청 (이동 포함)."""
    title: Optional[str] = Field(default=None, description="세션 제목 변경")
    topic_id: Optional[int] = Field(default=None, description="이동할 주제 ID (None이면 주제 없음)")
```

### `src/api/routers/session.py`

1. **`create_session` 수정**:

   ```python
   def create_session(..., session: Session = Depends(get_session)):
       if chat_session.topic_id is not None:
           # Topic 존재 확인
           # ...
       # ...
   ```

2. **`update_session` 추가**:
   ```python
   @router.patch("/{session_id}", response_model=ChatSession)
   def update_session(session_id: str, update_data: SessionUpdate, session: Session = Depends(get_session)):
       # 1. Session 조회
       # 2. Topic 존재 확인 (update_data.topic_id가 있는 경우)
       # 3. 업데이트 수행 (sqlmodel update)
       # ...
   ```

---

## Verification Plan

### Automated Tests

새로운 테스트 파일 `src/tasktests/phase2_5/test_chat_topic_move.py` 생성하여 다음 시나리오 검증:

1. **Create with Topic**: 존재하는 `topic_id`로 세션 생성 성공 확인
2. **Create with Invalid Topic**: 존재하지 않는 `topic_id`로 생성 시 404 에러 확인
3. **Move to Topic**: 기존 세션을 특정 Topic으로 이동 확인 (`topic_id` 업데이트)
4. **Remove from Topic**: Topic에 속한 세션을 Topic 없음 상태로 이동 확인
5. **Move to Invalid**: 존재하지 않는 Topic으로 이동 시도 시 404 에러 확인

**Run Verification:**

```bash
python -m pytest src/tasktests/phase2_5/test_chat_topic_move.py -v
```

---

## 요약

| 구분             | 내용                                             |
| :--------------- | :----------------------------------------------- |
| **New DTO**      | `SessionUpdate` (`src/dtypes/api.py`)            |
| **Modified API** | `POST /sessions` (Validation check)              |
| **New API**      | `PATCH /sessions/{id}` (Move logic)              |
| **New Test**     | `src/tasktests/phase2_5/test_chat_topic_move.py` |
