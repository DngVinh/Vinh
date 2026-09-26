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

from campus247.domain.handover.model import Handover, HandoverRiskLevel
from campus247.domain.shared.values import generate_uuid7
from campus247.infrastructure.identity.mock import SyntheticIdentityAdapter
from campus247.ports.identity import IdentityContext, IdentityRole
from campus247.presentation.identity import IdentityMiddleware
from campus247.presentation.handovers import create_handover_router


class DummyIdentityAdapter:
    def __init__(self):
        self.contexts: dict[str, IdentityContext] = {}

    def resolve_token(self, token: str) -> IdentityContext:
        if token in self.contexts:
            return self.contexts[token]
        raise ValueError("Invalid token")


@pytest.fixture
def setup_app():
    app = FastAPI()
    identity_adapter = DummyIdentityAdapter()
    app.add_middleware(IdentityMiddleware, adapter=identity_adapter)

    handover_store: dict[str, Handover] = {}
    router = create_handover_router(store=handover_store)
    app.include_router(router)

    client = TestClient(app)
    return client, identity_adapter, handover_store


def make_token(
    adapter: DummyIdentityAdapter,
    user_id: str,
    role: IdentityRole = IdentityRole.SUPPORT_OFFICER,
    unit_ids: tuple[str, ...] = ("STUDENT_SUPPORT_GENERAL",),
) -> str:
    now = datetime.now(timezone.utc)
    ctx = IdentityContext(
        subject_id=user_id,
        external_subject=f"sub-{user_id[:8]}",
        issuer="https://auth.huce.edu.vn",
        roles=(role,),
        display_name="Can Bo Test",
        student_code="SV123456" if role == IdentityRole.STUDENT else None,
        unit_ids=unit_ids,
        auth_time=now,
        expires_at=now + timedelta(hours=1),
    )
    token = f"tok-{user_id}"
    adapter.contexts[token] = ctx
    return token


def test_list_staff_handovers_unauthenticated(setup_app):
    client, _, _ = setup_app
    resp = client.get("/v1/staff/handovers")
    assert resp.status_code == 401


def test_list_staff_handovers_forbidden_for_student(setup_app):
    client, adapter, _ = setup_app
    student_id = generate_uuid7()
    token = make_token(adapter, student_id, role=IdentityRole.STUDENT)
    resp = client.get("/v1/staff/handovers", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 403


def test_list_staff_handovers_missing_scope(setup_app):
    client, adapter, _ = setup_app
    officer_id = generate_uuid7()
    token = make_token(adapter, officer_id, role=IdentityRole.SUPPORT_OFFICER, unit_ids=())
    resp = client.get("/v1/staff/handovers", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 403


def test_list_staff_handovers_queue_scoped(setup_app):
    client, adapter, store = setup_app
    officer_id = generate_uuid7()
    token = make_token(adapter, officer_id, role=IdentityRole.SUPPORT_OFFICER, unit_ids=("STUDENT_SUPPORT_GENERAL",))

    h1 = Handover.create_queued(
        conversation_id=generate_uuid7(),
        requester_user_id=generate_uuid7(),
        queue_key="STUDENT_SUPPORT_GENERAL",
        reason_code="USER_REQUESTED_HUMAN",
        risk_level=HandoverRiskLevel.LOW,
        summary="Thắc mắc học vụ chung",
    )
    h2 = Handover.create_queued(
        conversation_id=generate_uuid7(),
        requester_user_id=generate_uuid7(),
        queue_key="SAFETY_RESTRICTED",
        reason_code="POTENTIAL_SELF_HARM",
        risk_level=HandoverRiskLevel.CRITICAL,
        summary="Cảnh báo an toàn tâm lý",
    )
    store[h1.id] = h1
    store[h2.id] = h2

    resp = client.get("/v1/staff/handovers", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["items"]) == 1
    assert data["items"][0]["handover_id"] == h1.id
    assert data["items"][0]["queue_key"] == "STUDENT_SUPPORT_GENERAL"


def test_list_staff_handovers_unauthorized_queue_param(setup_app):
    client, adapter, _ = setup_app
    officer_id = generate_uuid7()
    token = make_token(adapter, officer_id, role=IdentityRole.SUPPORT_OFFICER, unit_ids=("STUDENT_SUPPORT_GENERAL",))

    resp = client.get(
        "/v1/staff/handovers?queue_key=SAFETY_RESTRICTED",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 403


def test_get_handover_success_and_forbidden(setup_app):
    client, adapter, store = setup_app
    officer_id = generate_uuid7()
    token = make_token(adapter, officer_id, role=IdentityRole.SUPPORT_OFFICER, unit_ids=("STUDENT_SUPPORT_GENERAL",))

    h1 = Handover.create_queued(
        conversation_id=generate_uuid7(),
        requester_user_id=generate_uuid7(),
        queue_key="STUDENT_SUPPORT_GENERAL",
        reason_code="USER_REQUESTED_HUMAN",
        risk_level=HandoverRiskLevel.LOW,
        summary="Hỗ trợ thông tin",
    )
    h2 = Handover.create_queued(
        conversation_id=generate_uuid7(),
        requester_user_id=generate_uuid7(),
        queue_key="SAFETY_RESTRICTED",
        reason_code="POTENTIAL_SELF_HARM",
        risk_level=HandoverRiskLevel.CRITICAL,
        summary="Nội dung an toàn bí mật",
    )
    store[h1.id] = h1
    store[h2.id] = h2

    resp = client.get(f"/v1/handovers/{h1.id}", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert resp.headers.get("etag") == f'"{h1.version}"'
    assert resp.json()["handover_id"] == h1.id

    resp_out_of_scope = client.get(f"/v1/handovers/{h2.id}", headers={"Authorization": f"Bearer {token}"})
    assert resp_out_of_scope.status_code in (403, 404)
