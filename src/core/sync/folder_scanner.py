"""
Folder Scanner for RAG

지정된 폴더를 재귀적으로 탐색하여 마크다운 파일을 수집하고
폴더 경로와 파일명을 메타데이터로 추출하는 모듈.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Set

from ..preprocessing import Chunk, process_markdown_file, semantic_chunk


# ============================================================================
# Constants
# ============================================================================

# 기본적으로 제외할 폴더 패턴
DEFAULT_IGNORE_PATTERNS: Set[str] = {
    ".obsidian",
    ".git",
    ".trash",
    ".github",
    "__pycache__",
    "node_modules",
    ".venv",
    "venv",
}


# ============================================================================
# Data Classes
# ============================================================================

@dataclass
class ScannedFile:
    """스캔된 파일 정보"""
    full_path: Path          # 절대 경로
    relative_path: Path      # root 기준 상대 경로
    filename: str            # 파일명 (확장자 포함)
    folder_path: str         # 상위 폴더 경로 (상대, / 구분자)
    
    def to_metadata(self) -> dict:
        """Chunk 메타데이터용 딕셔너리 변환"""
        return {
            "source": self.filename,
            "folder_path": self.folder_path,
            "relative_path": str(self.relative_path),
        }


# ============================================================================
# Folder Scanner Class
# ============================================================================

class FolderScanner:
    """
    폴더 재귀 스캔 및 마크다운 파일 수집.
    
    사용법:
        scanner = FolderScanner("/path/to/obsidian/vault")
        files = scanner.scan()
        chunks = scanner.scan_and_process()
    """
    
    def __init__(
        self,
        root_path: str | Path,
        ignore_patterns: Optional[Set[str]] = None,
        extensions: Optional[List[str]] = None,
    ):
        """
        Args:
            root_path: 스캔할 루트 폴더 경로
            ignore_patterns: 제외할 폴더명 패턴 (기본값: .obsidian, .git 등)
            extensions: 스캔할 파일 확장자 목록 (기본값: [".md"])
        """
        self.root_path = Path(root_path).resolve()
        self.ignore_patterns = ignore_patterns or DEFAULT_IGNORE_PATTERNS
        self.extensions = extensions or [".md"]
        
        if not self.root_path.exists():
            raise FileNotFoundError(f"Root path does not exist: {self.root_path}")
        if not self.root_path.is_dir():
            raise NotADirectoryError(f"Root path is not a directory: {self.root_path}")
    
    def _should_ignore(self, path: Path) -> bool:
        """경로가 무시 패턴에 해당하는지 확인"""
        for part in path.parts:
            if part in self.ignore_patterns:
                return True
            # 숨김 폴더 (.으로 시작) 제외 - 단, .md 파일은 허용
            if part.startswith(".") and part not in self.ignore_patterns:
                # 파일이 아닌 폴더인 경우만 제외
                if not path.is_file():
                    return True
        return False
    
    def scan(self) -> List[ScannedFile]:
        """
        재귀적으로 폴더를 스캔하여 대상 파일 목록 반환.
        
        Returns:
            ScannedFile 객체 리스트
        """
        scanned_files: List[ScannedFile] = []
        
        for ext in self.extensions:
            # 확장자 앞에 *가 없으면 추가
            pattern = f"*{ext}" if not ext.startswith("*") else ext
            
            for file_path in self.root_path.rglob(pattern):
                # 상대 경로 계산
                relative_path = file_path.relative_to(self.root_path)
                
                # 무시 패턴 체크
                if self._should_ignore(relative_path):
                    continue
                
                # 폴더 경로 추출 (파일 제외)
                folder_path = str(relative_path.parent)
                if folder_path == ".":
                    folder_path = ""
                
                scanned_file = ScannedFile(
                    full_path=file_path,
                    relative_path=relative_path,
                    filename=file_path.name,
                    folder_path=folder_path,
                )
                scanned_files.append(scanned_file)
        
        # 정렬: 폴더 경로 -> 파일명 순
        scanned_files.sort(key=lambda f: (f.folder_path, f.filename))
        
        return scanned_files
    
    def scan_and_process(
        self,
        min_chunk_size: int = 200,
        max_chunk_size: int = 1500,
        chunk_level: int = 2,
    ) -> List[Chunk]:
        """
        스캔된 파일들을 읽어서 청크로 변환.
        
        Args:
            min_chunk_size: 최소 청크 크기
            max_chunk_size: 최대 청크 크기
            chunk_level: 청킹 기준 헤더 레벨 (기본 ## = 2)
        
        Returns:
            모든 파일의 Chunk 리스트
        """
        scanned_files = self.scan()
        all_chunks: List[Chunk] = []
        
        for scanned_file in scanned_files:
            try:
                # 파일 읽기
                text = scanned_file.full_path.read_text(encoding="utf-8")
                
                # 청킹 수행
                chunks = semantic_chunk(
                    text=text,
                    source=scanned_file.filename,
                    extra_metadata=scanned_file.to_metadata(),
                    min_size=min_chunk_size,
                    max_size=max_chunk_size,
                    chunk_level=chunk_level,
                )
                
                all_chunks.extend(chunks)
                
            except Exception as e:
                # 파일 처리 실패 시 로깅하고 계속 진행
                print(f"Warning: Failed to process {scanned_file.full_path}: {e}")
                continue
        
        return all_chunks
    
    def __repr__(self) -> str:
        return f"FolderScanner(root_path={self.root_path}, extensions={self.extensions})"


# ============================================================================
# Convenience Functions
# ============================================================================

def scan_folder(
    root_path: str | Path,
    ignore_patterns: Optional[Set[str]] = None,
) -> List[ScannedFile]:
    """
    폴더를 스캔하여 마크다운 파일 목록 반환.
    
    Args:
        root_path: 스캔할 폴더 경로
        ignore_patterns: 제외할 폴더 패턴
    
    Returns:
        ScannedFile 리스트
    """
    scanner = FolderScanner(root_path, ignore_patterns)
    return scanner.scan()


def scan_and_process_folder(
    root_path: str | Path,
    ignore_patterns: Optional[Set[str]] = None,
    **chunk_options,
) -> List[Chunk]:
    """
    폴더를 스캔하고 모든 마크다운 파일을 청크로 변환.
    
    Args:
        root_path: 스캔할 폴더 경로
        ignore_patterns: 제외할 폴더 패턴
        **chunk_options: semantic_chunk에 전달할 옵션
    
    Returns:
        모든 파일의 Chunk 리스트
    """
    scanner = FolderScanner(root_path, ignore_patterns)
    return scanner.scan_and_process(**chunk_options)
