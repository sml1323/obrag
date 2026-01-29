import pytest
import time
from pathlib import Path
from datetime import datetime
from sqlmodel import Session, SQLModel, create_engine
from sqlalchemy.pool import StaticPool

from core.domain.project import Project
from core.project.scanner import ProjectScanner

# ----------------------------------------------------------------------------
# Fixtures
# ----------------------------------------------------------------------------

@pytest.fixture(name="session")
def session_fixture():
    engine = create_engine(
        "sqlite://", 
        connect_args={"check_same_thread": False}, 
        poolclass=StaticPool
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session

@pytest.fixture
def temp_vault(tmp_path):
    """임시 Vault 디렉토리 생성"""
    vault = tmp_path / "Vault"
    vault.mkdir()
    return vault

# ----------------------------------------------------------------------------
# Tests
# ----------------------------------------------------------------------------

def test_scan_updates_last_modified(session: Session, temp_vault: Path):
    """파일 수정 시 프로젝트의 last_modified_at이 갱신되는지 테스트"""
    # 1. Project 생성 (last_modified_at을 과거로 설정)
    proj_dir = temp_vault / "MyProject"
    proj_dir.mkdir()
    
    old_time = datetime(2020, 1, 1)
    project = Project(name="Test Project", path="MyProject", last_modified_at=old_time)
    session.add(project)
    session.commit()
    session.refresh(project)
    
    scanner = ProjectScanner(session, temp_vault)
    
    # 2. 파일 없음 -> 업데이트 안됨
    assert scanner.scan_project(project) is False
    assert project.last_modified_at == old_time
    
    # 3. 파일 생성 (과거지만 Project 시간보다는 뒤)
    file_a = proj_dir / "note.md"
    file_a.write_text("Hello")
    
    # 4. 스캔 -> 업데이트 됨
    # (파일을 방금 만들었으므로 mtime은 old_time(2020년)보다 큼)
    assert scanner.scan_project(project) is True
    assert project.last_modified_at > old_time
    first_update = project.last_modified_at
    
    # 5. 더 최신 파일 생성
    time.sleep(0.1) # mtime 차이 확보
    file_b = proj_dir / "recent.md"
    file_b.write_text("World")
    
    # 6. 재스캔 -> 갱신됨
    assert scanner.scan_project(project) is True
    assert project.last_modified_at > first_update

def test_scan_nested_structure(session: Session, temp_vault: Path):
    """사용자 요청: 중첩된 폴더 구조 (note/1.PARA...) 인식 테스트"""
    
    # 1. 중첩 경로 생성
    nested_path = "note/1.PARA/1.Project/DeepProject"
    full_path = temp_vault / nested_path
    full_path.mkdir(parents=True)
    
    # 2. 파일 생성
    (full_path / "readme.md").write_text("Deep nested project")
    
    # 3. Project 등록
    project = Project(name="Deep Project", path=nested_path)
    session.add(project)
    session.commit()
    session.refresh(project)
    
    # 4. 스캔 실행
    scanner = ProjectScanner(session, temp_vault)
    is_updated = scanner.scan_project(project)
    
    # 5. 결과 검증
    assert is_updated is True
    assert project.last_modified_at is not None
    # 날짜가 오늘인지 간단 확인
    assert project.last_modified_at.date() == datetime.today().date()

def test_scan_all_projects(session: Session, temp_vault: Path):
    """모든 활성 프로젝트 스캔 테스트"""
    old_time = datetime(2020, 1, 1)
    
    # Proj A: 활성, 파일 있음 (오래된 last_modified_at 설정 -> 업데이트 되어야 함)
    dir_a = temp_vault / "ProjectA"
    dir_a.mkdir()
    (dir_a / "test.md").write_text("A")
    p_a = Project(name="A", path="ProjectA", is_active=True, last_modified_at=old_time)
    
    # Proj B: 활성, 파일 없음 (last_modified_at 유지되어야 함)
    dir_b = temp_vault / "ProjectB"
    dir_b.mkdir()
    p_b = Project(name="B", path="ProjectB", is_active=True) # default now()
    
    # Proj C: 비활성, 파일 있음 (스캔 안되어야 함)
    dir_c = temp_vault / "ProjectC"
    dir_c.mkdir()
    (dir_c / "test.md").write_text("C")
    p_c = Project(name="C", path="ProjectC", is_active=False, last_modified_at=old_time)
    
    session.add_all([p_a, p_b, p_c])
    session.commit()
    
    # p_b의 초기 시간 저장
    session.refresh(p_b)
    p_b_initial_time = p_b.last_modified_at
    
    scanner = ProjectScanner(session, temp_vault)
    count = scanner.scan_all()
    
    # A만 업데이트되어야 함
    assert count == 1
    
    session.refresh(p_a)
    session.refresh(p_b)
    session.refresh(p_c)
    
    assert p_a.last_modified_at > old_time
    assert p_b.last_modified_at == p_b_initial_time
    assert p_c.last_modified_at == old_time
