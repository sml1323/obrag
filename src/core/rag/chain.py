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

    answer: str                        # LLM 생성 응답
    retrieval_result: RetrievalResult  # 검색 결과
    model: str                         # 사용된 LLM 모델명
    usage: dict                        # 토큰 사용량


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
