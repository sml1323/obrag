import pytest
from sqlmodel import Session, SQLModel, create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.pool import StaticPool

from core.domain.project import Project

# Use In-Memory SQLite with StaticPool to persist data within the test session
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

def test_create_project(session: Session):
    """Test creating a project with valid data."""
    project = Project(name="Test Project", path="Projects/Test")
    session.add(project)
    session.commit()
    session.refresh(project)

    assert project.id is not None
    assert project.name == "Test Project"
    assert project.path == "Projects/Test"
    assert project.is_active is True  # Default value
    assert project.created_at is not None

def test_project_path_uniqueness(session: Session):
    """Test that project path must be unique."""
    client1 = Project(name="Project A", path="Projects/Common")
    session.add(client1)
    session.commit()

    client2 = Project(name="Project B", path="Projects/Common")
    session.add(client2)
    
    with pytest.raises(IntegrityError):
        session.commit()

def test_project_optional_fields(session: Session):
    """Test creating a project with optional description."""
    project = Project(
        name="Detailed Project", 
        path="Projects/Detailed", 
        description="This is a detailed description"
    )
    session.add(project)
    session.commit()
    session.refresh(project)

    assert project.description == "This is a detailed description"
