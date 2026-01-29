"""
Project Scanner Module

등록된 프로젝트의 폴더를 스캔하여 파일 변경 상황을 감지하고
메타데이터(last_modified_at)를 동기화합니다.
"""

from pathlib import Path
from typing import List, Optional
from datetime import datetime

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
            # 파일이 하나도 없으면 업데이트 안 함 (또는 폴더 자체 mtime 사용 고려 가능)
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
                
        if max_mtime == 0.0:
            return False
            
        # 4. DB 업데이트 (변경된 경우에만)
        # timestamp to datetime
        last_modified = datetime.fromtimestamp(max_mtime)
        
        # 기존 값과 비교 (tzinfo 처리 필요할 수 있으나, 보통 로컬 타임스탬프 기준)
        # Project.last_modified_at이 없거나 더 최신이면 업데이트
        if project.last_modified_at is None or last_modified > project.last_modified_at:
            project.last_modified_at = last_modified
            self.session.add(project)
            self.session.commit()
            self.session.refresh(project)
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
