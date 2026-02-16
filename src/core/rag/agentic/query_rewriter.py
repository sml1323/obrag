import json
import re
from dataclasses import dataclass, field
from typing import List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from core.llm.strategy import LLMStrategy, Message


@dataclass
class RewriteResult:
    is_clear: bool
    rewritten_queries: List[str]
    clarification_needed: Optional[str] = None
    original_query: str = ""


class QueryRewriter:
    REWRITE_PROMPT = """You are a query analysis expert.

Given the conversation history and current question, analyze and rewrite the query if needed.

Conversation History:
{history}

Current Question:
{query}

Rules:
1. If the question contains ambiguous references (e.g., "it", "that", "this"), resolve them using conversation history
2. If the question is complex, split it into up to 3 sub-questions
3. If the question is already clear and simple, return it as-is
4. Always respond in the SAME LANGUAGE as the original question

Response Format (JSON only, no markdown):
{{
    "is_clear": true/false,
    "rewritten_queries": ["query1", "query2", ...],
    "clarification_needed": "what clarification is needed, or null if not needed"
}}"""

    def __init__(self, llm: "LLMStrategy"):
        self._llm = llm

    def rewrite(
        self,
        query: str,
        history: Optional[List["Message"]] = None,
    ) -> RewriteResult:
        history_text = self._format_history(history or [])
        prompt = self.REWRITE_PROMPT.format(
            history=history_text if history_text else "(No previous conversation)",
            query=query,
        )

        response = self._llm.generate([{"role": "user", "content": prompt}])
        result = self._parse_response(response.content)

        return RewriteResult(
            is_clear=result.get("is_clear", True),
            rewritten_queries=result.get("rewritten_queries", [query]),
            clarification_needed=result.get("clarification_needed"),
            original_query=query,
        )

    def _format_history(self, history: List["Message"]) -> str:
        if not history:
            return ""

        lines = []
        for msg in history[-6:]:
            role = msg.get("role", "unknown")
            content = msg.get("content", "")
            if len(content) > 200:
                content = content[:200] + "..."
            lines.append(f"{role}: {content}")

        return "\n".join(lines)

    def _parse_response(self, content: str) -> dict:
        content = content.strip()

        if content.startswith("```"):
            content = re.sub(r"```(?:json)?\s*", "", content)
            content = content.rstrip("`").strip()

        try:
            return json.loads(content)
        except json.JSONDecodeError:
            json_match = re.search(r"\{[^{}]*\}", content, re.DOTALL)
            if json_match:
                try:
                    return json.loads(json_match.group())
                except json.JSONDecodeError:
                    pass

            return {
                "is_clear": True,
                "rewritten_queries": [content] if content else [],
                "clarification_needed": None,
            }

    def resolve_references(
        self,
        query: str,
        history: Optional[List["Message"]] = None,
    ) -> str:
        if not history:
            return query

        ambiguous_patterns = [
            r"\b(it|this|that|these|those)\b",
            r"\b(그것|이것|저것|그|이|저)\b",
            r"\b(the same|같은 것|마찬가지)\b",
        ]

        has_ambiguous = any(
            re.search(pattern, query, re.IGNORECASE) for pattern in ambiguous_patterns
        )

        if not has_ambiguous:
            return query

        result = self.rewrite(query, history)
        if result.rewritten_queries:
            return result.rewritten_queries[0]
        return query
