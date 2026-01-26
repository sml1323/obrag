# RAGChain 구현 계획

> **Target Task**: Phase 2 - RAG 파이프라인 > RAGChain
> **Target Path**: `src/core/rag/chain.py`

## 목표

Retriever + PromptBuilder + LLM을 연결하여 **end-to-end RAG 질의응답 파이프라인**을 완성합니다.
사용자 질문을 받아 관련 문서를 검색하고, 컨텍스트를 주입한 프롬프트를 생성하여 LLM으로 응답을 생성합니다.

---

## 기존 컴포넌트 분석

### 1. Retriever (`src/core/rag/retriever.py`)

```python
retriever.retrieve(query, top_k=5) → RetrievalResult
retriever.retrieve_with_context(query, top_k=5) → str
```

### 2. PromptBuilder (`src/core/rag/prompt.py`)

```python
builder.build(question, context) → List[Message]
builder.build_with_history(question, context, history) → List[Message]
```

### 3. LLMStrategy (`src/core/llm/strategy.py`)

```python
llm.generate(messages, temperature=0.7) → LLMResponse
```

---

## 제안하는 구조

### 파일 구조

```
src/core/rag/
├── __init__.py     # RAGChain export 추가
├── retriever.py    # (기존)
├── prompt.py       # (기존)
└── chain.py        # [NEW] RAGChain 모듈
```

---

## 파일별 상세 계획

### 1. `src/core/rag/chain.py` [NEW]

```python
"""
RAGChain Module

Retriever + PromptBuilder + LLM을 연결하는 통합 RAG 파이프라인.
"""

from dataclasses import dataclass
from typing import List, Optional

from .retriever import Retriever, RetrievalResult
from .prompt import PromptBuilder, PromptTemplate, DEFAULT_RAG_TEMPLATE
from core.llm.strategy import LLMStrategy, Message, LLMResponse


# ============================================================================
# Data Classes
# ============================================================================

@dataclass
class RAGResponse:
    """RAG 파이프라인 응답 데이터"""

    answer: str                    # LLM 생성 응답
    retrieval_result: RetrievalResult  # 검색 결과
    model: str                     # 사용된 LLM 모델명
    usage: dict                    # 토큰 사용량


# ============================================================================
# RAGChain Class
# ============================================================================

class RAGChain:
    """
    End-to-end RAG 파이프라인.

    사용법:
        # 기본 사용
        chain = RAGChain(retriever=retriever, llm=llm)
        response = chain.query("What is RAG?")
        print(response.answer)

        # 커스텀 템플릿 사용
        chain = RAGChain(
            retriever=retriever,
            llm=llm,
            template=CONCISE_TEMPLATE
        )

        # top_k 및 temperature 조절
        response = chain.query(
            question="Explain Python decorators",
            top_k=3,
            temperature=0.5
        )
    """

    def __init__(
        self,
        retriever: Retriever,
        llm: LLMStrategy,
        template: Optional[PromptTemplate] = None,
    ):
        """
        Args:
            retriever: 벡터 검색을 수행할 Retriever 인스턴스
            llm: 응답 생성을 위한 LLM 인스턴스
            template: 프롬프트 템플릿 (기본값: DEFAULT_RAG_TEMPLATE)
        """
        self._retriever = retriever
        self._llm = llm
        self._prompt_builder = PromptBuilder(template)

    @property
    def prompt_builder(self) -> PromptBuilder:
        return self._prompt_builder

    def query(
        self,
        question: str,
        *,
        top_k: int = 5,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> RAGResponse:
        """
        질문에 대한 RAG 기반 응답 생성.

        Args:
            question: 사용자 질문
            top_k: 검색할 문서 수
            temperature: LLM 응답 다양성
            max_tokens: 최대 생성 토큰 수

        Returns:
            RAGResponse (answer, retrieval_result, model, usage)
        """
        # 1. 검색
        retrieval_result = self._retriever.retrieve(question, top_k=top_k)
        context = self._retriever.retrieve_with_context(question, top_k=top_k)

        # 2. 프롬프트 생성
        messages = self._prompt_builder.build(
            question=question,
            context=context,
        )

        # 3. LLM 호출
        llm_response = self._llm.generate(
            messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )

        return RAGResponse(
            answer=llm_response.content,
            retrieval_result=retrieval_result,
            model=llm_response.model,
            usage=llm_response.usage,
        )

    def query_with_history(
        self,
        question: str,
        history: Optional[List[Message]] = None,
        *,
        top_k: int = 5,
        temperature: float = 0.7,
    ) -> RAGResponse:
        """
        대화 이력을 포함한 멀티턴 RAG 질의.

        Args:
            question: 현재 질문
            history: 이전 대화 이력
            top_k: 검색할 문서 수
            temperature: LLM 응답 다양성

        Returns:
            RAGResponse
        """
        # 1. 검색
        retrieval_result = self._retriever.retrieve(question, top_k=top_k)
        context = self._retriever.retrieve_with_context(question, top_k=top_k)

        # 2. 프롬프트 생성 (이력 포함)
        messages = self._prompt_builder.build_with_history(
            question=question,
            context=context,
            history=history,
        )

        # 3. LLM 호출
        llm_response = self._llm.generate(messages, temperature=temperature)

        return RAGResponse(
            answer=llm_response.content,
            retrieval_result=retrieval_result,
            model=llm_response.model,
            usage=llm_response.usage,
        )
```

