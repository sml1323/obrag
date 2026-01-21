"""
Folder Scanner 디버깅용 스크립트

note/ 폴더를 대상으로 FolderScanner의 각 단계를 디버깅합니다.
breakpoint를 걸어서 단계별로 확인하세요. 👈
"""

import sys
from pathlib import Path

# 프로젝트 루트를 path에 추가
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

from core.sync.folder_scanner import (
    DEFAULT_IGNORE_PATTERNS,
    FolderScanner,
    ScannedFile,
    scan_and_process_folder,
    scan_folder,
)


def main():
    # 테스트 폴더 경로 (note 폴더)
    test_folder = project_root / "note"

    print(f"📁 스캔 대상 폴더: {test_folder}")
    print(f"📍 폴더 존재 여부: {test_folder.exists()}")
    print("=" * 60)
    print()

    # ========================================
    # 1. FolderScanner 인스턴스 생성
    # ========================================
    print("🔧 [1] FolderScanner 인스턴스 생성")
    print("-" * 40)

    scanner = FolderScanner(test_folder)  # 👈 여기에 breakpoint!

    print(f"  root_path: {scanner.root_path}")
    print(f"  extensions: {scanner.extensions}")
    print(f"  ignore_patterns: {scanner.ignore_patterns}")
    print()

    # ========================================
    # 2. 폴더 스캔 (파일 목록 수집)
    # ========================================
    print("🔍 [2] 폴더 스캔 (scan)")
    print("-" * 40)

    scanned_files = scanner.scan()  # 👈 여기에 breakpoint!

    print(f"  발견된 파일 수: {len(scanned_files)}")
    print()

    # 파일 목록 출력 (최대 10개)
    print("  📄 스캔된 파일 목록:")
    for i, sf in enumerate(scanned_files[:10]):
        print(f"    [{i + 1}] {sf.filename}")
        print(f"        폴더: {sf.folder_path or '(루트)'}")
        print(f"        상대경로: {sf.relative_path}")

    if len(scanned_files) > 10:
        print(f"    ... 외 {len(scanned_files) - 10}개 파일")
    print()

    # ========================================
    # 3. ScannedFile 메타데이터 확인
    # ========================================
    if scanned_files:
        print("📋 [3] ScannedFile 메타데이터 변환")
        print("-" * 40)

        first_file = scanned_files[0]  # 👈 여기에 breakpoint!
        metadata = first_file.to_metadata()

        print(f"  대상 파일: {first_file.filename}")
        print("  메타데이터: ")
        for key, value in metadata.items():
            print(f"    {key}: {value}")
        print()

    # ========================================
    # 4. 무시 패턴 테스트
    # ========================================
    print("🚫 [4] 무시 패턴 확인")
    print("-" * 40)

    print(f"  기본 무시 패턴: {DEFAULT_IGNORE_PATTERNS}")

    # 무시되는 경로 테스트
    test_paths = [
        Path(".obsidian/plugins/test.md"),
        Path(".git/config.md"),
        Path("normal/folder/test.md"),
        Path(".hidden/secret.md"),
    ]

    print()
    print("  패턴 테스트 결과:")
    for test_path in test_paths:
        ignored = scanner._should_ignore(test_path)  # 👈 여기에 breakpoint!
        status = "❌ 제외됨" if ignored else "✅ 포함됨"
        print(f"    {test_path}: {status}")
    print()

    # ========================================
    # 5. scan_and_process 실행 (청킹 포함)
    # ========================================
    print("✂️ [5] scan_and_process (스캔 + 청킹)")
    print("-" * 40)

    chunks = scanner.scan_and_process(
        min_chunk_size=200,
        max_chunk_size=1500,
        chunk_level=2,
    )  # 👈 여기에 breakpoint!

    print(f"  총 청크 수: {len(chunks)}")
    print()

    # 청크 상세 출력 (최대 5개)
    for i, chunk in enumerate(chunks[:5]):
        print(f"  === Chunk {i + 1} ===")
        print(f"  📄 Source: {chunk.metadata.get('source', 'N/A')}")
        print(f"  📁 Folder: {chunk.metadata.get('folder_path', 'N/A')}")
        print(f"  📍 Path: {chunk.metadata.get('header_path', 'N/A')}")
        print(f"  📏 길이: {len(chunk.text)} 문자")

        # 텍스트 미리보기 (처음 80자)
        preview = chunk.text[:80].replace("\n", " ")
        print(f"  📝 미리보기: {preview}...")
        print()

        if i >= 4:
            print(f"  ... 외 {len(chunks) - 5}개 청크")
            break

    # ========================================
    # 6. 편의 함수 테스트
    # ========================================
    print()
    print("🔧 [6] 편의 함수 테스트")
    print("-" * 40)

    # scan_folder 함수
    files_from_func = scan_folder(test_folder)  # 👈 여기에 breakpoint!
    print(f"  scan_folder() 결과: {len(files_from_func)}개 파일")

    # scan_and_process_folder 함수
    chunks_from_func = scan_and_process_folder(test_folder)  # 👈 여기에 breakpoint!
    print(f"  scan_and_process_folder() 결과: {len(chunks_from_func)}개 청크")
    print()

    # ========================================
    # 7. 폴더 구조 분석
    # ========================================
    print("📊 [7] 폴더 구조 분석")
    print("-" * 40)

    # 폴더별 파일 수 집계
    folder_counts: dict[str, int] = {}
    for sf in scanned_files:
        folder = sf.folder_path or "(루트)"
        folder_counts[folder] = folder_counts.get(folder, 0) + 1

    print("  폴더별 파일 수:")
    for folder, count in sorted(folder_counts.items()):
        print(f"    {folder}: {count}개")
    print()

    print("✅ 디버깅 완료!")


if __name__ == "__main__":
    main()
