from __future__ import annotations

import sys
from pathlib import Path
from fastapi import FastAPI
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[2]
API_SRC = ROOT / "services" / "api" / "src"
if str(API_SRC) not in sys.path:
    sys.path.insert(0, str(API_SRC))

from campus247.presentation.health import router


def test_health_ready_endpoint_healthy():
    """Verify /health/ready returns HTTP 200 with valid structure conforming to API-SYS-002."""
    app = FastAPI()
    app.include_router(router)
    client = TestClient(app)

    response = client.get("/health/ready")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ("ready", "degraded")
    assert isinstance(data["dependencies"], list)
    assert len(data["dependencies"]) >= 1
    assert data["security_configuration"]["demo_auth_guard"] in ("ENFORCED", "NOT_APPLICABLE")


def test_health_ready_unhealthy_negative_path(monkeypatch):
    """Verify /health/ready returns 503 when critical dependency fails."""
    from campus247.presentation import health

    async def failing_check(request=None):
        return False

    monkeypatch.setattr(health, "check_database_connectivity", failing_check)

    app = FastAPI()
    app.include_router(router)
    client = TestClient(app)

    response = client.get("/health/ready")
    assert response.status_code == 503
