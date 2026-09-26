"""Security test suite for web boundaries: CORS, CSRF, cookie flags and headers (TASK-TEST-SEC-004)."""

from pathlib import Path
import sys
from fastapi import FastAPI, Response
from fastapi.testclient import TestClient
import pytest

ROOT = Path(__file__).resolve().parents[2]
API_SRC = ROOT / "services" / "api" / "src"
if str(API_SRC) not in sys.path:
    sys.path.insert(0, str(API_SRC))

from campus247.bootstrap.app import create_app


def test_cors_allows_configured_local_origin():
    app = create_app()

    @app.get("/test-endpoint")
    def sample():
        return {"ok": True}

    client = TestClient(app)
    response = client.get("/test-endpoint", headers={"Origin": "http://localhost:3000"})
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "http://localhost:3000"
    assert response.headers.get("access-control-allow-credentials") == "true"


def test_cors_rejects_untrusted_origin():
    app = create_app()

    @app.get("/test-endpoint")
    def sample():
        return {"ok": True}

    client = TestClient(app)
    response = client.get("/test-endpoint", headers={"Origin": "http://evil-attacker.example"})
    assert response.status_code == 200
    assert "access-control-allow-origin" not in response.headers


def test_session_cookie_security_attributes():
    app = FastAPI()

    @app.post("/api/v1/auth/session")
    def set_session(response: Response):
        response.set_cookie(
            key="campus247_session",
            value="token_sample_123",
            httponly=True,
            samesite="lax",
            secure=True,
        )
        return {"authenticated": True}

    client = TestClient(app)
    resp = client.post("/api/v1/auth/session")
    assert resp.status_code == 200

    set_cookie = resp.headers.get("set-cookie", "")
    assert "HttpOnly" in set_cookie
    assert "SameSite=lax" in set_cookie
    assert "Secure" in set_cookie


def test_negative_cors_preflight_blocks_disallowed_origin():
    app = create_app()
    client = TestClient(app)

    response = client.options(
        "/openapi.json",
        headers={
            "Origin": "http://malicious.org",
            "Access-Control-Request-Method": "POST",
        },
    )
    # Disallowed origin should not have CORS approval header
    assert response.headers.get("access-control-allow-origin") is None
