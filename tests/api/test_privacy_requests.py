from __future__ import annotations

from datetime import datetime, timezone, timedelta
from pathlib import Path
import re
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

from campus247.application.audit.writer import AuditWriter
from campus247.application.privacy.requests import PrivacyRequestService
from campus247.domain.shared.values import generate_uuid7
from campus247.ports.identity import IdentityContext, IdentityRole
from campus247.presentation.identity import IdentityMiddleware
from campus247.presentation.privacy_requests import create_privacy_request_router


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

    audit = AuditWriter()
    svc = PrivacyRequestService(audit_writer=audit)
    router = create_privacy_request_router(svc)
    app.include_router(router)

    client = TestClient(app)
    return client, identity_adapter, svc


def make_token(adapter: DummyIdentityAdapter, user_id: str) -> str:
    now = datetime.now(timezone.utc)
    ctx = IdentityContext(
        subject_id=user_id,
        external_subject=f"sub-{user_id[:8]}",
        issuer="https://auth.huce.edu.vn",
        roles=(IdentityRole.STUDENT,),
        display_name="Sinh Vien Test",
        student_code="SV123456",
        auth_time=now,
        expires_at=now + timedelta(hours=1),
    )
    token = f"tok-{user_id}"
    adapter.contexts[token] = ctx
    return token


def test_create_privacy_request_export_receipt(setup_app):
    client, adapter, _ = setup_app
    student_id = generate_uuid7()
    tok = make_token(adapter, student_id)

    payload = {"request_type": "EXPORT", "requester_note": "Yêu cầu trích xuất dữ liệu của tôi"}
    resp = client.post(
        "/v1/privacy/requests",
        headers={"Authorization": f"Bearer {tok}"},
        json=payload,
    )
    assert resp.status_code == 201
    assert "Location" in resp.headers
    data = resp.json()
    assert data["request_type"] == "EXPORT"
    assert data["status"] == "RECEIVED"
    assert re.match(r"^PRIV-[A-Z0-9]{8,32}$", data["tracking_reference"])


def test_create_privacy_request_correction_requires_summary(setup_app):
    client, adapter, _ = setup_app
    student_id = generate_uuid7()
    tok = make_token(adapter, student_id)

    payload = {"request_type": "CORRECTION"}
    resp = client.post(
        "/v1/privacy/requests",
        headers={"Authorization": f"Bearer {tok}"},
        json=payload,
    )
    assert resp.status_code == 422


def test_create_privacy_request_correction_success(setup_app):
    client, adapter, _ = setup_app
    student_id = generate_uuid7()
    tok = make_token(adapter, student_id)

    payload = {
        "request_type": "CORRECTION",
        "correction_summary": "Sửa số điện thoại liên lạc",
    }
    resp = client.post(
        "/v1/privacy/requests",
        headers={"Authorization": f"Bearer {tok}"},
        json=payload,
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["request_type"] == "CORRECTION"
    assert data["status"] == "RECEIVED"


def test_get_privacy_request_status_owner(setup_app):
    client, adapter, _ = setup_app
    student_id = generate_uuid7()
    tok = make_token(adapter, student_id)

    create_resp = client.post(
        "/v1/privacy/requests",
        headers={"Authorization": f"Bearer {tok}"},
        json={"request_type": "DELETION", "requester_note": "Yêu cầu xóa tài khoản"},
    )
    req_id = create_resp.json()["request_id"]

    status_resp = client.get(
        f"/v1/privacy/requests/{req_id}",
        headers={"Authorization": f"Bearer {tok}"},
    )
    assert status_resp.status_code == 200
    status_data = status_resp.json()
    assert status_data["request_id"] == req_id
    assert status_data["status"] == "RECEIVED"
    # Ensure internal notes or private case details are not disclosed
    assert "internal_notes" not in status_data


def test_get_privacy_request_status_foreign_id_denied_404(setup_app):
    client, adapter, _ = setup_app
    student_1 = generate_uuid7()
    student_2 = generate_uuid7()
    tok1 = make_token(adapter, student_1)
    tok2 = make_token(adapter, student_2)

    create_resp = client.post(
        "/v1/privacy/requests",
        headers={"Authorization": f"Bearer {tok1}"},
        json={"request_type": "EXPORT"},
    )
    req_id = create_resp.json()["request_id"]

    # Student 2 tries to access Student 1's request
    foreign_resp = client.get(
        f"/v1/privacy/requests/{req_id}",
        headers={"Authorization": f"Bearer {tok2}"},
    )
    assert foreign_resp.status_code == 404


def test_no_auto_delete_guarantee(setup_app):
    client, adapter, svc = setup_app
    student_id = generate_uuid7()
    tok = make_token(adapter, student_id)

    resp = client.post(
        "/v1/privacy/requests",
        headers={"Authorization": f"Bearer {tok}"},
        json={"request_type": "DELETION"},
    )
    assert resp.status_code == 201
    req_id = resp.json()["request_id"]

    # Verify that data is not deleted and status remains strictly RECEIVED (no legal completion claim)
    stored = svc.get_raw_record(req_id)
    assert stored is not None
    assert stored.status == "RECEIVED"
