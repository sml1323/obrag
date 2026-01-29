# Frontend 연동 API 구현 계획

> **Target Task**: Phase 2.5 - Frontend 연동 준비 (Frontend Integration Preparation)
> **Target Path**: `src/api/routers/session.py`

## 목표

Frontend 개발에 필요한 Session 및 Message 관련 조회/삭제 API를 구현합니다.
기존 Chat API는 대화 생성에 초점을 맞췄다면, 이번 작업은 저장된 대화 기록을 관리하고 조회하는 기능을 제공합니다.

---

## 기존 패턴 분석

- `src/api/routers/topic.py`: `GET`, `POST`, `DELETE` 패턴이 이미 구현되어 있음.
- `src/api/routers/session.py`: 현재 `POST` (생성), `PATCH` (수정), `POST .../messages` (메시지 추가)만 존재.
- `src/core/domain/chat.py`: SQLModel 기반 `Session`, `Message` 모델 정의됨.

---

## 제안하는 구조

### `src/api/routers/session.py`

기존 파일에 다음 엔드포인트를 추가합니다.

1.  **`GET /sessions`**
    - Query Parameter: `topic_id: Optional[int]`
    - 반환: `List[Session]` (기본적으로 최신순 정렬)
    - 역할: 전체 세션 목록 또는 특정 주제의 세션 목록 조회

2.  **`GET /sessions/{session_id}`**
    - 반환: `Session`
    - 역할: 세션 상세 정보 조회

3.  **`DELETE /sessions/{session_id}`**
    - 역할: 세션 삭제 (Cascade 설정에 따라 하위 메시지도 삭제되는지 확인 필요, 현재 SQLModel 정의상 DB 레벨 Cascade 없으면 수동 삭제 필요할 수 있음. _Note: SQLModel Relationship에 `sa_relationship_kwargs={"cascade": "all, delete"}` 추가 고려 혹은 수동 삭제 로직 추가_)
    - 일단 Service 로직에서 Message 먼저 삭제 후 Session 삭제하는 안전한 방식 적용.

4.  **`GET /sessions/{session_id}/messages`**
    - 반환: `List[Message]` (생성일 오름차순)
    - 역할: 채팅방 입장 시 이전 대화 내용 로드

---

## 파일별 상세 계획

### [MODIFY] `src/api/routers/session.py`

```python
# GET /sessions
@router.get("", response_model=List[ChatSession])
def read_sessions(
    topic_id: Optional[int] = None,
    offset: int = 0,
    limit: int = 100,
    session: Session = Depends(get_session)
):
    # query construction with topic_id filter
    # order by created_at desc
    pass

# GET /sessions/{session_id}
@router.get("/{session_id}", response_model=ChatSession)
def read_session(session_id: str, session: Session = Depends(get_session)):
    pass

# DELETE /sessions/{session_id}
@router.delete("/{session_id}")
def delete_session(session_id: str, session: Session = Depends(get_session)):
    # Delete associated messages first (if no DB cascade)
    # Delete session
    pass

# GET /sessions/{session_id}/messages
@router.get("/{session_id}/messages", response_model=List[Message])
def read_session_messages(session_id: str, session: Session = Depends(get_session)):
    # order by created_at asc
    pass
```

---

## Verification Plan

### Automated Tests

새로운 테스트 파일 `src/tasktests/phase2_5/test_session_api.py`를 생성하여 다음 시나리오 검증:

1.  **세션 목록 조회**: Topic ID 필터링 동작 여부, 정렬 순서.
2.  **세션 상세 조회**: 존재하지 않는 ID 요청 시 404.
3.  **세션 삭제**: 삭제 후 조회 시 404, 관련 메시지가 정리가 되었는지(DB 레벨 체크).
4.  **메시지 조회**: 순서(오름차순) 확인.

### Command

```bash
pytest src/tasktests/phase2_5/test_session_api.py -v
```

---

## 요약

| 구분          | 내용                                         |
| :------------ | :------------------------------------------- |
| **수정 파일** | `src/api/routers/session.py`                 |
| **생성 파일** | `src/tasktests/phase2_5/test_session_api.py` |
| **주요 기능** | 세션 목록/상세 조회, 삭제, 메시지 이력 조회  |
| **의존성**    | `sqlmodel`, `fastapi`                        |
