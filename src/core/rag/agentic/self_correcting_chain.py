from dataclasses import dataclass
from typing import List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from core.llm.strategy import LLMStrategy, Message
    from core.rag.retriever import Retriever, RetrievalResult


@dataclass
class CorrectionResult:
    answer: str
    attempts: int
    final_query: str
    retrieval_quality: float
    all_queries: List[str]
    retrieval_result: Optional["RetrievalResult"] = None


class SelfCorrectingRAGChain:
    QUALITY_THRESHOLD = 0.5
    MAX_RETRIES = 2

    BROADEN_PROMPT = """The following search query did not find good results.
Please rewrite it to be broader and more likely to find relevant documents.
Keep the core meaning but use more general terms or synonyms.
Respond with ONLY the rewritten query, nothing else.

Original query: {query}

Rewritten query:"""

    ANSWER_PROMPT = """Based on the following context, answer the question.
If the context doesn't contain enough information, say so honestly.

Context:
{context}

Question: {question}

Answer:"""

    def __init__(
        self,
        retriever: "Retriever",
        llm: "LLMStrategy",
        quality_threshold: float = 0.5,
        max_retries: int = 2,
    ):
        self._retriever = retriever
        self._llm = llm
        self.QUALITY_THRESHOLD = quality_threshold
        self.MAX_RETRIES = max_retries

    def query(
        self,
        question: str,
        top_k: int = 5,
        temperature: float = 0.7,
    ) -> CorrectionResult:
        current_query = question
        attempts = 0
        all_queries = [question]
        result = None
        quality = 0.0

        while attempts <= self.MAX_RETRIES:
            attempts += 1

            result = self._retriever.retrieve(current_query, top_k=top_k)
            quality = self._evaluate_quality(result)

            if quality >= self.QUALITY_THRESHOLD:
                answer = self._generate_answer(question, result, temperature)
                return CorrectionResult(
                    answer=answer,
                    attempts=attempts,
                    final_query=current_query,
                    retrieval_quality=quality,
                    all_queries=all_queries,
                    retrieval_result=result,
                )

            if attempts <= self.MAX_RETRIES:
                current_query = self._broaden_query(current_query)
                all_queries.append(current_query)

        answer = self._generate_answer(question, result, temperature)
        return CorrectionResult(
            answer=answer,
            attempts=attempts,
            final_query=current_query,
            retrieval_quality=quality,
            all_queries=all_queries,
            retrieval_result=result,
        )

    def _evaluate_quality(self, result: "RetrievalResult") -> float:
        if not result or not result.chunks:
            return 0.0

        top_chunks = result.chunks[:3]
        if not top_chunks:
            return 0.0

        scores = [chunk.score for chunk in top_chunks]
        return sum(scores) / len(scores)

    def _broaden_query(self, query: str) -> str:
        prompt = self.BROADEN_PROMPT.format(query=query)
        response = self._llm.generate(
            [{"role": "user", "content": prompt}],
            temperature=0.3,
        )
        return response.content.strip()

    def _generate_answer(
        self,
        question: str,
        result: Optional["RetrievalResult"],
        temperature: float,
    ) -> str:
        if not result or not result.chunks:
            return "I couldn't find relevant information to answer your question."

        context_parts = []
        for i, chunk in enumerate(result.chunks[:5], 1):
            source = chunk.metadata.get("source", "unknown")
            context_parts.append(f"[{i}] Source: {source}\n{chunk.text}")

        context = "\n\n".join(context_parts)

        prompt = self.ANSWER_PROMPT.format(
            context=context,
            question=question,
        )

        response = self._llm.generate(
            [{"role": "user", "content": prompt}],
            temperature=temperature,
        )
        return response.content
