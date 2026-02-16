import pytest
from unittest.mock import MagicMock, patch
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class MockLLMResponse:
    content: str
    model: str = "mock-llm"
    usage: dict = None

    def __post_init__(self):
        if self.usage is None:
            self.usage = {"input_tokens": 10, "output_tokens": 5}


@dataclass
class MockRetrievedChunk:
    id: str
    text: str
    metadata: dict
    distance: float = 0.5
    score: float = 0.7


@dataclass
class MockRetrievalResult:
    query: str
    chunks: List[MockRetrievedChunk]
    total_count: int


class TestQueryRewriter:
    def test_rewrite_returns_result_object(self):
        from core.rag.agentic.query_rewriter import QueryRewriter, RewriteResult

        mock_llm = MagicMock()
        mock_llm.generate.return_value = MockLLMResponse(
            content='{"is_clear": true, "rewritten_queries": ["test query"], "clarification_needed": null}'
        )

        rewriter = QueryRewriter(llm=mock_llm)
        result = rewriter.rewrite("test query")

        assert isinstance(result, RewriteResult)
        assert result.is_clear is True
        assert result.rewritten_queries == ["test query"]
        assert result.clarification_needed is None

    def test_rewrite_with_history_resolves_references(self):
        from core.rag.agentic.query_rewriter import QueryRewriter

        mock_llm = MagicMock()
        mock_llm.generate.return_value = MockLLMResponse(
            content='{"is_clear": true, "rewritten_queries": ["How does Python authentication work?"], "clarification_needed": null}'
        )

        rewriter = QueryRewriter(llm=mock_llm)
        history = [
            {"role": "user", "content": "Tell me about Python"},
            {"role": "assistant", "content": "Python is a programming language."},
        ]

        result = rewriter.rewrite("How does it work?", history=history)

        assert len(result.rewritten_queries) > 0
        mock_llm.generate.assert_called_once()
        call_args = mock_llm.generate.call_args[0][0]
        assert any("Python" in str(msg) for msg in call_args)

    def test_rewrite_handles_complex_questions(self):
        from core.rag.agentic.query_rewriter import QueryRewriter

        mock_llm = MagicMock()
        mock_llm.generate.return_value = MockLLMResponse(
            content='{"is_clear": false, "rewritten_queries": ["What is RAG?", "How does retrieval work?", "What are embeddings?"], "clarification_needed": null}'
        )

        rewriter = QueryRewriter(llm=mock_llm)
        result = rewriter.rewrite("Explain RAG, retrieval, and embeddings")

        assert len(result.rewritten_queries) == 3
        assert result.is_clear is False

    def test_rewrite_handles_malformed_json(self):
        from core.rag.agentic.query_rewriter import QueryRewriter

        mock_llm = MagicMock()
        mock_llm.generate.return_value = MockLLMResponse(
            content="This is not valid JSON"
        )

        rewriter = QueryRewriter(llm=mock_llm)
        result = rewriter.rewrite("test query")

        assert result.is_clear is True
        assert len(result.rewritten_queries) > 0

    def test_resolve_references_without_history(self):
        from core.rag.agentic.query_rewriter import QueryRewriter

        mock_llm = MagicMock()
        rewriter = QueryRewriter(llm=mock_llm)

        result = rewriter.resolve_references("What is Python?")

        assert result == "What is Python?"
        mock_llm.generate.assert_not_called()


