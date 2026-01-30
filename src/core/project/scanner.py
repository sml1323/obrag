"""
Project Scanner Module

등록된 프로젝트의 폴더를 스캔하여 파일 변경 상황을 감지하고
메타데이터(last_modified_at)를 동기화합니다.
"""

from pathlib import Path
from typing import List, Optional
from datetime import datetime, timezone

from sqlmodel import Session, select

from core.domain.project import Project
from core.sync.folder_scanner import FolderScanner
from core.sync.file_tracker import FileTracker

class ProjectScanner:
    """
    Project 폴더 스캐너.
    
    주요 기능:
    - 프로젝트 경로 내 파일 스캔
    - 가장 최근 수정된 파일의 시간(mtime) 파악
    - Project DB 레코드 업데이트 (Stale Project 식별용)
    """
    
    def __init__(self, session: Session, vault_root: Path):
        """
        Args:
            session: DB 세션
            vault_root: Obsidian Vault 루트 경로
        """
        self.session = session
        self.vault_root = vault_root
    
    def scan_project(self, project: Project) -> bool:
        """
        단일 프로젝트를 스캔하여 메타데이터 업데이트.
        
        Args:
            project: 대상 프로젝트 객체
            
        Returns:
            bool: 업데이트 여부 (True if changed)
        """
        # 1. 프로젝트 절대 경로 계산
        project_path = self.vault_root / project.path
        
        if not project_path.exists() or not project_path.is_dir():
            # 프로젝트 폴더가 없으면 스킵 (로깅 필요하지만 현재는 패스)
            return False
            
        # 2. 폴더 내 파일 스캔 (.md 파일만 대상)
        # 지식 관리 목적이므로 마크다운 파일 수정만 감지합니다.
        scanner = FolderScanner(root_path=project_path, extensions=[".md"])
        scanned_files = scanner.scan()
        
        if not scanned_files:
            if project.file_count != 0:
                project.file_count = 0
                self.session.add(project)
                self.session.commit()
                self.session.refresh(project)
                return True
            return False
            
        # 3. 최신 mtime 찾기
        max_mtime = 0.0
        for f in scanned_files:
            try:
                mtime = FileTracker.get_file_mtime(f.full_path)
                if mtime > max_mtime:
                    max_mtime = mtime
            except OSError:
                continue
                
        updated = False
        
        # Update file count
        if project.file_count != len(scanned_files):
            project.file_count = len(scanned_files)
            updated = True

        if max_mtime > 0.0:
            # 4. DB 업데이트 (변경된 경우에만)
            # timestamp to datetime (UTC)
            last_modified = datetime.fromtimestamp(max_mtime, tz=timezone.utc)
            
            # 기존 값과 비교 (DB에서 naive로 올 경우 UTC로 가정)
            current_last_modified = project.last_modified_at
            if current_last_modified and current_last_modified.tzinfo is None:
                current_last_modified = current_last_modified.replace(tzinfo=timezone.utc)

            if current_last_modified is None or last_modified > current_last_modified:
                project.last_modified_at = last_modified
                updated = True
        
        if updated:
            self.session.add(project)
            self.session.commit()
            self.session.refresh(project)
            if project.last_modified_at and project.last_modified_at.tzinfo is None:
                project.last_modified_at = project.last_modified_at.replace(tzinfo=timezone.utc)
            return True
            
        return False

    def scan_all(self) -> int:
        """
        모든 활성 프로젝트를 스캔하고 업데이트된 프로젝트 수 반환.
        """
        projects = self.session.exec(select(Project).where(Project.is_active == True)).all()
        updated_count = 0
        
        for project in projects:
            if self.scan_project(project):
                updated_count += 1
                
        return updated_count
