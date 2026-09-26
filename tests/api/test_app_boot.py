from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
API_SRC = ROOT / "services" / "api" / "src"

if str(API_SRC) not in sys.path:
    sys.path.insert(0, str(API_SRC))

from campus247.bootstrap.app import create_app
from fastapi import FastAPI


def test_app_factory_creates_fastapi_instance():
    """Verify create_app produces a valid, configured FastAPI application."""
    app = create_app()
    assert isinstance(app, FastAPI)
    assert app.title == "Campus 24/7 API"
    assert app.version == "0.1.0"
    assert app.docs_url == "/docs"
    assert app.openapi_url == "/openapi.json"


def test_app_factory_mounts_all_routers_and_request_id():
    """Verify create_app mounts presentation routes and request ID header is returned."""
    from fastapi.testclient import TestClient

    app = create_app()
    client = TestClient(app)

    routes = []
    for r in app.routes:
        if hasattr(r, "path"):
            routes.append(r.path)
        elif hasattr(r, "original_router"):
            for sub_r in r.original_router.routes:
                if hasattr(sub_r, "path"):
                    routes.append(sub_r.path)
    assert "/health/live" in routes
    assert "/health/ready" in routes
    assert "/v1/users/me" in routes
    assert "/v1/capabilities" in routes
    assert "/v1/students/me/schedule" in routes
    assert "/v1/tickets" in routes
    assert "/v1/rooms" in routes
    assert "/v1/knowledge/sources" in routes
    assert "/v1/document-requests" in routes
    assert "/v1/staff/handovers" in routes
    assert "/v1/privacy/notice" in routes
    assert "/v1/privacy/requests" in routes

    resp = client.get("/health/live")
    assert resp.status_code == 200
    assert "x-request-id" in resp.headers or "X-Request-Id" in resp.headers


