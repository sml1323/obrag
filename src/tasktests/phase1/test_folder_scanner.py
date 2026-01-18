"""
Phase 1: Folder Scanner 테스트

이 테스트는 폴더 재귀 스캔 및 메타데이터 추출이 올바르게 동작하는지 검증합니다.
테스트 대상: src/core/sync/folder_scanner.py
"""

import sys
from pathlib import Path

# 프로젝트 루트를 path에 추가
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

import pytest
from core.sync import (
    DEFAULT_IGNORE_PATTERNS,
    FolderScanner,
    ScannedFile,
    scan_and_process_folder,
    scan_folder,
)


# ============================================================================
# Test: FolderScanner Basic
# ============================================================================

class TestFolderScannerBasic:
    """FolderScanner 기본 기능 테스트"""
    
    @pytest.fixture
    def testdoc_path(self):
        """testdoc 폴더 경로"""
        return project_root / "testdoc" / "note"
    
    def test_scanner_initialization(self, testdoc_path):
        """스캐너 초기화 성공"""
        scanner = FolderScanner(testdoc_path)
        assert scanner.root_path.exists()
        assert scanner.extensions == [".md"]
    
    def test_scanner_invalid_path_raises_error(self):
        """존재하지 않는 경로에 대해 에러 발생"""
        with pytest.raises(FileNotFoundError):
            FolderScanner("/nonexistent/path")
    
    def test_scanner_file_path_raises_error(self, testdoc_path):
        """파일 경로(폴더가 아닌)에 대해 에러 발생"""
        # testdoc 안의 아무 파일 찾기
        for child in testdoc_path.iterdir():
            if child.is_file():
                with pytest.raises(NotADirectoryError):
                    FolderScanner(child)
                break


# ============================================================================
# Test: Scanning
# ============================================================================

class TestScanning:
    """스캐닝 기능 테스트"""
    
    @pytest.fixture
    def testdoc_path(self):
        """testdoc 폴더 경로"""
        return project_root / "testdoc" / "note"
    
    def test_scan_finds_md_files(self, testdoc_path):
        """md 파일을 찾아야 함"""
        scanner = FolderScanner(testdoc_path)
        files = scanner.scan()
        
        assert len(files) > 0, "testdoc에 md 파일이 있어야 함"
        for f in files:
            assert f.filename.endswith(".md")
    
    def test_scan_returns_scanned_file_objects(self, testdoc_path):
        """ScannedFile 객체 반환"""
        scanner = FolderScanner(testdoc_path)
        files = scanner.scan()
        
        if files:
            file = files[0]
            assert isinstance(file, ScannedFile)
            assert isinstance(file.full_path, Path)
            assert file.full_path.exists()
            assert file.filename == file.full_path.name
    
    def test_ignores_hidden_folders(self, testdoc_path):
        """숨김 폴더 제외 (.obsidian, .git 등)"""
        scanner = FolderScanner(testdoc_path)
        files = scanner.scan()
        
        for f in files:
            for part in f.relative_path.parts:
                assert not part.startswith("."), f"숨김 폴더가 포함됨: {f.relative_path}"
    
    def test_ignores_configured_patterns(self, testdoc_path):
        """설정된 제외 패턴 적용"""
        scanner = FolderScanner(testdoc_path)
        files = scanner.scan()
        
        for f in files:
            for ignore_pattern in DEFAULT_IGNORE_PATTERNS:
                assert ignore_pattern not in f.relative_path.parts


# ============================================================================
# Test: Metadata Extraction
# ============================================================================

