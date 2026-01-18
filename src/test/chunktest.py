import os
from src.core.sync import FolderScanner, scan_and_process_folder

# 프로젝트 루트 기준의 테스트 경로 설정
test_vault_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../testdoc/note"))

print(f"--- Scanning path: {test_vault_path} ---\n")

# 방법 1: 클래스 사용
scanner = FolderScanner(test_vault_path)
chunks = scanner.scan_and_process()

# 청크 결과 출력 (첫 번째 청크만 예시로)
if chunks:
    print("Found chunks summary:")
    print(len(chunks), "dafsdffsdasdfsdfasd")
    for i, chunk in enumerate(chunks[:3]):  # 처음 3개만 출력
        print(f"Chunk {i+1} Metadata: {chunk.metadata}")
        print(f"Content snippet: {chunk.text[:100]}...")
        print("-" * 20)
else:
    print("No chunks found. Check if the directory contains markdown files.")



from src.core.sync import scan_and_process_folder

chunks = scan_and_process_folder("/Users/imseungmin/work/portfolio/obsidian_RAG/obrag/src/test")

for c in chunks[:1]:
    print(c.metadata)