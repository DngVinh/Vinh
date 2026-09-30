from __future__ import annotations

import os
from pathlib import Path
import sys
import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[2]
API_SRC = ROOT / "services" / "api" / "src"
SYNTH_SRC = ROOT / "packages" / "synthetic" / "src"
for p in [API_SRC, SYNTH_SRC]:
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from campus247.bootstrap.app import create_app
from campus247.infrastructure.identity.production_guard import ProductionSecurityError


@pytest.fixture
def api_client():
    app = create_app()
    return TestClient(app)


def test_ac_01_unauthenticated_request_fails_closed(api_client: TestClient) -> None:
    """AC-TASK-API-AUTHFIX-001-01: Protected endpoints return approved 401 ProblemDetails when identity is absent or invalid."""
    # 1. No token at all
    resp = api_client.get("/v1/users/me")
    assert resp.status_code == 401
    data = resp.json()
    assert data.get("code") == "AUTHENTICATION_REQUIRED"
    assert data.get("status") == 401
    assert "https://campus247.example/problems/authentication-required" in data.get("type", "")

    # 2. Malformed token
    resp_bad = api_client.get("/v1/users/me", headers={"Authorization": "Bearer not-a-valid-token"})
    assert resp_bad.status_code == 401
    bad_data = resp_bad.json()
    assert bad_data.get("code") == "AUTHENTICATION_REQUIRED"

    # 3. Bad authorization scheme
    resp_scheme = api_client.get("/v1/users/me", headers={"Authorization": "Basic dXNlcjpwYXNz"})
    assert resp_scheme.status_code == 401


def test_ac_02_untrusted_headers_cannot_spoof_identity(api_client: TestClient) -> None:
    """AC-TASK-API-AUTHFIX-001-02: Untrusted headers cannot select user, role, tenant, or privilege."""
    # 1. Attempting to access protected endpoint using spoofed headers without token
    spoofed_headers = {
        "X-User-Id": "admin-user-001",
        "X-Roles": "ADMIN,STAFF",
        "X-Role": "ADMIN",
        "X-Tenant-Id": "tenant-huce",
        "X-Staff-Id": "staff-999",
    }
    resp = api_client.get("/v1/users/me", headers=spoofed_headers)
    assert resp.status_code == 401

    # 2. Attempting privilege escalation with a valid student token plus spoofed admin headers
    resp_demo = api_client.post("/v1/auth/demo-session")
    student_token = resp_demo.json()["token"]

    auth_headers = {
        "Authorization": f"Bearer {student_token}",
        "X-User-Id": "admin-user-001",
        "X-Roles": "ADMIN,SUPERUSER",
        "X-Role": "ADMIN",
        "X-Staff-Id": "staff-999",
    }
    resp_auth = api_client.get("/v1/users/me", headers=auth_headers)
    assert resp_auth.status_code == 200
    data = resp_auth.json()
    # Must remain student identity as encoded in verified token claims
    assert "STUDENT" in data["roles"]
    assert "ADMIN" not in data["roles"]
    assert "SUPERUSER" not in data["roles"]
    assert data["student_code"] == "SV240000"


def test_ac_03_development_identity_impossible_in_production(monkeypatch: pytest.MonkeyPatch) -> None:
    """AC-TASK-API-AUTHFIX-001-03: Development identity behavior is explicit and impossible in production mode."""
    # 1. Starting app in production with mock auth must abort startup with ProductionSecurityError
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setenv("IDENTITY_SECRET_KEY", "a_very_secure_secret_key_for_production_env_test")
    monkeypatch.setenv("CONFIRMATION_SIGNING_KEY", "another_very_secure_secret_key_for_production")

    with pytest.raises(ProductionSecurityError):
        create_app()


def test_ac_03_demo_session_endpoint_in_non_production(api_client: TestClient) -> None:
    """AC-TASK-API-AUTHFIX-001-03: Demo session minting is explicit and working in non-production mode."""
    resp = api_client.post("/v1/auth/demo-session")
    assert resp.status_code == 200
    data = resp.json()
    assert "token" in data
    assert data["roles"] == ["STUDENT"]
