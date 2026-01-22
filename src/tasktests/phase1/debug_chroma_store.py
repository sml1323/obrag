"""
ChromaStore 디버깅용 스크립트
"""

import sys
import tempfile
from pathlib import Path

# 프로젝트 루트를 path에 추가
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

from core.embedding import FakeEmbedder
from core.preprocessing import process_markdown_file, semantic_chunk
from core.sync import scan_and_process_folder
from db.chroma_store import (
    ChromaStore,
    create_store,
    search_chunks,
    store_chunks,
)


def main():
    # 임시 디렉토리에 ChromaDB 저장 (테스트용)
    with tempfile.TemporaryDirectory() as temp_dir:
        print(f"📂 임시 저장 경로: {temp_dir}")
        print("=" * 60)
        print()

        # FakeEmbedder 사용 (API 호출 없이 테스트)
        embedder = FakeEmbedder(dimension=1536)

        # ========================================
        # 1. ChromaStore 생성
        # ========================================
        print("🔧 [1] ChromaStore 생성")
        print("-" * 40)

        store = ChromaStore(  # 👈 여기에 breakpoint!
            persist_path=temp_dir,
            collection_name="debug_collection",
            embedder=embedder,
        )

        stats = store.get_stats()
        print(f"  컬렉션 이름: {stats['name']}")
        print(f"  저장 경로: {stats['persist_path']}")
        print(f"  임베더: {stats['embedder']}")
        print(f"  초기 청크 수: {stats['count']}")
        print()

        # ========================================
        # 2. 테스트 청크 준비
        # ========================================
        print("📄 [2] 테스트 청크 준비")
        print("-" * 40)

        test_file = project_root / "src" / "test" / "Transformer models.md"
        if test_file.exists():
            chunks = process_markdown_file(test_file)  # 👈 여기에 breakpoint!
            print(f"  파일: {test_file.name}")
            print(f"  청크 개수: {len(chunks)}")
        else:
            # 파일이 없으면 더미 청크 생성
            from dataclasses import dataclass

            @dataclass
            class DummyChunk:
                text: str
                metadata: dict

            chunks = [
                DummyChunk(
                    text="Transformer는 self-attention 메커니즘을 사용하는 딥러닝 모델입니다.",
                    metadata={"source": "dummy.md", "header_path": "Transformer > 개요"},
                ),
                DummyChunk(
                    text="BERT는 Bidirectional Encoder Representations from Transformers입니다.",
                    metadata={"source": "dummy.md", "header_path": "BERT > 소개"},
                ),
                DummyChunk(
                    text="GPT는 Generative Pre-trained Transformer의 약자입니다.",
                    metadata={"source": "dummy.md", "header_path": "GPT > 개요"},
                ),
            ]
            print("  (테스트 파일 없음, 더미 청크 사용)")
            print(f"  더미 청크 개수: {len(chunks)}")

        print()

        # ========================================
        # 3. 청크 저장 (upsert_chunks)
        # ========================================
        print("💾 [3] 청크 저장 (upsert_chunks)")
        print("-" * 40)

        # upsert_chunks는 메타데이터 정규화를 수행함
        source_name = chunks[0].metadata.get("source", "test.md") if chunks else "test.md"
        added_count = store.upsert_chunks(chunks, source_name)  # 👈 여기에 breakpoint!

        print(f"  저장된 청크 수: {added_count}")
        print(f"  현재 총 청크 수: {store.get_stats()['count']}")
        print()

        # ========================================
        # 4. 쿼리 테스트
        # ========================================
        print("🔍 [4] 쿼리 테스트")
        print("-" * 40)

        query_text = "Transformer attention mechanism"
        results = store.query(query_text, n_results=3)  # 👈 여기에 breakpoint!

        print(f"  쿼리: \"{query_text}\"")
        print(f"  결과 수: {len(results)}")
        print()

        for i, result in enumerate(results):
            print(f"  === 결과 {i + 1} ===")
            print(f"  📍 ID: {result['id']}")
            print(f"  📏 Distance: {result['distance']:.4f}")
            header_path = result['metadata'].get('header_path', 'N/A')
            print(f"  🏷️ Header Path: {header_path}")
            preview = result['text'][:80].replace("\n", " ")
            print(f"  📝 미리보기: {preview}...")
            print()

        # ========================================
        # 5. Deterministic ID 생성 테스트
        # ========================================
        print("🔑 [5] Deterministic ID 생성 테스트")
        print("-" * 40)

        test_path = "notes/test.md"
        for idx in range(3):
            chunk_id = ChromaStore.generate_deterministic_id(test_path, idx)  # 👈 여기에 breakpoint!
            print(f"  [{idx}] {chunk_id}")
        print()

        # ========================================
        # 6. Upsert 테스트
        # ========================================
        print("🔄 [6] Upsert 테스트")
        print("-" * 40)

        # 새 store 생성 (upsert 테스트용)
        upsert_store = ChromaStore(
            persist_path=temp_dir,
            collection_name="upsert_test",
            embedder=embedder,
        )

        relative_path = "notes/upsert_test.md"

        # 첫 번째 upsert
        from dataclasses import dataclass

        @dataclass
        class TestChunk:
            text: str
            metadata: dict

        initial_chunks = [
            TestChunk(text="Original content 1", metadata={"relative_path": relative_path}),
            TestChunk(text="Original content 2", metadata={"relative_path": relative_path}),
        ]

        count1 = upsert_store.upsert_chunks(initial_chunks, relative_path)  # 👈 여기에 breakpoint!
        print(f"  첫 번째 upsert: {count1}개 청크")
        print(f"  현재 총 청크 수: {upsert_store.get_stats()['count']}")

        # 두 번째 upsert (수정된 내용)
        updated_chunks = [
            TestChunk(text="UPDATED content 1", metadata={"relative_path": relative_path}),
            TestChunk(text="UPDATED content 2", metadata={"relative_path": relative_path}),
        ]

        count2 = upsert_store.upsert_chunks(updated_chunks, relative_path)  # 👈 여기에 breakpoint!
        print(f"  두 번째 upsert: {count2}개 청크")
        print(f"  현재 총 청크 수: {upsert_store.get_stats()['count']} (변화 없어야 함)")
        print()

        # ========================================
        # 7. 메타데이터 정규화 테스트
        # ========================================
        print("📋 [7] 메타데이터 정규화 테스트")
        print("-" * 40)

        test_metadata = {
            "source": "test.md",
            "tags": ["python", "ml"],  # 리스트
            "frontmatter": {"author": "test"},  # 딕셔너리
            "count": 42,  # int
            "score": 0.95,  # float
            "active": True,  # bool
        }

        normalized = ChromaStore._normalize_metadata(test_metadata)  # 👈 여기에 breakpoint!

        print("  원본 메타데이터:")
        for k, v in test_metadata.items():
            print(f"    {k}: {v} ({type(v).__name__})")

        print()
        print("  정규화된 메타데이터:")
        for k, v in normalized.items():
            print(f"    {k}: {v} ({type(v).__name__})")
        print()

        # ========================================
        # 8. 청크 삭제 테스트
        # ========================================
        print("🗑️ [8] 청크 삭제 테스트")
        print("-" * 40)

        before_count = upsert_store.get_stats()['count']
        print(f"  삭제 전 청크 수: {before_count}")

        upsert_store.delete_chunks_by_prefix(relative_path, from_index=1)  # 👈 여기에 breakpoint!

        after_count = upsert_store.get_stats()['count']
        print(f"  삭제 후 청크 수: {after_count}")
        print()

        # ========================================
        # 9. clear 테스트
        # ========================================
        print("🧹 [9] Clear 테스트")
        print("-" * 40)

        print(f"  Clear 전 청크 수: {store.get_stats()['count']}")
        store.clear()  # 👈 여기에 breakpoint!
        print(f"  Clear 후 청크 수: {store.get_stats()['count']}")
        print()

        # ========================================
        # 10. 편의 함수 테스트
        # ========================================
        print("🚀 [10] 편의 함수 테스트")
        print("-" * 40)

        # create_store
        new_store = create_store(  # 👈 여기에 breakpoint!
            persist_path=temp_dir,
            collection_name="convenience_test",
            embedder=embedder,
        )
        print(f"  create_store: {new_store}")

        # store_chunks (add_chunks 사용하므로 upsert로 대체)
        if chunks:
            new_store.upsert_chunks(chunks[:2], "convenience_test.md")
            print(f"  upsert_chunks: 2개 저장됨")

        # search_chunks
        search_results = search_chunks(
            "transformer",
            n_results=2,
            persist_path=temp_dir,
            collection_name="convenience_test",
            embedder=embedder,
        )
        print(f"  search_chunks: {len(search_results)}개 결과")
        print()

        print("✅ 디버깅 완료!")


if __name__ == "__main__":
    main()
