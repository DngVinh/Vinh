import pytest
from fastapi.testclient import TestClient
from fastapi import FastAPI
from campus247.bootstrap.app import create_app

@pytest.fixture
def client():
    app = create_app()
    return TestClient(app)

def test_liveness_returns_alive(client):
    response = client.get("/health/live")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "alive"

def test_readiness_without_db_returns_disabled_and_ready(client):
    # By default, test environment doesn't bind a real database unless configured.
    # So db_engine is probably not set, meaning 'disabled' status.
    response = client.get("/health/ready")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ready"
    
    db_dep = next(d for d in data["dependencies"] if d["name"] == "database")
    assert db_dep["status"] in ["disabled", "ready"]
    assert "security_configuration" in data

def test_readiness_unavailable_when_db_fails(client):
    # Mock the app state to have a failing db_engine
    class MockFailingEngine:
        def connect(self):
            class MockContextManager:
                async def __aenter__(self):
                    class MockConn:
                        async def execute(self, query):
                            import asyncio
                            await asyncio.sleep(3) # trigger timeout
                    return MockConn()
                async def __aexit__(self, exc_type, exc_val, exc_tb):
                    pass
            return MockContextManager()
            
    client.app.state.db_engine = MockFailingEngine()
    
    response = client.get("/health/ready")
    assert response.status_code == 503
    data = response.json()
    assert data["code"] == "DEPENDENCY_UNAVAILABLE"
    assert data["retryable"] is True
    # Ensure no stack traces or secrets
    assert "MockFailingEngine" not in response.text
