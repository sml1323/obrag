"""
PromptBuilder Module

Retrieved context를 LLM 프롬프트에 주입하는 템플릿 빌더.
"""

from dataclasses import dataclass
from typing import List, Optional

from core.llm.strategy import Message


# ============================================================================
# Data Classes
# ============================================================================

@dataclass
class PromptTemplate:
    """프롬프트 템플릿 정의"""

    name: str
    system_prompt: str
    user_template: str  # {question}, {context_section} 플레이스홀더 사용

    # 선택적 설정
    context_intro: str = "다음은 관련 문서에서 검색된 내용입니다:"
    no_context_message: str = "관련 문서를 찾지 못했습니다."


# ============================================================================
# Default Templates
# ============================================================================

DEFAULT_RAG_TEMPLATE = PromptTemplate(
    name="rag_qa",
    system_prompt="""You are a helpful assistant that answers questions based on the provided context.
Answer in the same language as the question.
If the context doesn't contain relevant information, say so honestly.""",
    user_template="""{context_section}

Question: {question}""",
)

CONCISE_TEMPLATE = PromptTemplate(
    name="concise",
    system_prompt="""Answer concisely based on the context. Maximum 3 sentences.
If unsure, say "I don't know." Answer in the same language as the question.""",
    user_template="""{context_section}

Question: {question}""",
)


# ============================================================================
# PromptBuilder Class
# ============================================================================

class PromptBuilder:
    """
    검색된 컨텍스트를 LLM 메시지로 변환하는 빌더.

    사용법:
        builder = PromptBuilder()  # 기본 RAG 템플릿 사용

        messages = builder.build(
            question="What is RAG?",
            context="[1] RAG combines retrieval and generation..."
        )

        # LLM 호출
        response = llm.generate(messages)
    """

    def __init__(self, template: Optional[PromptTemplate] = None):
        self._template = template or DEFAULT_RAG_TEMPLATE

    @property
    def template(self) -> PromptTemplate:
        return self._template

    def build(
        self,
        question: str,
        context: str = "",
        additional_context: Optional[str] = None,
    ) -> List[Message]:
        """
        질문과 컨텍스트를 LLM 메시지 리스트로 변환.

        Args:
            question: 사용자 질문
            context: 검색된 컨텍스트 (Retriever.retrieve_with_context 결과)
            additional_context: 추가 시스템 컨텍스트 (선택)

        Returns:
            LLM에 전달할 메시지 리스트
        """
        # 컨텍스트 섹션 구성
        if context.strip():
            context_section = f"{self._template.context_intro}\n\n{context}"
        else:
            context_section = self._template.no_context_message

        # 시스템 메시지
        system_content = self._template.system_prompt
        if additional_context:
            system_content += f"\n\n{additional_context}"

        # 사용자 메시지
        user_content = self._template.user_template.format(
            question=question,
            context_section=context_section,
        )

        return [
            {"role": "system", "content": system_content},
            {"role": "user", "content": user_content},
        ]

    def build_with_history(
        self,
        question: str,
        context: str = "",
        history: Optional[List[Message]] = None,
    ) -> List[Message]:
        """
        대화 이력을 포함한 메시지 리스트 생성 (멀티턴 대화용).

        Args:
            question: 현재 질문
            context: 검색된 컨텍스트
            history: 이전 대화 이력 [{"role": "user/assistant", "content": ...}]

        Returns:
            시스템 메시지 + 이력 + 현재 질문을 포함한 메시지 리스트
        """
        messages: List[Message] = [
            {"role": "system", "content": self._template.system_prompt}
        ]

        # 대화 이력 추가
        if history:
            messages.extend(history)

        # 컨텍스트 + 현재 질문
        if context.strip():
            context_section = f"{self._template.context_intro}\n\n{context}"
        else:
            context_section = ""

        current_content = self._template.user_template.format(
            question=question,
            context_section=context_section,
        )
        messages.append({"role": "user", "content": current_content})

        return messages
