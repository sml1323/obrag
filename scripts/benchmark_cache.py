"""
리소스 캐싱 효과 벤치마크.

get_rag_chain 이 요청마다 Embedder/ChromaStore 를 재생성하던 구조(PR 이전)와,
설정 시그니처별로 캐시해 재사용하는 구조(PR 이후)의 요청당 오버헤드를 비교한다.

LLM 생성 비용은 제외하고, "임베더 로드 + ChromaStore 오픈 + 쿼리 임베딩 + 벡터검색"
까지의 리소스 구성 오버헤드만 측정한다.

실행:
    PYTHONPATH=src python scripts/benchmark_cache.py [--model intfloat/multilingual-e5-small] [-n 6]
"""

import argparse
import statistics
import tempfile
import time

import api.deps as deps
from config.models import MultilingualE5EmbeddingConfig
from core.embedding.factory import EmbedderFactory
from db.chroma_store import ChromaStore


class _Chunk:
    def __init__(self, text: str, metadata: dict):
        self.text = text
        self.metadata = metadata


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="intfloat/multilingual-e5-small")
    ap.add_argument("-n", type=int, default=6, help="측정 반복 횟수")
    ap.add_argument("--provider", default="multilingual_e5")
    args = ap.parse_args()

    chroma = tempfile.mkdtemp()
    emb0, m0 = deps.build_embedder(args.provider, args.model)
    store0 = deps.build_store(chroma, "obsidian_notes", emb0, m0)
    store0.upsert_chunks(
        [_Chunk(f"문서 {i}: RAG 마크다운 검색 성능 테스트", {"source": f"d{i}.md"}) for i in range(30)],
        "bench.md",
    )

    def old_style(n: int) -> list[float]:
        """요청마다 embedder/store 재생성 (PR 이전 동작)."""
        ts = []
        for _ in range(n):
            t = time.perf_counter()
            e = EmbedderFactory.create(MultilingualE5EmbeddingConfig(model_name=args.model))
            s = ChromaStore(persist_path=chroma, collection_name=store0.collection_name, embedder=e)
            s.query("성능 테스트", n_results=5)
            ts.append(time.perf_counter() - t)
        return ts

    def new_style(n: int) -> list[float]:
        """캐시된 embedder/store 재사용 (PR 동작)."""
        ts = []
        for _ in range(n):
            t = time.perf_counter()
            e, m = deps.build_embedder(args.provider, args.model)
            s = deps.build_store(chroma, "obsidian_notes", e, m)
            s.query("성능 테스트", n_results=5)
            ts.append(time.perf_counter() - t)
        return ts

    old_style(1)
    new_style(1)  # 워밍업
    old = old_style(args.n)
    new = new_style(args.n)
    om = statistics.median(old) * 1000
    nm = statistics.median(new) * 1000
    print(f"model={args.model}  n={args.n}")
    print(f"  OLD (요청마다 재생성): {om:8.1f} ms/req")
    print(f"  NEW (캐시 재사용)    : {nm:8.1f} ms/req")
    print(f"  speedup: {om / nm:.1f}x  (요청당 {om - nm:.1f} ms 절감)")


if __name__ == "__main__":
    main()
