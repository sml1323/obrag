# [Chat Persistence] 구현 계획

> **Target Task**: Phase 2.5 - Chat Persistence Integration
> **Target Path**: `src/api/routers/chat.py`

## 목표

- **Chat API 연동**: `POST /chat` 및 `POST /chat/stream` 호출 시 대화 내용을 SQLite DB에 자동 저장합니다.
- **Context Awareness**: `session_id`를 통해 이전 대화 내용을 로드하여 멀티턴 대화를 지원합니다.

---

## 기존 패턴 분석

- **Type Collision**: `core.llm.strategy.Message`(dict)와 `core.domain.chat.Message`(SQLModel)의 이름 충돌 주의 필요. DB 저장 시에는 SQLModel을, LLM 전달 시에는 dict 변환 필요.
- **Streaming**: FastAPI `StreamingResponse`는 iterator를 소비하므로, DB 저장을 위해 응답을 가로채서(accumulate) 저장하는 래퍼 로직 필요.

---

## 제안하는 구조

### 1. `src/dtypes/api.py` [MODIFY]

- `ChatRequest`에 `session_id` 필드 추가.

### 2. `src/core/rag/chain.py` [MODIFY]

- `stream_query` 메서드에 `history` 파라미터 추가하여 멀티턴 스트리밍 지원.

### 3. `src/api/routers/chat.py` [MODIFY]

- **의존성 주입**: `get_session`을 통해 DB 세션 접근.
- **Persistent Logic**:
  - `_load_history`: DB에서 메시지 조회 후 List[dict] 변환.
  - `_save_message`: User/Assistant 메시지 DB 저장.
  - **Single Turn (`chat`)**: 요청 -> 로드 -> 생성 -> 저장 -> 응답.
  - **Stream (`chat_stream`)**: 요청 -> 로드 -> 생성(Stream) -> **Hook** -> 저장 -> 응답.

---

## Verification Plan

### Automated Tests (`src/tasktests/phase2_5/test_chat_persistence.py`)

```bash
PYTHONPATH=src pytest src/tasktests/phase2_5/test_chat_persistence.py -v
```

- **test_chat_persistence_basic**: `session_id` 없이 호출 시 저장 안됨 확인.
- **test_chat_persistence_stateful**: 세션 생성 -> 질문1 -> 질문2(질문1 내용 참조) 성공 확인.
- **test_chat_persistence_stream**: 스트리밍 응답 완료 후 DB 저장 확인.

---

## 요약

| 구분         | 파일명                                            | 역할                             |
| ------------ | ------------------------------------------------- | -------------------------------- |
| **[MODIFY]** | `src/api/routers/chat.py`                         | DB 연동 및 메시지 저장 로직 추가 |
| **[MODIFY]** | `src/core/rag/chain.py`                           | 스트리밍 시 History 지원 추가    |
| **[MODIFY]** | `src/dtypes/api.py`                               | `session_id` 필드 추가           |
| **[NEW]**    | `src/tasktests/phase2_5/test_chat_persistence.py` | 통합 테스트                      |
