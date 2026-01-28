import pytest
from unittest.mock import Mock, MagicMock
from fastapi.testclient import TestClient

from api.main import app
from api.deps import get_syncer, get_chroma_store
from core.sync.incremental_syncer import IncrementalSyncer, SyncResult
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
