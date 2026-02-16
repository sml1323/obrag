"""
Sync Registry for Incremental Sync

동기화 상태 저장소. JSON 파일 기반으로 각 파일의 동기화 상태를 추적합니다.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Optional


# ============================================================================
# Registry Schema
# ============================================================================

REGISTRY_VERSION = 1

DEFAULT_REGISTRY = {
    "version": REGISTRY_VERSION,
    "files": {},
}


# ============================================================================
# SyncRegistry Class
# ============================================================================


class SyncRegistry:
    """
    동기화 상태 저장소 (JSON 파일 기반).

    각 파일의 mtime, content_hash, 청크 수, 마지막 동기화 시간 등을 저장합니다.

    레지스트리 스키마:
        {
            "version": 1,
            "files": {
                "folder/note.md": {
                    "content_hash": "abc123...",
                    "mtime": 1705678900.123,
                    "chunk_count": 3,
                    "last_synced": "2026-01-20T09:00:00"
                }
            }
        }

    사용법:
        registry = SyncRegistry(Path("./sync_registry.json"))
        registry.update_file_info("note.md", {"content_hash": "abc", "mtime": 123.0})
        info = registry.get_file_info("note.md")
        registry.save()
    """

    def __init__(self, registry_path: Path | str):
        """
        Args:
            registry_path: 레지스트리 JSON 파일 경로
        """
        self.registry_path = Path(registry_path)
        self._data: dict = self._load()

    def _load(self) -> dict:
        """레지스트리 파일 로드 (없으면 기본값 생성)"""
        if self.registry_path.exists():
            try:
                with open(self.registry_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                # 버전 체크 (향후 마이그레이션 대비)
                if data.get("version") != REGISTRY_VERSION:
                    # 버전 불일치 시 경고 (현재는 그냥 사용)
                    pass
                return data
            except (json.JSONDecodeError, IOError):
                # 파일 손상 시 기본값으로 초기화
                return {"version": REGISTRY_VERSION, "files": {}}
        else:
            return {"version": REGISTRY_VERSION, "files": {}}

    def save(self) -> None:
        """레지스트리를 파일에 저장"""
        # 부모 디렉토리 생성
        self.registry_path.parent.mkdir(parents=True, exist_ok=True)

        with open(self.registry_path, "w", encoding="utf-8") as f:
            json.dump(self._data, f, indent=2, ensure_ascii=False)

    @property
    def files(self) -> dict:
        """파일 정보 딕셔너리 반환"""
        return self._data.get("files", {})

    def get_file_info(self, relative_path: str) -> Optional[dict]:
        """
        특정 파일의 동기화 정보 조회.

        Args:
            relative_path: 루트 기준 상대 경로

        Returns:
            파일 정보 딕셔너리 또는 None
        """
        return self.files.get(relative_path)

    def update_file_info(
        self,
        relative_path: str,
        content_hash: str,
        mtime: float,
        chunk_count: int,
    ) -> None:
        """
        파일 동기화 정보 업데이트.

        Args:
            relative_path: 루트 기준 상대 경로
            content_hash: 콘텐츠 MD5 해시
            mtime: 수정 시간
            chunk_count: 저장된 청크 수
        """
        self._data["files"][relative_path] = {
            "content_hash": content_hash,
            "mtime": mtime,
            "chunk_count": chunk_count,
            "last_synced": datetime.now().isoformat(),
        }

    def remove_file_info(self, relative_path: str) -> bool:
        """
        파일 정보 삭제.

        Args:
            relative_path: 삭제할 파일 경로

        Returns:
            삭제 성공 여부
        """
        if relative_path in self._data["files"]:
            del self._data["files"][relative_path]
            return True
        return False

    def get_vault_path(self) -> Optional[str]:
        """마지막으로 동기화된 vault 경로 반환."""
        return self._data.get("vault_path")

    def set_vault_path(self, vault_path: str) -> None:
        """vault 경로 저장."""
        self._data["vault_path"] = vault_path

    def clear(self) -> None:
        """모든 파일 정보 초기화 (vault_path는 유지)."""
        vault_path = self._data.get("vault_path")
        self._data = {"version": REGISTRY_VERSION, "files": {}}
        if vault_path:
            self._data["vault_path"] = vault_path

    def get_all_paths(self) -> list[str]:
        """저장된 모든 파일 경로 반환"""
        return list(self.files.keys())

    def __len__(self) -> int:
        """저장된 파일 수"""
        return len(self.files)

    def __repr__(self) -> str:
        return f"SyncRegistry(path={self.registry_path}, files={len(self)})"


# ============================================================================
# Convenience Functions
# ============================================================================


def load_registry(registry_path: Path | str) -> SyncRegistry:
    """레지스트리 로드 편의 함수"""
    return SyncRegistry(registry_path)
