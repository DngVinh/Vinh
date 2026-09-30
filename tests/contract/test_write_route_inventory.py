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
from campus247.infrastructure.identity.mock import SyntheticIdentityAdapter


@pytest.fixture
def test_client():
    app = create_app()
    return TestClient(app)


@pytest.fixture
def auth_header(test_client: TestClient) -> dict[str, str]:
    resp = test_client.post("/v1/auth/demo-session")
    token = test_client.cookies.get("auth_token", "").strip('"')
    return {"Authorization": f"Bearer {token}"}


def test_ac_01_direct_write_routes_fail_closed(test_client: TestClient, auth_header: dict[str, str]) -> None:
    """AC-TASK-API-WRITEFIX-001-01: Direct unconfirmed or unauthenticated write routes fail closed."""
    # 1. Direct ticket POST must be blocked (405 Method Not Allowed)
    resp_ticket = test_client.post("/v1/tickets", headers=auth_header, json={"subject": "Direct write test"})
    assert resp_ticket.status_code == 405
    assert "Direct ticket creation is prohibited" in str(resp_ticket.json())

    # 2. Room booking without authentication must return 401
    test_client.cookies.clear()
    resp_unauth = test_client.post("/v1/rooms/book", json={"room_id": "r-101"})
    assert resp_unauth.status_code == 401

    # 3. Room booking without confirmation_token must return 422
    resp_no_token = test_client.post(
        "/v1/rooms/book",
        headers={**auth_header, "Idempotency-Key": "idem-key-1"},
        json={"room_id": "r-101"},
    )
    assert resp_no_token.status_code == 422
    assert "confirmation_token" in str(resp_no_token.json())

    # 4. Room booking without Idempotency-Key must return 422
    resp_no_idem = test_client.post(
        "/v1/rooms/book",
        headers=auth_header,
        json={"room_id": "r-101", "confirmation_token": "valid.confirm.token.001"},
    )
    assert resp_no_idem.status_code == 422
    assert "Idempotency-Key" in str(resp_no_idem.json())

    # 5. Apparent credentials must not bypass server-issued preview binding.
    resp_valid = test_client.post(
        "/v1/rooms/book",
        headers={**auth_header, "Idempotency-Key": "idem-key-1"},
        json={"room_id": "r-101", "confirmation_token": "valid.confirm.token.001"},
    )
    assert resp_valid.status_code == 503
    assert "booking_id" not in resp_valid.json()
    assert resp_valid.json().get("status") != "CONFIRMED"

    # Replaying the same apparent credentials must remain side-effect free.
    resp_replay = test_client.post(
        "/v1/rooms/book",
        headers={**auth_header, "Idempotency-Key": "idem-key-1"},
        json={"room_id": "r-101", "confirmation_token": "valid.confirm.token.001"},
    )
    assert resp_replay.status_code == 503
    assert "booking_id" not in resp_replay.json()
    assert resp_replay.json().get("status") != "CONFIRMED"


def test_ac_02_controlled_ticket_write_enforces_preview_and_idempotency(test_client: TestClient, auth_header: dict[str, str]) -> None:
    """AC-TASK-API-WRITEFIX-001-02: Ticket write requires preview and confirmation; replay produces no duplicate."""
    # 1. Preview
    preview_payload = {
        "category": "ACADEMIC_POLICY",
        "priority": "NORMAL",
        "subject": "Xin hoãn thi môn Triết",
        "description": "Lý do cá nhân",
        "queue_key": "HUCE_GENERAL",
    }
    resp_preview = test_client.post("/v1/tickets/preview", headers=auth_header, json=preview_payload)
    assert resp_preview.status_code == 201
    preview_data = resp_preview.json()
    preview_id = preview_data["preview_id"]
    confirmation_token = preview_data["confirmation_token"]

    # 2. Confirm with valid token and idempotency key
    confirm_payload = {
        "confirmation_token": confirmation_token,
        "idempotency_key": "idemp-test-ticket-001",
        "payload": preview_payload,
    }
    resp_confirm_1 = test_client.post(f"/v1/tickets/{preview_id}/confirm", headers=auth_header, json=confirm_payload)
    assert resp_confirm_1.status_code == 201
    assert resp_confirm_1.json()["is_replay"] is False
    ticket_id_1 = resp_confirm_1.json()["ticket_id"]

    # 3. Replay with same idempotency key must not create a duplicate
    resp_confirm_2 = test_client.post(f"/v1/tickets/{preview_id}/confirm", headers=auth_header, json=confirm_payload)
    assert resp_confirm_2.status_code == 201
    assert resp_confirm_2.json()["is_replay"] is True
    assert resp_confirm_2.json()["ticket_id"] == ticket_id_1


def test_ac_03_route_inventory_classifies_all_write_routes() -> None:
    """AC-TASK-API-WRITEFIX-001-03: Every write route is registered and classified in the controlled-write catalog."""
    app = create_app()
    schema = app.openapi()
    paths = schema.get("paths", {})

    write_routes: list[tuple[str, str]] = []
    for path, path_item in paths.items():
        for method in path_item.keys():
            if method.upper() in ("POST", "PUT", "PATCH", "DELETE"):
                write_routes.append((method.upper(), path))

    # Approved classified catalog of write operations
    KNOWN_WRITE_CATALOG = {
        ("POST", "/v1/auth/demo-session"): "demo_session_minting",
        ("POST", "/v1/auth/logout"): "session_revocation",
        ("POST", "/v1/logout"): "session_revocation",
        ("POST", "/v1/tickets/preview"): "write_preview_generation",
        ("POST", "/v1/tickets/{preview_id}/confirm"): "controlled_write_confirmation",
        ("POST", "/v1/tickets"): "guarded_blocked_direct_write",
        ("POST", "/v1/rooms/book"): "guarded_disabled_room_booking",
        ("POST", "/v1/conversations"): "conversation_initialization",
        ("POST", "/v1/conversations/{conversation_id}/messages:stream"): "chat_stream_query",
        ("POST", "/v1/conversations/{conversation_id}/messages/{message_id}/feedback"): "user_feedback_submission",
        ("POST", "/v1/privacy/consents"): "privacy_consent_recording",
        ("POST", "/v1/privacy/requests"): "privacy_request_submission",
    }

    unclassified_routes = []
    for route in write_routes:
        if route not in KNOWN_WRITE_CATALOG:
            unclassified_routes.append(route)

    assert not unclassified_routes, f"Found unclassified or unguarded write routes: {unclassified_routes}"
