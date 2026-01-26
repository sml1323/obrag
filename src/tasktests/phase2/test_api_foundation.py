"""FastAPI App Foundation 테스트"""

import pytest
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from fastapi.testclient import TestClient


class TestAppCreation:
    """앱 생성 테스트"""

    def test_create_app_returns_fastapi_instance(self):
        """create_app()이 FastAPI 인스턴스를 반환하는지 확인"""
        from api.main import create_app
        from fastapi import FastAPI

        app = create_app()
        assert isinstance(app, FastAPI)

    def test_app_has_cors_middleware(self):
        """CORS 미들웨어가 설정되었는지 확인"""
        from api.main import create_app

        app = create_app()
        middleware_names = [m.cls.__name__ for m in app.user_middleware]
        assert "CORSMiddleware" in middleware_names


class TestHealthEndpoint:
    """헬스체크 엔드포인트 테스트"""

    @pytest.fixture
    def client(self):
        from api.main import create_app
        app = create_app()
        # Lifespan을 건너뛰고 테스트용 상태 설정
        return TestClient(app, raise_server_exceptions=False)

    def test_health_returns_200(self, client):
        """GET /health가 200을 반환하는지 확인"""
        response = client.get("/health")
        assert response.status_code == 200

    def test_health_returns_healthy_status(self, client):
        """GET /health가 healthy 상태를 반환하는지 확인"""
        response = client.get("/health")
        assert response.json() == {"status": "healthy"}


class TestAppState:
    """AppState 테스트"""

    def test_app_state_dataclass(self):
        """AppState가 올바른 필드를 가지는지 확인"""
        from api.deps import AppState
        import dataclasses

        assert dataclasses.is_dataclass(AppState)
        fields = {f.name for f in dataclasses.fields(AppState)}
        assert "chroma_store" in fields
        assert "rag_chain" in fields


class TestDependencyFunctions:
    """의존성 주입 함수 테스트"""

    def test_get_rag_chain_exists(self):
        """get_rag_chain 함수가 존재하는지 확인"""
        from api.deps import get_rag_chain
        assert callable(get_rag_chain)

    def test_get_chroma_store_exists(self):
        """get_chroma_store 함수가 존재하는지 확인"""
        from api.deps import get_chroma_store
        assert callable(get_chroma_store)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
