import asyncio
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from typing import List, Optional, Set, TYPE_CHECKING

if TYPE_CHECKING:
    from core.rag.retriever import Retriever, RetrievalResult, RetrievedChunk


@dataclass
class AggregatedResult:
    queries: List[str]
    chunks: List["RetrievedChunk"]
    total_count: int
    query_results: dict = field(default_factory=dict)


class ParallelQueryProcessor:
    def __init__(
        self,
        retriever: "Retriever",
        max_workers: int = 3,
    ):
        self._retriever = retriever
        self._max_workers = max_workers

    def process_queries(
        self,
        queries: List[str],
        top_k: int = 5,
    ) -> List["RetrievalResult"]:
        if not queries:
            return []

        if len(queries) == 1:
            return [self._retriever.retrieve(queries[0], top_k=top_k)]

        results = []
        with ThreadPoolExecutor(max_workers=self._max_workers) as executor:
            future_to_query = {
                executor.submit(self._retriever.retrieve, q, top_k): q for q in queries
            }

            for future in as_completed(future_to_query):
                try:
                    result = future.result()
                    results.append(result)
                except Exception:
                    pass

        return results

    async def process_queries_async(
        self,
        queries: List[str],
        top_k: int = 5,
    ) -> List["RetrievalResult"]:
        if not queries:
            return []

        loop = asyncio.get_event_loop()

        with ThreadPoolExecutor(max_workers=self._max_workers) as executor:
            tasks = [
                loop.run_in_executor(
                    executor,
                    self._retriever.retrieve,
                    q,
                    top_k,
                )
                for q in queries
            ]

            results = await asyncio.gather(*tasks, return_exceptions=True)

        return [r for r in results if not isinstance(r, Exception)]

    def aggregate_results(
        self,
        results: List["RetrievalResult"],
        top_k: int = 5,
        dedup: bool = True,
    ) -> AggregatedResult:
        if not results:
            return AggregatedResult(
                queries=[],
                chunks=[],
                total_count=0,
            )

        all_chunks: List["RetrievedChunk"] = []
        seen_ids: Set[str] = set()
        queries = []
        query_results = {}

        for result in results:
            queries.append(result.query)
            query_results[result.query] = result

            for chunk in result.chunks:
                if dedup and chunk.id in seen_ids:
                    continue

                all_chunks.append(chunk)
                if dedup:
                    seen_ids.add(chunk.id)

        all_chunks.sort(key=lambda c: c.score, reverse=True)

        return AggregatedResult(
            queries=queries,
            chunks=all_chunks[:top_k],
            total_count=len(all_chunks),
            query_results=query_results,
        )

    def process_and_aggregate(
        self,
        queries: List[str],
        top_k_per_query: int = 5,
        top_k_final: int = 5,
        dedup: bool = True,
    ) -> AggregatedResult:
        results = self.process_queries(queries, top_k=top_k_per_query)
        return self.aggregate_results(results, top_k=top_k_final, dedup=dedup)

    async def process_and_aggregate_async(
        self,
        queries: List[str],
        top_k_per_query: int = 5,
        top_k_final: int = 5,
        dedup: bool = True,
    ) -> AggregatedResult:
        results = await self.process_queries_async(queries, top_k=top_k_per_query)
        return self.aggregate_results(results, top_k=top_k_final, dedup=dedup)