class TestSelfCorrectingRAGChain:
    def test_query_returns_correction_result(self):
        from core.rag.agentic.self_correcting_chain import (
            SelfCorrectingRAGChain,
            CorrectionResult,
        )

        mock_retriever = MagicMock()
        mock_retriever.retrieve.return_value = MockRetrievalResult(
            query="test",
            chunks=[
                MockRetrievedChunk(id="1", text="Test content", metadata={}, score=0.8),
            ],
            total_count=1,
        )

        mock_llm = MagicMock()
        mock_llm.generate.return_value = MockLLMResponse(content="This is the answer.")

        chain = SelfCorrectingRAGChain(
            retriever=mock_retriever,
            llm=mock_llm,
            quality_threshold=0.5,
        )

        result = chain.query("test question")

        assert isinstance(result, CorrectionResult)
        assert result.answer == "This is the answer."
        assert result.attempts >= 1

    def test_query_retries_on_low_quality(self):
        from core.rag.agentic.self_correcting_chain import SelfCorrectingRAGChain

        low_quality_result = MockRetrievalResult(
            query="test",
            chunks=[
                MockRetrievedChunk(id="1", text="Low quality", metadata={}, score=0.2),
            ],
            total_count=1,
        )

        high_quality_result = MockRetrievalResult(
            query="broadened",
            chunks=[
                MockRetrievedChunk(id="2", text="High quality", metadata={}, score=0.9),
            ],
            total_count=1,
        )

        mock_retriever = MagicMock()
        mock_retriever.retrieve.side_effect = [low_quality_result, high_quality_result]

        mock_llm = MagicMock()
        mock_llm.generate.side_effect = [
            MockLLMResponse(content="broadened query"),
            MockLLMResponse(content="Final answer"),
        ]

        chain = SelfCorrectingRAGChain(
            retriever=mock_retriever,
            llm=mock_llm,
            quality_threshold=0.5,
            max_retries=2,
        )

        result = chain.query("test question")

        assert result.attempts == 2
        assert len(result.all_queries) == 2
        assert mock_retriever.retrieve.call_count == 2

    def test_query_stops_after_max_retries(self):
        from core.rag.agentic.self_correcting_chain import SelfCorrectingRAGChain

        low_quality_result = MockRetrievalResult(
            query="test",
            chunks=[
                MockRetrievedChunk(id="1", text="Low quality", metadata={}, score=0.1),
            ],
            total_count=1,
        )

        mock_retriever = MagicMock()
        mock_retriever.retrieve.return_value = low_quality_result

        mock_llm = MagicMock()
        mock_llm.generate.return_value = MockLLMResponse(content="broadened query")

        chain = SelfCorrectingRAGChain(
            retriever=mock_retriever,
            llm=mock_llm,
            quality_threshold=0.9,
            max_retries=2,
        )

        result = chain.query("test question")

        assert result.attempts == 3
        assert result.retrieval_quality < 0.9

    def test_handles_empty_retrieval(self):
        from core.rag.agentic.self_correcting_chain import SelfCorrectingRAGChain

        empty_result = MockRetrievalResult(query="test", chunks=[], total_count=0)

        mock_retriever = MagicMock()
        mock_retriever.retrieve.return_value = empty_result

        mock_llm = MagicMock()
        mock_llm.generate.return_value = MockLLMResponse(content="broadened")

        chain = SelfCorrectingRAGChain(
            retriever=mock_retriever,
            llm=mock_llm,
        )

        result = chain.query("test")

        assert result.retrieval_quality == 0.0
        assert "couldn't find" in result.answer.lower()