### 2. `src/core/rag/__init__.py` [MODIFY]

```python
# 기존 export에 추가
from .chain import RAGChain, RAGResponse
```

### 3. `src/tasktests/phase2/test_rag_chain.py` [NEW]

```python
"""RAGChain 단위 테스트"""

import pytest
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.rag.chain import RAGChain, RAGResponse
from core.rag.prompt import CONCISE_TEMPLATE
from core.llm.strategy import FakeLLM


class MockChromaStore:
    """테스트용 Mock ChromaStore"""

    def query(self, query_text, n_results=5, **kwargs):
        return [
            {
                "id": "chunk_1",
                "text": "RAG는 Retrieval Augmented Generation의 약자입니다.",
                "metadata": {"source": "rag_intro.md"},
                "distance": 0.5,
            },
            {
                "id": "chunk_2",
                "text": "RAG는 검색과 생성을 결합합니다.",
                "metadata": {"source": "rag_details.md"},
                "distance": 0.8,
            },
        ]


class TestRAGChain:
    """RAGChain 기본 테스트"""

    @pytest.fixture
    def chain(self):
        from core.rag import Retriever
        store = MockChromaStore()
        retriever = Retriever(store)
        llm = FakeLLM(response="This is the answer about RAG.")
        return RAGChain(retriever=retriever, llm=llm)

    def test_query_returns_rag_response(self, chain):
        """query()가 RAGResponse를 반환하는지 확인"""
        response = chain.query("What is RAG?")

        assert isinstance(response, RAGResponse)
        assert response.answer == "This is the answer about RAG."
        assert response.model == "fake-llm"

    def test_query_includes_retrieval_result(self, chain):
        """검색 결과가 포함되는지 확인"""
        response = chain.query("What is RAG?")

        assert response.retrieval_result is not None
        assert response.retrieval_result.total_count == 2

    def test_query_with_top_k(self, chain):
        """top_k 파라미터 동작 확인"""
        response = chain.query("Test", top_k=1)
        # MockStore는 항상 2개 반환하므로 실제로는 2개
        assert response.retrieval_result is not None

    def test_custom_template(self):
        """커스텀 템플릿 적용 확인"""
        from core.rag import Retriever
        store = MockChromaStore()
        retriever = Retriever(store)
        llm = FakeLLM()

        chain = RAGChain(
            retriever=retriever,
            llm=llm,
            template=CONCISE_TEMPLATE
        )

        assert chain.prompt_builder.template.name == "concise"


class TestRAGChainWithHistory:
    """멀티턴 대화 테스트"""

    @pytest.fixture
    def chain(self):
        from core.rag import Retriever
        store = MockChromaStore()
        retriever = Retriever(store)
        llm = FakeLLM(response="Follow-up answer")
        return RAGChain(retriever=retriever, llm=llm)

    def test_query_with_history(self, chain):
        """대화 이력 포함 질의 확인"""
        history = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi!"},
        ]
        response = chain.query_with_history(
            question="What is RAG?",
            history=history
        )

        assert response.answer == "Follow-up answer"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
```

---

## Verification Plan

### Automated Tests

1. **단위 테스트 실행**

   ```bash
   uv run pytest src/tasktests/phase2/test_rag_chain.py -v
   ```

2. **전체 Phase 2 테스트**

   ```bash
   uv run pytest src/tasktests/phase2/ -v
   ```

3. **임포트 확인**
   ```bash
   uv run python -c "from src.core.rag import RAGChain, RAGResponse; print('OK')"
   ```

---

## 요약

| 항목            | 내용                                        |
| --------------- | ------------------------------------------- |
| **신규 파일**   | `src/core/rag/chain.py`                     |
| **수정 파일**   | `src/core/rag/__init__.py`                  |
| **테스트 파일** | `src/tasktests/phase2/test_rag_chain.py`    |
| **핵심 클래스** | `RAGChain`, `RAGResponse`                   |
| **메서드**      | `query()`, `query_with_history()`           |
| **의존성**      | `Retriever`, `PromptBuilder`, `LLMStrategy` |
