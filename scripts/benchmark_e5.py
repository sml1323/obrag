#!/usr/bin/env python3
"""
Benchmark script for Multilingual E5 embedder.
Tests cross-lingual retrieval performance (Korean <-> English).
"""

import sys
import time
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from typing import List, Tuple
import numpy as np


def cosine_similarity(a: List[float], b: List[float]) -> float:
    """Calculate cosine similarity between two vectors."""
    a_np = np.array(a)
    b_np = np.array(b)
    return float(np.dot(a_np, b_np) / (np.linalg.norm(a_np) * np.linalg.norm(b_np)))


def run_benchmark():
    print("=" * 60)
    print("Multilingual E5 Embedding Benchmark")
    print("=" * 60)

    # Import and create embedder
    print("\n[1] Loading model...")
    start_time = time.time()

    from core.embedding.multilingual_e5_embedder import MultilingualE5Embedder

    embedder = MultilingualE5Embedder()

    # Force model load by embedding a test text
    _ = embedder.embed("test")
    load_time = time.time() - start_time
    print(f"    Model loaded in {load_time:.2f}s")
    print(f"    Model: {embedder.model_name}")
    print(f"    Dimension: {embedder.dimension}")

    # Test documents (Korean)
    korean_docs = [
        "API 인증을 위해서는 먼저 API 키를 발급받아야 합니다. 발급받은 키는 요청 헤더에 포함시켜 전송합니다.",
        "데이터베이스 연결 시 connection pool을 사용하면 성능을 크게 향상시킬 수 있습니다.",
        "React에서 상태 관리는 useState 훅을 사용하거나 Redux 같은 외부 라이브러리를 활용할 수 있습니다.",
        "Python에서 비동기 프로그래밍은 async/await 키워드를 사용하여 구현합니다.",
        "Git에서 브랜치를 병합할 때 충돌이 발생하면 수동으로 해결해야 합니다.",
    ]

    # Test documents (English)
    english_docs = [
        "To authenticate with the API, you first need to obtain an API key. Include the key in your request headers.",
        "Using a connection pool for database connections can significantly improve performance.",
        "In React, state management can be done using the useState hook or external libraries like Redux.",
        "Asynchronous programming in Python is implemented using async/await keywords.",
        "When merging branches in Git, conflicts must be resolved manually if they occur.",
    ]

    # Test queries
    test_cases = [
        # (query, expected_top_doc_index, description)
        ("How to authenticate API?", 0, "EN query -> EN/KO auth doc"),
        ("API 인증 방법", 0, "KO query -> EN/KO auth doc"),
        ("database connection optimization", 1, "EN query -> EN/KO db doc"),
        ("데이터베이스 성능 향상", 1, "KO query -> EN/KO db doc"),
        ("React state management hooks", 2, "EN query -> EN/KO React doc"),
        ("리액트 상태 관리", 2, "KO query -> EN/KO React doc"),
        ("Python async programming", 3, "EN query -> EN/KO async doc"),
        ("파이썬 비동기 프로그래밍", 3, "KO query -> EN/KO async doc"),
        ("Git merge conflict resolution", 4, "EN query -> EN/KO git doc"),
        ("깃 브랜치 충돌 해결", 4, "KO query -> EN/KO git doc"),
    ]

    # Embed documents
    print("\n[2] Embedding documents...")
    start_time = time.time()

    korean_embeddings = embedder.embed_documents(korean_docs)
    english_embeddings = embedder.embed_documents(english_docs)
    all_docs = korean_docs + english_docs
    all_embeddings = korean_embeddings + english_embeddings

    embed_time = time.time() - start_time
    print(f"    Embedded {len(all_docs)} documents in {embed_time:.2f}s")
    print(f"    Avg time per document: {embed_time / len(all_docs) * 1000:.1f}ms")

    # Run retrieval tests
    print("\n[3] Running cross-lingual retrieval tests...")
    print("-" * 60)

    results = []
    query_times = []

    for query, expected_idx, description in test_cases:
        start_time = time.time()
        query_embedding = embedder.embed_query(query)
        query_time = time.time() - start_time
        query_times.append(query_time)

        # Calculate similarities
        similarities = [
            (i, cosine_similarity(query_embedding, doc_emb))
            for i, doc_emb in enumerate(all_embeddings)
        ]
        similarities.sort(key=lambda x: x[1], reverse=True)

        # Check if expected doc is in top results
        top_3_indices = [idx for idx, _ in similarities[:3]]

        # Expected can match either Korean (idx) or English (idx + 5) version
        korean_match = expected_idx in top_3_indices
        english_match = (expected_idx + 5) in top_3_indices
        success = korean_match or english_match

        results.append(
            {
                "query": query,
                "description": description,
                "success": success,
                "top_3": [(idx, f"{sim:.3f}") for idx, sim in similarities[:3]],
                "expected": expected_idx,
                "query_time": query_time,
            }
        )

        status = "✅" if success else "❌"
        print(f"{status} {description}")
        print(
            f'   Query: "{query[:40]}..."'
            if len(query) > 40
            else f'   Query: "{query}"'
        )
        print(f"   Top 3: {[(idx, sim) for idx, sim in similarities[:3]]}")
        print(f"   Time: {query_time * 1000:.1f}ms")
        print()

    # Summary
    print("=" * 60)
    print("BENCHMARK SUMMARY")
    print("=" * 60)

    success_count = sum(1 for r in results if r["success"])
    total_count = len(results)
    accuracy = success_count / total_count * 100

    print(
        f"\nCross-lingual Retrieval Accuracy: {success_count}/{total_count} ({accuracy:.1f}%)"
    )
    print(f"Average Query Time: {np.mean(query_times) * 1000:.1f}ms")
    print(f"Model Load Time: {load_time:.2f}s")
    print(f"Document Embedding Time: {embed_time:.2f}s ({len(all_docs)} docs)")

    # Detailed results by language pair
    print("\n--- Results by Query Language ---")
    en_queries = [r for r in results if not any(ord(c) > 127 for c in r["query"])]
    ko_queries = [r for r in results if any(ord(c) > 127 for c in r["query"])]

    en_success = sum(1 for r in en_queries if r["success"])
    ko_success = sum(1 for r in ko_queries if r["success"])

    print(
        f"English queries: {en_success}/{len(en_queries)} ({en_success / len(en_queries) * 100:.1f}%)"
    )
    print(
        f"Korean queries: {ko_success}/{len(ko_queries)} ({ko_success / len(ko_queries) * 100:.1f}%)"
    )

    # Cross-lingual similarity analysis
    print("\n--- Cross-lingual Similarity Analysis ---")
    print("Comparing same-meaning docs in different languages:")

    for i in range(5):
        sim = cosine_similarity(korean_embeddings[i], english_embeddings[i])
        print(f"  Doc {i + 1} (KO<->EN): {sim:.3f}")

    avg_cross_sim = np.mean(
        [
            cosine_similarity(korean_embeddings[i], english_embeddings[i])
            for i in range(5)
        ]
    )
    print(f"\nAverage cross-lingual similarity: {avg_cross_sim:.3f}")

    return accuracy >= 80  # Return True if accuracy is acceptable


if __name__ == "__main__":
    success = run_benchmark()
    sys.exit(0 if success else 1)
