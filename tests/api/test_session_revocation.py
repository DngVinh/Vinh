from __future__ import annotations

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
from campus247.application.identity.session_service import (
    SessionService,
    get_session_service,
    RevocationStoreError,
)


@pytest.fixture
def api_client():
    # Reset session service for deterministic test
    session_svc = get_session_service()
    session_svc.clear()
    app = create_app()
    return TestClient(app)


def test_ac_01_revoked_session_cannot_authenticate_protected_endpoints(api_client: TestClient) -> None:
    """AC-TASK-API-SESSFIX-001-01: A revoked session cannot authenticate any subsequent protected request."""
    # 1. Obtain a valid session token
    resp_demo = api_client.post("/v1/auth/demo-session")
    assert resp_demo.status_code == 200
    token = resp_demo.json()["token"]

    # 2. Before revocation: request succeeds
    resp_before = api_client.get("/v1/users/me", headers={"Authorization": f"Bearer {token}"})
    assert resp_before.status_code == 200

    # 3. Revoke the token via session service
    session_svc = get_session_service()
    result = session_svc.revoke_session(token, reason="user_logout", actor_id="SV240000")
    assert result["status"] == "revoked"

    # 4. After revocation: immediate fail closed with 401
    resp_after = api_client.get("/v1/users/me", headers={"Authorization": f"Bearer {token}"})
    assert resp_after.status_code == 401
    data = resp_after.json()
    assert data.get("code") == "AUTHENTICATION_REQUIRED"


def test_ac_02_logout_is_idempotent_and_handles_store_failure() -> None:
    """AC-TASK-API-SESSFIX-001-02: Logout is idempotent and does not report success before revocation is durably recorded."""
    service = SessionService()
    token = "demo.test.bearer.token.12345"

    # First revocation succeeds
    res1 = service.revoke_session(token, reason="logout")
    assert res1["status"] == "revoked"
    assert res1["idempotent"] is False

    # Second revocation is idempotent and succeeds without error
    res2 = service.revoke_session(token, reason="logout")
    assert res2["status"] == "revoked"
    assert res2["idempotent"] is True

    # Backend store failure: must raise error and NOT falsely report success
    class FailingStore:
        def revoke(self, key: str) -> None:
            raise RuntimeError("Database connection lost during commit")

        def is_revoked(self, key: str) -> bool:
            return False

    failing_service = SessionService(store=FailingStore())
    with pytest.raises(RevocationStoreError):
        failing_service.revoke_session("another.token")


def test_ac_03_audit_events_use_safe_hashes_without_raw_token() -> None:
    """AC-TASK-API-SESSFIX-001-03: Audit events contain safe identifiers and outcome but no raw token or secret."""
    service = SessionService()
    raw_token = "secret-jwt-token-with-signature-987654321"

    service.revoke_session(raw_token, reason="credential_rotation", actor_id="user-456")

    events = service.get_audit_events()
    assert len(events) >= 1
    last_event = events[-1]

    # Must contain safe identifier and reason
    assert "safe_id" in last_event
    assert last_event["reason"] == "credential_rotation"
    assert last_event["actor_id"] == "user-456"
    assert last_event["outcome"] == "revoked"

    # Crucial security assertion: raw token MUST NOT appear anywhere in the audit event
    event_str = str(last_event)
    assert raw_token not in event_str
    assert "987654321" not in event_str
