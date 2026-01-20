"""
File Tracker for Incremental Sync

파일 변경 감지 유틸리티. mtime + content hash 하이브리드 방식으로
변경된 파일을 정확하게 식별합니다.
"""

import hashlib
import os
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Set


# ============================================================================
# Data Classes
# ============================================================================

@dataclass
class FileState:
    """파일 상태 정보"""
    relative_path: str       # 루트 기준 상대 경로
    mtime: float            # 수정 시간 (Unix timestamp)
    content_hash: str       # 콘텐츠 MD5 해시
    
    def to_dict(self) -> dict:
        """레지스트리 저장용 딕셔너리"""
        return {
            "mtime": self.mtime,
            "content_hash": self.content_hash,
            "last_synced": datetime.now().isoformat(),
        }


@dataclass
class ChangeSet:
    """파일 변경 분류 결과"""
    added: List[FileState]     # 새로 추가된 파일
    modified: List[FileState]  # 수정된 파일
    deleted: List[str]         # 삭제된 파일 (relative_path)
    unchanged: List[str]       # 변경 없는 파일 (relative_path)
    
    @property
    def has_changes(self) -> bool:
        return bool(self.added or self.modified or self.deleted)
    
    def __repr__(self) -> str:
        return (
            f"ChangeSet(added={len(self.added)}, modified={len(self.modified)}, "
            f"deleted={len(self.deleted)}, unchanged={len(self.unchanged)})"
        )


# ============================================================================
# File Tracker Class
# ============================================================================

class FileTracker:
    """
    파일 변경 감지 유틸리티.
    
    mtime(수정시간)과 content_hash(콘텐츠 해시)를 조합한 하이브리드 방식:
    1. mtime이 같으면 → 변경 없음 (빠른 스킵)
    2. mtime이 다르면 → 해시 비교로 실제 변경 확인
    
    사용법:
        tracker = FileTracker()
        file_state = tracker.get_file_state(path, root)
        changes = tracker.detect_changes(current_files, registry_data)
    """
    
    @staticmethod
    def compute_file_hash(file_path: Path) -> str:
        """
        파일 콘텐츠의 MD5 해시 계산.
        
        Args:
            file_path: 해시를 계산할 파일 경로
        
        Returns:
            MD5 해시 문자열 (32자)
        """
        hasher = hashlib.md5()
        with open(file_path, "rb") as f:
            # 대용량 파일 대비 청크 단위 읽기
            for chunk in iter(lambda: f.read(8192), b""):
                hasher.update(chunk)
        return hasher.hexdigest()
    
    @staticmethod
    def get_file_mtime(file_path: Path) -> float:
        """파일 수정 시간(mtime) 반환"""
        return os.path.getmtime(file_path)
    
    def get_file_state(self, file_path: Path, root_path: Path) -> FileState:
        """
        파일의 현재 상태(mtime, hash) 수집.
        
        Args:
            file_path: 파일 절대 경로
            root_path: 루트 폴더 경로
        
        Returns:
            FileState 객체
        """
        relative_path = str(file_path.relative_to(root_path))
        mtime = self.get_file_mtime(file_path)
        content_hash = self.compute_file_hash(file_path)
        
        return FileState(
            relative_path=relative_path,
            mtime=mtime,
            content_hash=content_hash,
        )
    
    def detect_changes(
        self,
        current_files: List[FileState],
        registry_files: dict,
    ) -> ChangeSet:
        """
        현재 파일 목록과 레지스트리를 비교하여 변경 사항 탐지.
        
        Args:
            current_files: 현재 스캔된 파일 상태 목록
            registry_files: 레지스트리의 files 딕셔너리
                           {"relative_path": {"mtime": ..., "content_hash": ...}, ...}
        
        Returns:
            ChangeSet 객체 (added, modified, deleted, unchanged)
        """
        added: List[FileState] = []
        modified: List[FileState] = []
        unchanged: List[str] = []
        
        # 현재 파일 경로 집합
        current_paths: Set[str] = {f.relative_path for f in current_files}
        # 레지스트리 파일 경로 집합
        registry_paths: Set[str] = set(registry_files.keys())
        
        # 삭제된 파일: 레지스트리에 있지만 현재 없음
        deleted = list(registry_paths - current_paths)
        
        # 각 현재 파일 분류
        for file_state in current_files:
            path = file_state.relative_path
            
            if path not in registry_files:
                # 새 파일
                added.append(file_state)
            else:
                # 기존 파일 → 변경 여부 확인
                reg_info = registry_files[path]
                
                # 하이브리드 비교: mtime 먼저, 다르면 hash 비교
                if file_state.mtime == reg_info.get("mtime"):
                    # mtime 동일 → 변경 없음 (빠른 경로)
                    unchanged.append(path)
                elif file_state.content_hash == reg_info.get("content_hash"):
                    # mtime은 다르지만 hash 동일 → 실제 내용 변경 없음
                    # (touch만 된 경우 등)
                    unchanged.append(path)
                else:
                    # 실제 변경됨
                    modified.append(file_state)
        
        return ChangeSet(
            added=added,
            modified=modified,
            deleted=deleted,
            unchanged=unchanged,
        )


# ============================================================================
# Convenience Functions
# ============================================================================

def compute_file_hash(file_path: Path) -> str:
    """파일 해시 계산 편의 함수"""
    return FileTracker.compute_file_hash(file_path)


def get_file_state(file_path: Path, root_path: Path) -> FileState:
    """파일 상태 수집 편의 함수"""
    tracker = FileTracker()
    return tracker.get_file_state(file_path, root_path)
