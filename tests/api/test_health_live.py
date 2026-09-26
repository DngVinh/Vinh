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


def test_health_live_endpoint_returns_alive():
    """Verify /health/live returns HTTP 200 with status alive conforming to API-SYS-001."""
    app = FastAPI()
    app.include_router(router)
    client = TestClient(app)

    response = client.get("/health/live")
    assert response.status_code == 200
    data = response.json()
    assert data == {"status": "alive"}


def test_health_live_rejects_post():
    """Verify /health/live rejects unsupported HTTP methods (negative path)."""
    app = FastAPI()
    app.include_router(router)
    client = TestClient(app)

    response = client.post("/health/live", json={})
    assert response.status_code == 405
