"""
Markdown Preprocessor 디버깅용 스크립트
"""

import sys
from pathlib import Path

# 프로젝트 루트를 path에 추가
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

from core.preprocessing import (
    extract_frontmatter,
    extract_header_marks,
    process_markdown_file,
    protect_code_blocks,
    semantic_chunk,
)


def main():
    # 테스트 파일 경로
    test_file = project_root / "src" / "test" / "Transformer models.md"

    print(f"📄 파일: {test_file}")
    print("=" * 60)

    # 파일 읽기
    text = test_file.read_text(encoding="utf-8")
    print(f"📏 전체 길이: {len(text)} 문자")
    print()

    # ========================================
    # 1. YAML Frontmatter 추출
    # ========================================
    print("🔍 [1] YAML Frontmatter 추출")
    print("-" * 40)

    frontmatter, body = extract_frontmatter(text)  # 👈 여기에 breakpoint!

    if frontmatter:
        print(f"  태그: {frontmatter.tags}")
        print(f"  생성일: {frontmatter.create_date}")
        print(f"  기타: {frontmatter.extra}")
    else:
        print("  (frontmatter 없음)")
    print()

    # ========================================
    # 2. 코드 블록 보호
    # ========================================
    print("🛡️ [2] 코드 블록 보호")
    print("-" * 40)

    protected, placeholders = protect_code_blocks(body)  # 👈 여기에 breakpoint!

    print(f"  코드 블록 개수: {len(placeholders)}")
    for i, (ph, original) in enumerate(placeholders[:3]):  # 처음 3개만 출력
        preview = original[:50].replace("\n", "\\n")
        print(f"    [{i}] {preview}...")
    if len(placeholders) > 3:
        print(f"    ... 외 {len(placeholders) - 3}개")
    print()

    # ========================================
    # 3. 헤더 추출
    # ========================================
    print("📑 [3] 헤더 추출 (breadcrumb 추적)")
    print("-" * 40)

    headers = extract_header_marks(body)  # 👈 여기에 breakpoint!

    print(f"  헤더 개수: {len(headers)}")
    for h in headers[:10]:  # 처음 10개만 출력
        indent = "  " * h.level
        path_str = " > ".join(h.path)
        print(f"  {indent}[L{h.level}] {h.title}")
        print(f"  {indent}      경로: {path_str}")
    if len(headers) > 10:
        print(f"  ... 외 {len(headers) - 10}개")
    print()

    # ========================================
    # 4. Semantic Chunking
    # ========================================
    print("✂️ [4] Semantic Chunking")
    print("-" * 40)

    chunks = semantic_chunk(
        text, source="Transformer models.md"
    )  # 👈 여기에 breakpoint!

    print(f"  청크 개수: {len(chunks)}")
    print()

    for i, chunk in enumerate(chunks):
        print(f"  === Chunk {i + 1} ===")
        print(f"  📍 Header Path: {chunk.metadata.get('header_path', 'N/A')}")
        print(f"  📏 길이: {len(chunk.text)} 문자")
        print(f"  🏷️ Headers: {chunk.metadata.get('headers', [])}")

        # 텍스트 미리보기 (처음 100자)
        preview = chunk.text[:100].replace("\n", " ")
        print(f"  📝 미리보기: {preview}...")
        print()

        # 처음 5개만 상세 출력
        if i >= 4:
            print(f"  ... 외 {len(chunks) - 5}개 청크")
            break

    # ========================================
    # 5. 전체 파일 처리 (한 번에)
    # ========================================
    print()
    print("🚀 [5] process_markdown_file() 실행")
    print("-" * 40)

    all_chunks = process_markdown_file(test_file)  # 👈 여기에 breakpoint!

    print(f"  최종 청크 개수: {len(all_chunks)}")
    print()

    # frontmatter 메타데이터 확인
    if all_chunks and "frontmatter" in all_chunks[0].metadata:
        fm = all_chunks[0].metadata["frontmatter"]
        print("  첫 번째 청크 frontmatter:")
        print(f"    태그: {fm.get('tags', [])}")
        print(f"    생성일: {fm.get('create_date', 'N/A')}")

    print()
    print("✅ 디버깅 완료!")


if __name__ == "__main__":
    main()
