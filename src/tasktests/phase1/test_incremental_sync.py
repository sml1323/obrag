"""
Incremental Sync 테스트

FileTracker, SyncRegistry, IncrementalSyncer에 대한 통합 테스트.
"""

import json
import os
import sys
import tempfile
import time
from pathlib import Path

# 프로젝트 루트를 path에 추가 (pytest import 전에 설정)
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

import pytest

from core.sync import (
    FileTracker,
    FileState,
    ChangeSet,
    SyncRegistry,
    FolderScanner,
    IncrementalSyncer,
    SyncResult,
)
from core.embedding import FakeEmbedder
from db import ChromaStore


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def temp_dir():
    """임시 디렉토리 생성"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_markdown_files(temp_dir):
    """샘플 마크다운 파일 생성"""
    # 파일 1
    file1 = temp_dir / "note1.md"
    file1.write_text("""---
title: Note 1
---

# Header 1

This is note 1 content.

## Section A

More content here.
""", encoding="utf-8")
    
    # 폴더 내 파일 2
    subfolder = temp_dir / "subfolder"
    subfolder.mkdir()
    file2 = subfolder / "note2.md"
    file2.write_text("""---
title: Note 2
tags: [test]
---

# Header 2

This is note 2 in subfolder.
""", encoding="utf-8")
    
    return {"file1": file1, "file2": file2, "root": temp_dir}


@pytest.fixture
def chroma_store(temp_dir):
    """테스트용 ChromaStore"""
    store = ChromaStore(
        persist_path=str(temp_dir / "test_chroma"),
        collection_name="test_sync",
        embedder=FakeEmbedder(),
    )
    yield store
    # Cleanup
    store.clear()


@pytest.fixture
def sync_registry(temp_dir):
    """테스트용 SyncRegistry"""
    registry_path = temp_dir / "sync_registry.json"
    return SyncRegistry(registry_path)


# ============================================================================
# FileTracker Tests
# ============================================================================

class TestFileTracker:
    """FileTracker 단위 테스트"""
    
    def test_compute_file_hash(self, temp_dir):
        """파일 해시 계산 테스트"""
        # Given
        test_file = temp_dir / "test.txt"
        test_file.write_text("Hello, World!", encoding="utf-8")
        
        # When
        hash1 = FileTracker.compute_file_hash(test_file)
        hash2 = FileTracker.compute_file_hash(test_file)
        
        # Then
        assert len(hash1) == 32  # MD5 해시 길이
        assert hash1 == hash2  # 동일 파일은 동일 해시
    
    def test_different_content_different_hash(self, temp_dir):
        """다른 내용은 다른 해시"""
        # Given
        file1 = temp_dir / "file1.txt"
        file2 = temp_dir / "file2.txt"
        file1.write_text("Content A", encoding="utf-8")
        file2.write_text("Content B", encoding="utf-8")
        
        # When
        hash1 = FileTracker.compute_file_hash(file1)
        hash2 = FileTracker.compute_file_hash(file2)
        
        # Then
        assert hash1 != hash2
    
    def test_get_file_state(self, sample_markdown_files):
        """파일 상태 수집 테스트"""
        # Given
        tracker = FileTracker()
        root = sample_markdown_files["root"]
        file1 = sample_markdown_files["file1"]
        
        # When
        state = tracker.get_file_state(file1, root)
        
        # Then
        assert state.relative_path == "note1.md"
        assert state.mtime > 0
        assert len(state.content_hash) == 32
    
    def test_detect_added_files(self):
        """새 파일 감지 테스트"""
        # Given
        tracker = FileTracker()
        current_files = [
            FileState("new_file.md", 100.0, "abc123"),
        ]
        registry_files = {}  # 빈 레지스트리
        
        # When
        changes = tracker.detect_changes(current_files, registry_files)
        
        # Then
        assert len(changes.added) == 1
        assert changes.added[0].relative_path == "new_file.md"
        assert len(changes.modified) == 0
        assert len(changes.deleted) == 0
    
    def test_detect_modified_files(self):
        """수정된 파일 감지 테스트"""
        # Given
        tracker = FileTracker()
        current_files = [
            FileState("note.md", 200.0, "new_hash"),  # mtime과 hash 모두 변경
        ]
        registry_files = {
            "note.md": {"mtime": 100.0, "content_hash": "old_hash"},
        }
        
        # When
        changes = tracker.detect_changes(current_files, registry_files)
        
        # Then
        assert len(changes.added) == 0
        assert len(changes.modified) == 1
        assert changes.modified[0].relative_path == "note.md"
    
    def test_detect_deleted_files(self):
        """삭제된 파일 감지 테스트"""
        # Given
        tracker = FileTracker()
        current_files = []  # 현재 파일 없음
        registry_files = {
            "deleted.md": {"mtime": 100.0, "content_hash": "old_hash"},
        }
        
        # When
        changes = tracker.detect_changes(current_files, registry_files)
        
        # Then
        assert len(changes.deleted) == 1
        assert "deleted.md" in changes.deleted
    
    def test_unchanged_files_with_same_mtime(self):
        """mtime 동일 → 변경 없음"""
        # Given
        tracker = FileTracker()
        current_files = [
            FileState("note.md", 100.0, "same_hash"),
        ]
        registry_files = {
            "note.md": {"mtime": 100.0, "content_hash": "same_hash"},
        }
        
        # When
        changes = tracker.detect_changes(current_files, registry_files)
        
        # Then
        assert len(changes.unchanged) == 1
        assert len(changes.modified) == 0
    
    def test_unchanged_files_with_different_mtime_but_same_hash(self):
        """mtime 다르지만 hash 동일 → 변경 없음 (touch만 된 경우)"""
        # Given
        tracker = FileTracker()
        current_files = [
            FileState("note.md", 200.0, "same_hash"),  # mtime만 다름
        ]
        registry_files = {
            "note.md": {"mtime": 100.0, "content_hash": "same_hash"},
        }
        
        # When
        changes = tracker.detect_changes(current_files, registry_files)
        
        # Then
        assert len(changes.unchanged) == 1
        assert len(changes.modified) == 0


# ============================================================================
# SyncRegistry Tests
# ============================================================================

class TestSyncRegistry:
    """SyncRegistry 단위 테스트"""
    
    def test_empty_registry(self, temp_dir):
        """빈 레지스트리 생성"""
        # Given
        registry = SyncRegistry(temp_dir / "new_registry.json")
        
        # Then
        assert len(registry) == 0
        assert registry.files == {}
    
    def test_save_and_load(self, temp_dir):
        """저장 및 로드 테스트"""
        # Given
        registry_path = temp_dir / "registry.json"
        registry1 = SyncRegistry(registry_path)
        registry1.update_file_info("note.md", "abc123", 100.0, 3)
        registry1.save()
        
        # When
        registry2 = SyncRegistry(registry_path)
        
        # Then
        assert len(registry2) == 1
        info = registry2.get_file_info("note.md")
        assert info["content_hash"] == "abc123"
        assert info["mtime"] == 100.0
        assert info["chunk_count"] == 3
    
    def test_update_file_info(self, sync_registry):
        """파일 정보 업데이트"""
        # When
        sync_registry.update_file_info("note.md", "hash123", 100.0, 5)
        
        # Then
        info = sync_registry.get_file_info("note.md")
        assert info is not None
        assert info["content_hash"] == "hash123"
        assert "last_synced" in info
    
    def test_remove_file_info(self, sync_registry):
        """파일 정보 삭제"""
        # Given
        sync_registry.update_file_info("note.md", "hash", 100.0, 1)
        
        # When
        result = sync_registry.remove_file_info("note.md")
        
        # Then
        assert result is True
        assert sync_registry.get_file_info("note.md") is None
    
    def test_clear(self, sync_registry):
        """전체 초기화"""
        # Given
        sync_registry.update_file_info("note1.md", "h1", 100.0, 1)
        sync_registry.update_file_info("note2.md", "h2", 200.0, 2)
        
        # When
        sync_registry.clear()
        
        # Then
        assert len(sync_registry) == 0


# ============================================================================
# IncrementalSyncer Integration Tests
# ============================================================================

class TestIncrementalSyncer:
    """IncrementalSyncer 통합 테스트"""
    
    @pytest.fixture
    def setup_sync_env(self, temp_dir):
        """동기화 환경 설정 - 동일한 temp_dir 사용"""
        # 샘플 파일 생성
        file1 = temp_dir / "note1.md"
        file1.write_text("""---