class TestMetadataExtraction:
    """메타데이터 추출 테스트"""
    
    @pytest.fixture
    def testdoc_path(self):
        """testdoc 폴더 경로"""
        return project_root / "testdoc" / "note"
    
    def test_metadata_has_required_fields(self, testdoc_path):
        """메타데이터에 필수 필드 포함"""
        scanner = FolderScanner(testdoc_path)
        files = scanner.scan()
        
        if files:
            metadata = files[0].to_metadata()
            
            assert "source" in metadata, "source 필드 필요"
            assert "folder_path" in metadata, "folder_path 필드 필요"
            assert "full_path" in metadata, "full_path 필드 필요"
    
    def test_folder_path_is_relative(self, testdoc_path):
        """folder_path가 상대 경로"""
        scanner = FolderScanner(testdoc_path)
        files = scanner.scan()
        
        for f in files:
            # full_path와 다르게 folder_path는 절대경로 시작이 아니어야 함
            assert not f.folder_path.startswith("/"), f"folder_path는 상대경로여야 함: {f.folder_path}"
    
    def test_source_is_filename(self, testdoc_path):
        """source가 파일명과 일치"""
        scanner = FolderScanner(testdoc_path)
        files = scanner.scan()
        
        for f in files:
            assert f.filename == Path(f.to_metadata()["source"]).name


# ============================================================================
# Test: Integration with Preprocessor
# ============================================================================

class TestIntegration:
    """Preprocessor 통합 테스트"""
    
    @pytest.fixture
    def testdoc_path(self):
        """testdoc 폴더 경로"""
        return project_root / "testdoc" / "note"
    
    def test_scan_and_process_returns_chunks(self, testdoc_path):
        """scan_and_process가 Chunk 리스트 반환"""
        scanner = FolderScanner(testdoc_path)
        chunks = scanner.scan_and_process()
        
        assert len(chunks) > 0, "청크가 생성되어야 함"
    
    def test_chunks_have_folder_metadata(self, testdoc_path):
        """청크에 폴더 메타데이터 포함"""
        scanner = FolderScanner(testdoc_path)
        chunks = scanner.scan_and_process()
        
        if chunks:
            chunk = chunks[0]
            assert "source" in chunk.metadata
            # folder_path와 full_path는 extra_metadata로 추가됨
            assert "folder_path" in chunk.metadata, "folder_path 메타데이터 필요"
            assert "full_path" in chunk.metadata, "full_path 메타데이터 필요"
    
    def test_convenience_function_scan_folder(self, testdoc_path):
        """scan_folder 편의 함수"""
        files = scan_folder(testdoc_path)
        assert isinstance(files, list)
    
    def test_convenience_function_scan_and_process(self, testdoc_path):
        """scan_and_process_folder 편의 함수"""
        chunks = scan_and_process_folder(testdoc_path)
        assert isinstance(chunks, list)


# ============================================================================
# Test: Edge Cases
# ============================================================================

class TestEdgeCases:
    """엣지 케이스 테스트"""
    
    def test_empty_folder(self, tmp_path):
        """빈 폴더 스캔"""
        scanner = FolderScanner(tmp_path)
        files = scanner.scan()
        assert files == []
    
    def test_folder_with_no_md_files(self, tmp_path):
        """md 파일이 없는 폴더"""
        # txt 파일만 생성
        (tmp_path / "test.txt").write_text("hello")
        
        scanner = FolderScanner(tmp_path)
        files = scanner.scan()
        assert files == []
    
    def test_custom_extensions(self, tmp_path):
        """커스텀 확장자 스캔"""
        (tmp_path / "test.txt").write_text("hello")
        (tmp_path / "test.md").write_text("# Hello")
        
        scanner = FolderScanner(tmp_path, extensions=[".txt"])
        files = scanner.scan()
        
        assert len(files) == 1
        assert files[0].filename == "test.txt"
    
    def test_nested_folder_structure(self, tmp_path):
        """중첩 폴더 구조"""
        # 중첩 폴더 생성
        nested = tmp_path / "level1" / "level2" / "level3"
        nested.mkdir(parents=True)
        (nested / "deep.md").write_text("# Deep file")
        
        scanner = FolderScanner(tmp_path)
        files = scanner.scan()
        
        assert len(files) == 1
        assert files[0].folder_path == "level1/level2/level3"
        assert files[0].filename == "deep.md"


# ============================================================================
# Run Tests
# ============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
