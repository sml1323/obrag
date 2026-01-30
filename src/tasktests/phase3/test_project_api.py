import pytest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from fastapi.testclient import TestClient

# ... imports ...

# ----------------------------------------------------------------------------
# Test: Business Logic (Stale Calculation)
# ----------------------------------------------------------------------------

def test_project_staleness_logic():
    """Test stale calculation based on 30-day threshold."""
    now = datetime.now(timezone.utc)
from sqlmodel import Session, SQLModel, create_engine
from sqlalchemy.pool import StaticPool

from api.main import app
from api.deps import get_session
from core.domain.project import Project
from core.project.scanner import ProjectScanner
from core.project.status import ProjectStatus

# Include current directory in path to import properly
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), "../../../src"))

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

@pytest.fixture(name="client")
def client_fixture(session: Session):
    def get_session_override():
        return session

    app.dependency_overrides[get_session] = get_session_override
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()

@pytest.fixture
def temp_vault(tmp_path):
    """Temporary Vault directory."""
    vault = tmp_path / "Vault"
    vault.mkdir()
    return vault

# ----------------------------------------------------------------------------
# Test: Scanner Refinement (Only .md)
# ----------------------------------------------------------------------------

def test_scanner_ignores_non_md_files(session: Session, temp_vault: Path):
    """Test that scanner only updates for .md files."""
    proj_dir = temp_vault / "MyProject"
    proj_dir.mkdir()
    
    old_time = datetime(2020, 1, 1, tzinfo=timezone.utc)
    project = Project(name="Test Project", path="MyProject", last_modified_at=old_time)
    session.add(project)
    session.commit()
    session.refresh(project)
    if project.last_modified_at.tzinfo is None:
        project.last_modified_at = project.last_modified_at.replace(tzinfo=timezone.utc)
    
    scanner = ProjectScanner(session, temp_vault)
    
    # 1. Create .txt file (should be ignored)
    (proj_dir / "ignore.txt").write_text("ignore me")
    assert scanner.scan_project(project) is False
    
    # 2. Create .DS_Store (should be ignored)
    (proj_dir / ".DS_Store").write_bytes(b"junk")
    assert scanner.scan_project(project) is False
    
    # 3. Create .md file (should trigger update)
    (proj_dir / "valid.md").write_text("knowledge")
    assert scanner.scan_project(project) is True
    
    session.refresh(project)
    if project.last_modified_at and project.last_modified_at.tzinfo is None:
        project.last_modified_at = project.last_modified_at.replace(tzinfo=timezone.utc)
    assert project.last_modified_at > old_time

# ----------------------------------------------------------------------------
# Test: Business Logic (Stale Calculation)
# ----------------------------------------------------------------------------

def test_project_staleness_logic():
    """Test stale calculation based on 30-day threshold."""
    now = datetime.now(timezone.utc)
    
    # Case 1: Active (modified today)
    p_active = Project(name="Active", path="A", last_modified_at=now)
    is_stale, days = ProjectStatus.calculate_staleness(p_active)
    assert is_stale is False
    assert days == 0
    
    # Case 2: Stale (modified 31 days ago)
    past = now - timedelta(days=31)
    p_stale = Project(name="Stale", path="B", last_modified_at=past)
    is_stale, days = ProjectStatus.calculate_staleness(p_stale)
    assert is_stale is True
    assert days >= 31
    
    # Case 3: Boundary (30 days ago) -> Stale
    boundary = now - timedelta(days=30)
    p_boundary = Project(name="Boundary", path="C", last_modified_at=boundary)
    is_stale, days = ProjectStatus.calculate_staleness(p_boundary)
    assert is_stale is True
    
    # Case 4: Never modified (uses created_at), assume created long ago
    p_new = Project(name="New", path="D", created_at=past) # defaults last_modified=None
    p_new.last_modified_at = None # Force None to test fallback
    is_stale, days = ProjectStatus.calculate_staleness(p_new)
    assert is_stale is True # Based on created_at if last_modified is None

# ----------------------------------------------------------------------------
# Test: API Integration
# ----------------------------------------------------------------------------

def test_create_project(client: TestClient):
    response = client.post(
        "/projects/",
        json={"name": "API Project", "path": "Projects/API"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "API Project"
    assert data["path"] == "Projects/API"
    assert "is_stale" in data
    assert "days_inactive" in data

def test_create_duplicate_project_fails(client: TestClient):
    client.post("/projects/", json={"name": "P1", "path": "Dup"})
    response = client.post("/projects/", json={"name": "P2", "path": "Dup"})
    assert response.status_code == 400

def test_get_project_list_and_filter(client: TestClient, session: Session):
    # Setup projects
    now = datetime.now(timezone.utc)
    old = now - timedelta(days=40)
    
    p1 = Project(name="Active", path="A", last_modified_at=now)
    p2 = Project(name="Stale", path="B", last_modified_at=old)
    p3 = Project(name="Inactive", path="C", is_active=False)
    
    session.add_all([p1, p2, p3])
    session.commit()
    
    # 1. List All Active (Default)
    response = client.get("/projects/")
    assert response.status_code == 200
    data = response.json()
    names = [p["name"] for p in data]
    assert "Active" in names
    assert "Stale" in names
    assert "Inactive" not in names
    
    # 2. List All (active_only=False)
    response = client.get("/projects/?active_only=false")
    data = response.json()
    assert len(data) == 3
    
    # 3. List Stale Only
    response = client.get("/projects/?stale_only=true")
    data = response.json()
    names = [p["name"] for p in data]
    assert "Active" not in names
    assert "Stale" in names

def test_update_project(client: TestClient, session: Session):
    p = Project(name="Original", path="UpdateTest")
    session.add(p)
    session.commit()
    
    response = client.patch(
        f"/projects/{p.id}",
        json={"name": "Updated", "is_active": False, "progress": 50}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated"
    assert data["is_active"] is False
    assert data["progress"] == 50
    
    session.refresh(p)
    assert p.name == "Updated"
    assert p.is_active is False
    assert p.progress == 50

def test_update_project_invalid_progress(client: TestClient, session: Session):
    p = Project(name="P", path="P")
    session.add(p)
    session.commit()
    
    response = client.patch(f"/projects/{p.id}", json={"progress": 101})
    assert response.status_code == 422
    
    response = client.patch(f"/projects/{p.id}", json={"progress": -1})
    assert response.status_code == 422

def test_delete_project(client: TestClient, session: Session):
    p = Project(name="DeleteMe", path="DeleteTest")
    session.add(p)
    session.commit()
    
    response = client.delete(f"/projects/{p.id}")
    assert response.status_code == 200
    
    assert session.get(Project, p.id) is None