title: Note 1
---

# Header 1

This is note 1 content.

## Section A

More content here.
""", encoding="utf-8")
        
        subfolder = temp_dir / "subfolder"
        subfolder.mkdir()
        file2 = subfolder / "note2.md"
        file2.write_text("""---
title: Note 2
tags: [test]
---

# Header 2

This is note 2 in subfolder.
""", encoding="utf-8")
        
        # ChromaStore 생성
        store = ChromaStore(
            persist_path=str(temp_dir / "test_chroma"),
            collection_name="test_sync",
            embedder=FakeEmbedder(),
        )
        
        # Registry 생성
        registry = SyncRegistry(temp_dir / "sync_registry.json")
        
        yield {
            "root": temp_dir,
            "file1": file1,
            "file2": file2,
            "store": store,
            "registry": registry,
        }
        
        # Cleanup
        store.clear()
    
    def test_sync_new_files(self, setup_sync_env):
        """새 파일 동기화 테스트"""
        # Given
        env = setup_sync_env
        scanner = FolderScanner(env["root"])
        syncer = IncrementalSyncer(
            folder_scanner=scanner,
            chroma_store=env["store"],
            registry=env["registry"],
        )
        
        # When
        result = syncer.sync()
        
        # Then
        assert result.added == 2
        assert result.modified == 0
        assert result.deleted == 0
        assert result.total_chunks > 0
        assert len(result.errors) == 0
        
        # 레지스트리에 저장되었는지 확인
        assert len(env["registry"]) == 2
        assert env["registry"].get_file_info("note1.md") is not None
        assert env["registry"].get_file_info("subfolder/note2.md") is not None
    
    def test_sync_no_changes(self, setup_sync_env):
        """변경 없을 때 스킵 테스트"""
        # Given
        env = setup_sync_env
        scanner = FolderScanner(env["root"])
        syncer = IncrementalSyncer(
            folder_scanner=scanner,
            chroma_store=env["store"],
            registry=env["registry"],
        )
        
        # First sync
        syncer.sync()
        
        # When - Second sync without changes
        result = syncer.sync()
        
        # Then
        assert result.added == 0
        assert result.modified == 0
        assert result.deleted == 0
        assert result.skipped == 2
    
    def test_sync_modified_file(self, setup_sync_env):
        """수정된 파일 동기화 테스트"""
        # Given
        env = setup_sync_env
        scanner = FolderScanner(env["root"])
        syncer = IncrementalSyncer(
            folder_scanner=scanner,
            chroma_store=env["store"],
            registry=env["registry"],
        )
        
        # First sync
        syncer.sync()
        
        # Modify file
        time.sleep(0.1)  # mtime 변경을 위한 대기
        env["file1"].write_text("""---
