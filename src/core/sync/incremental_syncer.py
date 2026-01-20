"""
Incremental Syncer for RAG

메인 증분 동기화 클래스. 폴더를 스캔하여 변경된 파일만
ChromaDB에 업데이트합니다.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

from .file_tracker import ChangeSet, FileState, FileTracker
from .folder_scanner import FolderScanner, ScannedFile
from .sync_registry import SyncRegistry
from ..preprocessing import Chunk, semantic_chunk


# ============================================================================
# Data Classes
# ============================================================================

@dataclass
class SyncResult:
    """동기화 결과 요약"""
    added: int = 0        # 새로 추가된 파일 수
    modified: int = 0     # 수정된 파일 수
    deleted: int = 0      # 삭제된 파일 수
    skipped: int = 0      # 변경 없어 스킵된 파일 수
    total_chunks: int = 0 # 처리된 총 청크 수
    errors: List[str] = field(default_factory=list)
    
    @property
    def has_changes(self) -> bool:
        return self.added > 0 or self.modified > 0 or self.deleted > 0
    
    def __repr__(self) -> str:
        return (
            f"SyncResult(added={self.added}, modified={self.modified}, "
            f"deleted={self.deleted}, skipped={self.skipped}, "
            f"chunks={self.total_chunks}, errors={len(self.errors)})"
        )


# ============================================================================
# IncrementalSyncer Class
# ============================================================================

class IncrementalSyncer:
    """
    증분 동기화 엔진.
    
    폴더를 스캔하여 변경된 파일만 ChromaDB에 업데이트합니다.
    
    동작 플로우:
        1. 현재 파일 목록 스캔 (FolderScanner)
        2. 레지스트리와 비교 → added, modified, deleted 분류 (FileTracker)
        3. 각 카테고리별 처리:
           - added: 청킹 → upsert
           - modified: 청킹 → upsert + 초과 청크 삭제
           - deleted: 청크 삭제
        4. 레지스트리 업데이트 (SyncRegistry)
    
    사용법:
        syncer = IncrementalSyncer(
            folder_scanner=FolderScanner(root_path),
            chroma_store=ChromaStore(),
            registry=SyncRegistry(registry_path),
        )
        result = syncer.sync()
    """
    
    def __init__(
        self,
        folder_scanner: FolderScanner,
        chroma_store,  # ChromaStore - 순환 import 방지
        registry: SyncRegistry,
        min_chunk_size: int = 200,
        max_chunk_size: int = 1500,
        chunk_level: int = 2,
    ):
        """
        Args:
            folder_scanner: 폴더 스캐너 인스턴스
            chroma_store: ChromaStore 인스턴스
            registry: 동기화 레지스트리
            min_chunk_size: 최소 청크 크기
            max_chunk_size: 최대 청크 크기
            chunk_level: 청킹 기준 헤더 레벨
        """
        self.folder_scanner = folder_scanner
        self.chroma_store = chroma_store
        self.registry = registry
        
        self.min_chunk_size = min_chunk_size
        self.max_chunk_size = max_chunk_size
        self.chunk_level = chunk_level
        
        self._file_tracker = FileTracker()
    
    def sync(self) -> SyncResult:
        """
        증분 동기화 수행.
        
        Returns:
            SyncResult 객체
        """
        result = SyncResult()
        
        # 1. 현재 파일 스캔
        scanned_files = self.folder_scanner.scan()
        
        # 2. 각 파일의 상태(mtime, hash) 수집
        current_states: List[FileState] = []
        file_map: dict[str, ScannedFile] = {}  # relative_path -> ScannedFile
        
        for scanned_file in scanned_files:
            try:
                state = self._file_tracker.get_file_state(
                    scanned_file.full_path,
                    self.folder_scanner.root_path,
                )
                current_states.append(state)
                file_map[state.relative_path] = scanned_file
            except Exception as e:
                result.errors.append(f"Failed to get state for {scanned_file.relative_path}: {e}")
        
        # 3. 레지스트리와 비교
        changes = self._file_tracker.detect_changes(
            current_states,
            self.registry.files,
        )
        
        # 4. 변경 처리
        # 4a. 새 파일 처리
        for file_state in changes.added:
            try:
                chunk_count = self._process_file(file_state, file_map[file_state.relative_path])
                result.added += 1
                result.total_chunks += chunk_count
            except Exception as e:
                result.errors.append(f"Failed to add {file_state.relative_path}: {e}")
        
        # 4b. 수정된 파일 처리
        for file_state in changes.modified:
            try:
                chunk_count = self._process_file(file_state, file_map[file_state.relative_path])
                # 기존 청크 수보다 새 청크 수가 적으면 초과 청크 삭제
                old_info = self.registry.get_file_info(file_state.relative_path)
                if old_info and old_info.get("chunk_count", 0) > chunk_count:
                    self.chroma_store.delete_chunks_by_prefix(
                        file_state.relative_path,
                        chunk_count,
                    )
                result.modified += 1
                result.total_chunks += chunk_count
            except Exception as e:
                result.errors.append(f"Failed to modify {file_state.relative_path}: {e}")
        
        # 4c. 삭제된 파일 처리
        for relative_path in changes.deleted:
            try:
                self.chroma_store.delete_by_relative_path(relative_path)
                self.registry.remove_file_info(relative_path)
                result.deleted += 1
            except Exception as e:
                result.errors.append(f"Failed to delete {relative_path}: {e}")
        
        # 4d. 변경 없는 파일 카운트
        result.skipped = len(changes.unchanged)
        
        # 5. 레지스트리 저장
        self.registry.save()
        
        return result
    
    def _process_file(self, file_state: FileState, scanned_file: ScannedFile) -> int:
        """
        단일 파일 처리 (청킹 → upsert → 레지스트리 업데이트).
        
        Args:
            file_state: 파일 상태
            scanned_file: 스캔된 파일 정보
        
        Returns:
            처리된 청크 수
        """
        # 파일 읽기
        text = scanned_file.full_path.read_text(encoding="utf-8")
        
        # 청킹
        chunks = semantic_chunk(
            text=text,
            source=scanned_file.filename,
            extra_metadata=scanned_file.to_metadata(),
            min_size=self.min_chunk_size,
            max_size=self.max_chunk_size,
            chunk_level=self.chunk_level,
        )
        
        # ChromaDB upsert
        chunk_count = self.chroma_store.upsert_chunks(
            chunks,
            file_state.relative_path,
        )
        
        # 레지스트리 업데이트
        self.registry.update_file_info(
            relative_path=file_state.relative_path,
            content_hash=file_state.content_hash,
            mtime=file_state.mtime,
            chunk_count=chunk_count,
        )
        
        return chunk_count
    
    def full_sync(self) -> SyncResult:
        """
        전체 재동기화 (레지스트리 초기화 후 sync).
        
        Returns:
            SyncResult 객체
        """
        # 레지스트리 초기화
        self.registry.clear()
        
        # ChromaDB 클리어
        self.chroma_store.clear()
        
        # 동기화 수행
        return self.sync()
    
    def __repr__(self) -> str:
        return (
            f"IncrementalSyncer(root={self.folder_scanner.root_path}, "
            f"registry_files={len(self.registry)})"
        )


# ============================================================================
# Convenience Functions
# ============================================================================

def create_syncer(
    root_path: str | Path,
    chroma_store,
    registry_path: Optional[str | Path] = None,
    **chunk_options,
) -> IncrementalSyncer:
    """
    IncrementalSyncer 생성 편의 함수.
    
    Args:
        root_path: 스캔할 폴더 경로
        chroma_store: ChromaStore 인스턴스
        registry_path: 레지스트리 파일 경로 (기본: root_path/.sync_registry.json)
        **chunk_options: 청킹 옵션
    
    Returns:
        IncrementalSyncer 인스턴스
    """
    root = Path(root_path).resolve()
    
    # 기본 레지스트리 경로
    if registry_path is None:
        registry_path = root / ".sync_registry.json"
    
    folder_scanner = FolderScanner(root)
    registry = SyncRegistry(registry_path)
    
    return IncrementalSyncer(
        folder_scanner=folder_scanner,
        chroma_store=chroma_store,
        registry=registry,
        **chunk_options,
    )