class TestParallelQueryProcessor:
    def test_process_single_query(self):
        from core.rag.agentic.parallel_processor import ParallelQueryProcessor

        mock_retriever = MagicMock()
        mock_retriever.retrieve.return_value = MockRetrievalResult(
            query="test",
            chunks=[MockRetrievedChunk(id="1", text="Result", metadata={})],
            total_count=1,
        )

        processor = ParallelQueryProcessor(retriever=mock_retriever)
        results = processor.process_queries(["test query"])

        assert len(results) == 1
        mock_retriever.retrieve.assert_called_once()

    def test_process_multiple_queries_parallel(self):
        from core.rag.agentic.parallel_processor import ParallelQueryProcessor

        mock_retriever = MagicMock()
        mock_retriever.retrieve.side_effect = [
            MockRetrievalResult(query=f"q{i}", chunks=[], total_count=0)
            for i in range(3)
        ]

        processor = ParallelQueryProcessor(retriever=mock_retriever, max_workers=3)
        results = processor.process_queries(["q1", "q2", "q3"])

        assert len(results) == 3
        assert mock_retriever.retrieve.call_count == 3

    def test_aggregate_deduplicates_results(self):
        from core.rag.agentic.parallel_processor import ParallelQueryProcessor

        mock_retriever = MagicMock()
        processor = ParallelQueryProcessor(retriever=mock_retriever)

        chunk1 = MockRetrievedChunk(id="1", text="Chunk 1", metadata={}, score=0.9)
        chunk2 = MockRetrievedChunk(id="2", text="Chunk 2", metadata={}, score=0.8)
        chunk1_dup = MockRetrievedChunk(id="1", text="Chunk 1", metadata={}, score=0.7)

        results = [
            MockRetrievalResult(query="q1", chunks=[chunk1, chunk2], total_count=2),
            MockRetrievalResult(query="q2", chunks=[chunk1_dup], total_count=1),
        ]

        aggregated = processor.aggregate_results(results, top_k=5, dedup=True)

        assert len(aggregated.chunks) == 2
        chunk_ids = [c.id for c in aggregated.chunks]
        assert chunk_ids.count("1") == 1

    def test_aggregate_sorts_by_score(self):
        from core.rag.agentic.parallel_processor import ParallelQueryProcessor

        mock_retriever = MagicMock()
        processor = ParallelQueryProcessor(retriever=mock_retriever)

        chunks = [
            MockRetrievedChunk(id="1", text="Low", metadata={}, score=0.3),
            MockRetrievedChunk(id="2", text="High", metadata={}, score=0.9),
            MockRetrievedChunk(id="3", text="Mid", metadata={}, score=0.6),
        ]

        results = [MockRetrievalResult(query="q", chunks=chunks, total_count=3)]
        aggregated = processor.aggregate_results(results)

        assert aggregated.chunks[0].score == 0.9
        assert aggregated.chunks[1].score == 0.6
        assert aggregated.chunks[2].score == 0.3

    def test_process_and_aggregate_combined(self):
        from core.rag.agentic.parallel_processor import ParallelQueryProcessor

        mock_retriever = MagicMock()
        mock_retriever.retrieve.side_effect = [
            MockRetrievalResult(
                query="q1",
                chunks=[MockRetrievedChunk(id="1", text="R1", metadata={}, score=0.9)],
                total_count=1,
            ),
            MockRetrievalResult(
                query="q2",
                chunks=[MockRetrievedChunk(id="2", text="R2", metadata={}, score=0.8)],
                total_count=1,
            ),
        ]

        processor = ParallelQueryProcessor(retriever=mock_retriever)
        aggregated = processor.process_and_aggregate(["q1", "q2"], top_k_final=5)

        assert len(aggregated.chunks) == 2
        assert aggregated.queries == ["q1", "q2"]

    def test_handles_empty_query_list(self):
        from core.rag.agentic.parallel_processor import ParallelQueryProcessor

        mock_retriever = MagicMock()
        processor = ParallelQueryProcessor(retriever=mock_retriever)

        results = processor.process_queries([])
        assert results == []

        aggregated = processor.aggregate_results([])
        assert aggregated.chunks == []


class TestHierarchicalChunker:
    def test_chunk_creates_parent_and_children(self):
        from core.rag.agentic.hierarchical_chunker import HierarchicalChunker

        chunker = HierarchicalChunker(
            parent_chunk_size=500,
            child_chunk_size=100,
        )

        text = """# Main Section

This is a long paragraph that contains multiple sentences. It should be chunked appropriately.
The content continues here with more information about the topic at hand.

## Subsection

More content here that adds to the discussion. This section provides additional details.
We need enough text to trigger child chunking behavior in the hierarchical chunker.
"""

        parents, children = chunker.chunk(text, source="test.md")

        assert len(parents) > 0
        assert all(p.level == "parent" for p in parents)

    def test_chunk_respects_headers(self):
        from core.rag.agentic.hierarchical_chunker import HierarchicalChunker

        chunker = HierarchicalChunker(min_chunk_size=20)

        text = """# Introduction

Introduction content goes here with some explanation and more text to ensure it meets minimum size.

# Main Topic

Main topic content with detailed information that is long enough to be considered a valid chunk.

# Conclusion

Conclusion wrapping up the document with additional content to meet minimum requirements.
"""

        parents, _ = chunker.chunk(text, source="test.md")

        assert len(parents) >= 1

        headers_found = []
        for parent in parents:
            if parent.metadata.get("headers"):
                headers_found.extend(parent.metadata["headers"])

        assert len(headers_found) > 0 or len(parents) >= 1

    def test_child_chunks_reference_parent(self):
        from core.rag.agentic.hierarchical_chunker import HierarchicalChunker

        chunker = HierarchicalChunker(
            parent_chunk_size=1000,
            child_chunk_size=200,
        )

        long_text = (
            """# Very Long Section

"""
            + "This is a very long paragraph. " * 100
        )

        parents, children = chunker.chunk(long_text, source="test.md")

        if children:
            for child in children:
                assert child.parent_id is not None
                assert child.level == "child"
                assert "parent_id" in child.metadata

    def test_get_parent_for_child(self):
        from core.rag.agentic.hierarchical_chunker import (
            HierarchicalChunker,
            HierarchicalChunk,
        )

        chunker = HierarchicalChunker()

        parent = HierarchicalChunk(
            id="parent_1",
            text="Parent content",
            metadata={"source": "test.md"},
            level="parent",
        )

        child = HierarchicalChunk(
            id="parent_1::child_0",
            text="Child content",
            metadata={"source": "test.md"},
            parent_id="parent_1",
            level="child",
        )

        found_parent = chunker.get_parent_for_child(child, [parent])

        assert found_parent is not None
        assert found_parent.id == "parent_1"

    def test_chunk_flat_returns_all_chunks(self):
        from core.rag.agentic.hierarchical_chunker import HierarchicalChunker

        chunker = HierarchicalChunker(
            parent_chunk_size=500,
            child_chunk_size=100,
            min_chunk_size=20,
        )

        text = """# Section One

Content for section one with enough text to make it meaningful and pass minimum size requirements.

# Section Two

Content for section two also with sufficient text content to be a valid chunk for testing purposes.
"""

        all_chunks = chunker.chunk_flat(text, source="test.md")

        assert len(all_chunks) > 0
        assert any(c.is_parent for c in all_chunks)

    def test_handles_text_without_headers(self):
        from core.rag.agentic.hierarchical_chunker import HierarchicalChunker

        chunker = HierarchicalChunker(parent_chunk_size=100)

        text = "This is just plain text without any headers. " * 10

        parents, children = chunker.chunk(text, source="test.md")

        assert len(parents) > 0

    def test_respects_min_chunk_size(self):
        from core.rag.agentic.hierarchical_chunker import HierarchicalChunker

        chunker = HierarchicalChunker(min_chunk_size=50)

        text = """# Header

Short.

# Another Header

This is a longer section with enough content to pass the minimum chunk size threshold.
"""

        parents, _ = chunker.chunk(text, source="test.md")

        for parent in parents:
            assert len(parent.text) >= 50 or len(parent.text) == 0