title: Note 1 Modified
---

# Changed Header

Completely new content!
""", encoding="utf-8")
        
        # When
        result = syncer.sync()
        
        # Then
        assert result.modified == 1
        assert result.added == 0
        assert result.skipped == 1
    
    def test_sync_deleted_file(self, setup_sync_env):
        """삭제된 파일 동기화 테스트"""
        # Given
        env = setup_sync_env
        scanner = FolderScanner(env["root"])
        syncer = IncrementalSyncer(
            folder_scanner=scanner,
            chroma_store=env["store"],
            registry=env["registry"],
        )
        
        # First sync
        syncer.sync()
        
        # Delete file
        env["file1"].unlink()
        
        # When
        result = syncer.sync()
        
        # Then
        assert result.deleted == 1
        assert result.skipped == 1
        assert env["registry"].get_file_info("note1.md") is None
    
    def test_full_sync(self, setup_sync_env):
        """전체 재동기화 테스트"""
        # Given
        env = setup_sync_env
        scanner = FolderScanner(env["root"])
        syncer = IncrementalSyncer(
            folder_scanner=scanner,
            chroma_store=env["store"],
            registry=env["registry"],
        )
        
        # First sync
        syncer.sync()
        initial_count = env["store"].get_stats()["count"]
        
        # When
        result = syncer.full_sync()
        
        # Then
        assert result.added == 2
        assert env["store"].get_stats()["count"] == initial_count


# ============================================================================
# ChromaStore Incremental Methods Tests
# ============================================================================

class TestChromaStoreIncrementalMethods:
    """ChromaStore 증분 동기화 메서드 테스트"""
    
    def test_generate_deterministic_id(self):
        """Deterministic ID 생성 테스트"""
        # When
        id1 = ChromaStore.generate_deterministic_id("folder/note.md", 0)
        id2 = ChromaStore.generate_deterministic_id("folder/note.md", 1)
        id3 = ChromaStore.generate_deterministic_id("folder/note.md", 0)
        
        # Then
        assert id1 == "folder/note.md::chunk_0"
        assert id2 == "folder/note.md::chunk_1"
        assert id1 == id3  # 같은 경로/인덱스는 같은 ID
    
    def test_upsert_chunks(self, chroma_store):
        """upsert 테스트"""
        # Given
        from core.preprocessing import Chunk
        
        chunks1 = [
            Chunk("Content 1", {"source": "test.md", "relative_path": "test.md"}),
            Chunk("Content 2", {"source": "test.md", "relative_path": "test.md"}),
        ]
        
        # When - First upsert
        count1 = chroma_store.upsert_chunks(chunks1, "test.md")
        
        # Then
        assert count1 == 2
        assert chroma_store.get_stats()["count"] == 2
        
        # When - Second upsert (update)
        chunks2 = [
            Chunk("Updated Content 1", {"source": "test.md", "relative_path": "test.md"}),
            Chunk("Updated Content 2", {"source": "test.md", "relative_path": "test.md"}),
        ]
        count2 = chroma_store.upsert_chunks(chunks2, "test.md")
        
        # Then - Count should still be 2 (updated, not added)
        assert count2 == 2
        assert chroma_store.get_stats()["count"] == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
