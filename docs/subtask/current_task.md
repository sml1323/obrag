# RAG Chat Endpoints 구현 계획

> **Target Task**: Phase 2 - FastAPI 백엔드 > RAG Chat Endpoints
> **Target Path**: `src/api/routers/chat.py`

## 목표

RAG 기반 질의응답 엔드포인트를 구현합니다:

- `/chat`: 단일 질의 (동기)
- `/chat/stream`: 스트리밍 응답 (SSE)
- `/chat/history`: 대화 이력 포함 멀티턴

---

## 기존 패턴 분석

### 1. DI 패턴 (`deps.py`)

- `AppState` 데이터클래스로 전역 상태 캡슐화
- `get_rag_chain()` 의존성 함수로 `RAGChain` 주입
- `request.app.state.deps`를 통한 접근

### 2. RAGChain 인터페이스 (`chain.py`)

```python
# 이미 구현됨
chain.query(question, top_k=5, temperature=0.7) -> RAGResponse
chain.query_with_history(question, history, top_k=5) -> RAGResponse
```

### 3. LLMStrategy 현황 (`strategy.py`)

- `generate()` 메서드만 존재 (동기)
- **스트리밍 메서드 없음** → 추가 필요

---

## 제안하는 구조

```
src/api/
├── routers/           [NEW] 라우터 디렉토리
│   ├── __init__.py    [NEW]
│   └── chat.py        [NEW] 채팅 엔드포인트
├── main.py            [MODIFY] 라우터 등록
└── deps.py            (변경 없음)

src/core/llm/
├── strategy.py        [MODIFY] stream_generate() 추가
├── openai_llm.py      [MODIFY] 스트리밍 구현
├── gemini_llm.py      [MODIFY] 스트리밍 구현
└── ollama_llm.py      [MODIFY] 스트리밍 구현

src/core/rag/
└── chain.py           [MODIFY] stream_query() 추가

src/dtypes/
└── api.py             [NEW] API 요청/응답 스키마
```

---

## 파일별 상세 계획

### 1. `src/dtypes/api.py` [NEW]

API 요청/응답 Pydantic 모델 정의.

```python
from pydantic import BaseModel
from typing import List, Optional

class ChatRequest(BaseModel):
    """채팅 요청 스키마"""
    question: str
    top_k: int = 5
    temperature: float = 0.7
    max_tokens: Optional[int] = None

class ChatHistoryRequest(ChatRequest):
    """대화 이력 포함 채팅 요청"""
    history: List[dict] = []  # [{"role": "user/assistant", "content": "..."}]

class SourceChunk(BaseModel):
    """근거 문서 정보"""
    content: str
    source: str
    score: float

class ChatResponse(BaseModel):
    """채팅 응답 스키마"""
    answer: str
    sources: List[SourceChunk]
    model: str
    usage: dict

class StreamChunk(BaseModel):
    """스트리밍 청크"""
    content: str
    done: bool = False
```

---

### 2. `src/core/llm/strategy.py` [MODIFY]

스트리밍 메서드를 Protocol에 추가.

```python
from typing import Iterator, AsyncIterator

class LLMStrategy(Protocol):
    # 기존 generate() 유지

    def stream_generate(
        self,
        messages: List[Message],
        *,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> Iterator[str]:
        """스트리밍 응답 생성 (Generator)"""
        ...
```

---

### 3. `src/core/llm/openai_llm.py` [MODIFY]

OpenAI 스트리밍 구현.

```python
def stream_generate(
    self,
    messages: List[Message],
    *,
    temperature: float = 0.7,
    max_tokens: Optional[int] = None,
) -> Iterator[str]:
    response = self._client.chat.completions.create(
        model=self._model_name,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
        stream=True,  # 스트리밍 활성화
    )
    for chunk in response:
        if chunk.choices[0].delta.content:
            yield chunk.choices[0].delta.content
```

---

### 4. `src/core/rag/chain.py` [MODIFY]

스트리밍 query 메서드 추가.

