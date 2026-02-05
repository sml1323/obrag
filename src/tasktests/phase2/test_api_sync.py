import pytest
from unittest.mock import Mock, MagicMock, patch
from fastapi.testclient import TestClient

from api.main import app
from api.deps import get_syncer, get_chroma_store, get_session
from core.sync.incremental_syncer import IncrementalSyncer, SyncResult
from core.domain.project import Project
from db.chroma_store import ChromaStore


@pytest.fixture
def mock_syncer():
    syncer = Mock(spec=IncrementalSyncer)
    # 기본적으로 변경사항이 있는 결과 반환
    syncer.sync.return_value = SyncResult(
        added=1, modified=0, deleted=0, skipped=5, total_chunks=3
    )
    return syncer


@pytest.fixture
def mock_store():
    store = Mock(spec=ChromaStore)
    store.get_stats.return_value = {"total_documents": 100}
    return store


@pytest.fixture
def client(mock_syncer, mock_store):
    # 의존성 오버라이드
    app.dependency_overrides[get_syncer] = lambda: mock_syncer
    app.dependency_overrides[get_chroma_store] = lambda: mock_store

    with TestClient(app) as c:
        yield c

    # 오버라이드 해제
    app.dependency_overrides.clear()


def test_sync_trigger(client, mock_syncer):
    """POST /sync/trigger 테스트"""
    response = client.post("/sync/trigger")

    assert response.status_code == 200
    data = response.json()

    # SyncResult 검증
    assert data["added"] == 1
    assert data["skipped"] == 5
    assert data["total_chunks"] == 3

    # syncer.sync() 호출 확인
    mock_syncer.sync.assert_called_once()


def test_health_check(client):
    """GET /health 테스트"""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_status_check(client, mock_store):
    """GET /status 테스트"""
    response = client.get("/status")

    assert response.status_code == 200
    data = response.json()

    assert data["status"] == "ready"
    assert data["db"] == {"total_documents": 100}

    # store.get_stats() 호출 확인
    mock_store.get_stats.assert_called_once()


# ============================================================================
# project_id 기반 동기화 테스트
# ============================================================================


@pytest.fixture
def mock_session():
    """Mock DB session"""
    session = Mock()
    return session


@pytest.fixture
def client_with_session(mock_syncer, mock_store, mock_session):
    """프로젝트 ID 테스트용 클라이언트"""
    app.dependency_overrides[get_syncer] = lambda: mock_syncer
    app.dependency_overrides[get_chroma_store] = lambda: mock_store
    app.dependency_overrides[get_session] = lambda: mock_session

    with TestClient(app) as c:
        yield c

    app.dependency_overrides.clear()


def test_sync_trigger_with_project_id_not_found(client_with_session, mock_session):
    """project_id 제공 시 프로젝트가 없으면 404 반환"""
    mock_session.get.return_value = None

    response = client_with_session.post("/sync/trigger?project_id=999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Project not found"


def test_sync_trigger_with_project_id_path_not_exists(
    client_with_session, mock_session
):
    """project_id 제공 시 경로가 존재하지 않으면 400 반환"""
    mock_project = Mock(spec=Project)
    mock_project.path = "/nonexistent/path/that/does/not/exist"
    mock_session.get.return_value = mock_project

    response = client_with_session.post("/sync/trigger?project_id=1")

    assert response.status_code == 400
    assert "does not exist" in response.json()["detail"]


@patch("api.routers.sync.create_syncer")
def test_sync_trigger_with_valid_project_id(
    mock_create_syncer, client_with_session, mock_session, mock_store, tmp_path
):
    """유효한 project_id 제공 시 해당 경로로 동기화"""
    # 실제 존재하는 tmp 디렉토리 사용
    mock_project = Mock(spec=Project)
    mock_project.path = str(tmp_path)
    mock_session.get.return_value = mock_project

    # create_syncer가 반환할 mock syncer
    dynamic_syncer = Mock()
    dynamic_syncer.sync.return_value = SyncResult(
        added=5, modified=2, deleted=1, skipped=10, total_chunks=20
    )
    mock_create_syncer.return_value = dynamic_syncer

    response = client_with_session.post("/sync/trigger?project_id=1")

    assert response.status_code == 200
    data = response.json()
    assert data["added"] == 5
    assert data["modified"] == 2
    assert data["deleted"] == 1

    # create_syncer가 올바른 경로로 호출되었는지 확인
    mock_create_syncer.assert_called_once()
    call_args = mock_create_syncer.call_args
    assert call_args.kwargs["root_path"] == str(tmp_path)
