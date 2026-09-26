from __future__ import annotations

from datetime import datetime, timezone, timedelta
from pathlib import Path
import sys
from fastapi import FastAPI
from fastapi.testclient import TestClient
import pytest

ROOT = Path(__file__).resolve().parents[2]
API_SRC = ROOT / "services" / "api" / "src"
SYNTH_SRC = ROOT / "packages" / "synthetic" / "src"
if str(API_SRC) not in sys.path:
    sys.path.insert(0, str(API_SRC))
if str(SYNTH_SRC) not in sys.path:
    sys.path.insert(0, str(SYNTH_SRC))

from campus247.application.action.idempotency import IdempotencyLedger
from campus247.application.audit.writer import AuditWriter
from campus247.application.ticket.confirm import TicketConfirmationService
from campus247.application.ticket.preview import TicketPreviewService
from campus247.domain.action.confirmation import ConfirmationTokenService
from campus247.domain.policy.student import StudentPolicyEngine
from campus247.infrastructure.identity.mock import SyntheticIdentityAdapter
from campus247.presentation.identity import IdentityMiddleware
from campus247.presentation.tickets import create_ticket_router


@pytest.fixture
def setup_app():
    app = FastAPI()
    identity_adapter = SyntheticIdentityAdapter(secret_key="secret-test-key-247")
    app.add_middleware(IdentityMiddleware, adapter=identity_adapter)

    signing_key = "secret-signing-key-247"
    token_svc = ConfirmationTokenService(signing_key=signing_key)
    policy_engine = StudentPolicyEngine()
    preview_svc = TicketPreviewService(confirmation_service=token_svc, policy_engine=policy_engine)
    idempotency_ledger = IdempotencyLedger()
    audit_writer = AuditWriter()

    confirm_svc = TicketConfirmationService(
        confirmation_service=token_svc,
        idempotency_ledger=idempotency_ledger,
        audit_writer=audit_writer,
    )

    router = create_ticket_router(preview_svc=preview_svc, confirm_svc=confirm_svc)
    app.include_router(router)

    client = TestClient(app)
    return client, identity_adapter


def test_ticket_preview_unauthenticated(setup_app):
    client, _ = setup_app
    resp = client.post(
        "/v1/tickets/preview",
        json={
            "category": "GENERAL_SUPPORT",
            "priority": "NORMAL",
            "subject": "Cần hỗ trợ",
            "description": "Chi tiết yêu cầu",
        },
    )
    assert resp.status_code == 401


def test_ticket_preview_and_confirm_flow(setup_app):
    client, identity_adapter = setup_app
    student_id = "4b419a1b-6d41-7dfb-8943-2edd9f071385"
    token = identity_adapter.mint_token(student_id)
    headers = {"Authorization": f"Bearer {token}"}

    ticket_data = {
        "category": "GENERAL_SUPPORT",
        "priority": "NORMAL",
        "subject": "Hỗ trợ học vụ",
        "description": "Thắc mắc lịch thi",
    }

    # 1. Preview
    resp_preview = client.post(
        "/v1/tickets/preview",
        headers=headers,
        json=ticket_data,
    )
    assert resp_preview.status_code == 201
    prev_json = resp_preview.json()
    assert "preview_id" in prev_json
    assert "confirmation_token" in prev_json

    preview_id = prev_json["preview_id"]
    conf_token = prev_json["confirmation_token"]

    # 2. Confirm
    confirm_payload = {
        "confirmation_token": conf_token,
        "idempotency_key": "test-idem-key-1234567890",
        "payload": ticket_data,
    }
    resp_confirm = client.post(
        f"/v1/tickets/{preview_id}/confirm",
        headers=headers,
        json=confirm_payload,
    )
    assert resp_confirm.status_code == 201
    conf_json = resp_confirm.json()
    assert "ticket_id" in conf_json
    assert conf_json["status"] == "OPEN"
    assert conf_json["is_replay"] is False

    # 3. Idempotent replay
    resp_replay = client.post(
        f"/v1/tickets/{preview_id}/confirm",
        headers=headers,
        json=confirm_payload,
    )
    assert resp_replay.status_code == 201
    replay_json = resp_replay.json()
    assert replay_json["ticket_id"] == conf_json["ticket_id"]
    assert replay_json["is_replay"] is True