```python
def stream_query(
    self,
    question: str,
    *,
    top_k: int = 5,
    temperature: float = 0.7,
) -> tuple[RetrievalResult, Iterator[str]]:
    """스트리밍 RAG 응답 생성.

    Returns:
        (retrieval_result, content_generator)
    """
    retrieval_result = self._retriever.retrieve(question, top_k=top_k)
    context = self._retriever.retrieve_with_context(question, top_k=top_k)
    messages = self._prompt_builder.build(question=question, context=context)

    return retrieval_result, self._llm.stream_generate(messages, temperature=temperature)
```

---

### 5. `src/api/routers/chat.py` [NEW]

채팅 엔드포인트 구현.

```python
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from api.deps import get_rag_chain
from core.rag import RAGChain
from dtypes.api import ChatRequest, ChatHistoryRequest, ChatResponse

router = APIRouter(prefix="/chat", tags=["chat"])

@router.post("", response_model=ChatResponse)
async def chat(request: ChatRequest, chain: RAGChain = Depends(get_rag_chain)):
    """단일 질의 RAG 응답"""
    response = chain.query(
        request.question,
        top_k=request.top_k,
        temperature=request.temperature,
        max_tokens=request.max_tokens,
    )
    return ChatResponse(
        answer=response.answer,
        sources=[...],  # retrieval_result 변환
        model=response.model,
        usage=response.usage,
    )

@router.post("/stream")
async def chat_stream(request: ChatRequest, chain: RAGChain = Depends(get_rag_chain)):
    """SSE 스트리밍 응답"""
    retrieval_result, generator = chain.stream_query(...)

    async def event_generator():
        for chunk in generator:
            yield f"data: {chunk}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")

@router.post("/history", response_model=ChatResponse)
async def chat_with_history(request: ChatHistoryRequest, chain: RAGChain = Depends(get_rag_chain)):
    """대화 이력 포함 멀티턴"""
    response = chain.query_with_history(
        request.question,
        history=request.history,
        top_k=request.top_k,
        temperature=request.temperature,
    )
    return ChatResponse(...)
```

---

### 6. `src/api/main.py` [MODIFY]

라우터 등록.

```python
from .routers import chat

def create_app() -> FastAPI:
    app = FastAPI(...)

    # 라우터 등록
    app.include_router(chat.router)

    return app
```

---

## Verification Plan

### Automated Tests

테스트 파일: `src/tasktests/phase2/test_api_chat.py`

```bash
# 전체 테스트 실행
cd /Users/imseungmin/work/portfolio/obsidian_RAG/obrag
python -m pytest src/tasktests/phase2/test_api_chat.py -v
```

**테스트 항목:**

1. **엔드포인트 존재 확인**
   - `POST /chat` 라우트 존재
   - `POST /chat/stream` 라우트 존재
   - `POST /chat/history` 라우트 존재

2. **정상 응답 테스트 (FakeLLM 사용)**
   - `/chat` → `ChatResponse` 형식 반환
   - `/chat/history` → 이력 포함 응답

3. **스트리밍 테스트**
   - `/chat/stream` → `text/event-stream` Content-Type
   - SSE 형식 (`data: ...`) 확인

4. **입력 검증**
   - 빈 question → 422 에러
   - 잘못된 temperature 범위 → 검증 에러

---

## 요약

| 항목           | 내용                                                                                    |
| -------------- | --------------------------------------------------------------------------------------- |
| **새 파일**    | `routers/__init__.py`, `routers/chat.py`, `dtypes/api.py`, `test_api_chat.py`           |
| **수정 파일**  | `strategy.py`, `openai_llm.py`, `gemini_llm.py`, `ollama_llm.py`, `chain.py`, `main.py` |
| **엔드포인트** | `POST /chat`, `POST /chat/stream`, `POST /chat/history`                                 |
| **의존성**     | `pydantic` (이미 FastAPI에 포함)                                                        |
| **테스트**     | `test_api_chat.py` (단위 + Mock 기반)                                                   |
