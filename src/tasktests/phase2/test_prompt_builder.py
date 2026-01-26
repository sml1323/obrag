"""PromptBuilder 단위 테스트"""

import pytest
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.rag.prompt import (
    PromptBuilder, PromptTemplate,
    DEFAULT_RAG_TEMPLATE, CONCISE_TEMPLATE
)


class TestPromptBuilder:
    """PromptBuilder 기본 테스트"""

    def test_build_returns_message_list(self):
        """build()가 메시지 리스트를 반환하는지 확인"""
        builder = PromptBuilder()
        messages = builder.build(question="What is RAG?")

        assert isinstance(messages, list)
        assert len(messages) == 2
        assert messages[0]["role"] == "system"
        assert messages[1]["role"] == "user"

    def test_build_with_context(self):
        """컨텍스트가 메시지에 포함되는지 확인"""
        builder = PromptBuilder()
        context = "[1] RAG is retrieval augmented generation."
        messages = builder.build(question="What is RAG?", context=context)

        user_content = messages[1]["content"]
        assert "RAG is retrieval augmented generation" in user_content

    def test_build_without_context(self):
        """컨텍스트 없을 때 no_context_message 사용 확인"""
        builder = PromptBuilder()
        messages = builder.build(question="What is RAG?", context="")

        user_content = messages[1]["content"]
        assert DEFAULT_RAG_TEMPLATE.no_context_message in user_content

    def test_custom_template(self):
        """커스텀 템플릿 적용 확인"""
        custom = PromptTemplate(
            name="custom",
            system_prompt="Custom system prompt",
            user_template="Q: {question}\nC: {context_section}",
        )
        builder = PromptBuilder(template=custom)
        messages = builder.build(question="Test?")

        assert messages[0]["content"] == "Custom system prompt"
        assert "Q: Test?" in messages[1]["content"]

    def test_concise_template(self):
        """CONCISE_TEMPLATE 사용 확인"""
        builder = PromptBuilder(template=CONCISE_TEMPLATE)
        messages = builder.build(question="Summarize this")

        assert "3 sentences" in messages[0]["content"]

    def test_additional_context(self):
        """additional_context가 시스템 메시지에 추가되는지 확인"""
        builder = PromptBuilder()
        messages = builder.build(
            question="Test?",
            additional_context="You are an expert in Python."
        )

        assert "You are an expert in Python." in messages[0]["content"]


class TestPromptBuilderWithHistory:
    """대화 이력 포함 테스트"""

    def test_build_with_history(self):
        """대화 이력이 메시지에 포함되는지 확인"""
        builder = PromptBuilder()
        history = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"},
        ]
        messages = builder.build_with_history(
            question="What is RAG?",
            context="RAG info here",
            history=history,
        )

        assert len(messages) == 4  # system + 2 history + current
        assert messages[1] == {"role": "user", "content": "Hello"}
        assert messages[2] == {"role": "assistant", "content": "Hi there!"}

    def test_build_with_empty_history(self):
        """빈 이력도 정상 처리되는지 확인"""
        builder = PromptBuilder()
        messages = builder.build_with_history(question="Test", history=[])

        assert len(messages) == 2

    def test_build_with_none_history(self):
        """history=None도 정상 처리되는지 확인"""
        builder = PromptBuilder()
        messages = builder.build_with_history(question="Test", history=None)

        assert len(messages) == 2


class TestPromptTemplate:
    """PromptTemplate 데이터클래스 테스트"""

    def test_default_values(self):
        """기본값이 올바르게 설정되는지 확인"""
        template = PromptTemplate(
            name="test",
            system_prompt="System",
            user_template="User: {question}",
        )

        assert template.context_intro != ""
        assert template.no_context_message != ""

    def test_custom_context_intro(self):
        """커스텀 context_intro 적용 확인"""
        template = PromptTemplate(
            name="test",
            system_prompt="System",
            user_template="User: {question}",
            context_intro="Custom intro:",
        )

        assert template.context_intro == "Custom intro:"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