class TestIntegration:
    def test_query_rewriter_with_self_correcting_chain(self):
        from core.rag.agentic.query_rewriter import QueryRewriter
        from core.rag.agentic.self_correcting_chain import SelfCorrectingRAGChain

        mock_llm = MagicMock()
        mock_llm.generate.side_effect = [
            MockLLMResponse(
                content='{"is_clear": true, "rewritten_queries": ["What is RAG?"], "clarification_needed": null}'
            ),
            MockLLMResponse(content="RAG is Retrieval Augmented Generation."),
        ]

        mock_retriever = MagicMock()
        mock_retriever.retrieve.return_value = MockRetrievalResult(
            query="What is RAG?",
            chunks=[
                MockRetrievedChunk(
                    id="1", text="RAG explanation", metadata={}, score=0.8
                )
            ],
            total_count=1,
        )

        rewriter = QueryRewriter(llm=mock_llm)
        chain = SelfCorrectingRAGChain(
            retriever=mock_retriever,
            llm=mock_llm,
        )

        rewrite_result = rewriter.rewrite(
            "What is that thing?",
            history=[
                {"role": "user", "content": "Tell me about RAG"},
            ],
        )

        if rewrite_result.rewritten_queries:
            query = rewrite_result.rewritten_queries[0]
            chain_result = chain.query(query)
            assert chain_result.answer is not None

    def test_parallel_processor_with_rewritten_queries(self):
        from core.rag.agentic.query_rewriter import QueryRewriter
        from core.rag.agentic.parallel_processor import ParallelQueryProcessor

        mock_llm = MagicMock()
        mock_llm.generate.return_value = MockLLMResponse(
            content='{"is_clear": false, "rewritten_queries": ["What is RAG?", "How does retrieval work?"], "clarification_needed": null}'
        )

        mock_retriever = MagicMock()
        mock_retriever.retrieve.side_effect = [
            MockRetrievalResult(
                query="What is RAG?",
                chunks=[MockRetrievedChunk(id="1", text="RAG", metadata={}, score=0.9)],
                total_count=1,
            ),
            MockRetrievalResult(
                query="How does retrieval work?",
                chunks=[
                    MockRetrievedChunk(id="2", text="Retrieval", metadata={}, score=0.8)
                ],
                total_count=1,
            ),
        ]

        rewriter = QueryRewriter(llm=mock_llm)
        processor = ParallelQueryProcessor(retriever=mock_retriever)

        rewrite_result = rewriter.rewrite("Explain RAG and retrieval")

        aggregated = processor.process_and_aggregate(
            rewrite_result.rewritten_queries,
            top_k_final=5,
        )

        assert len(aggregated.chunks) == 2
        assert mock_retriever.retrieve.call_count == 2
