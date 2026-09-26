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

from campus247.application.audit.writer import AuditWriter
from campus247.application.privacy.consent import (
    PrivacyConsentService,
    PrivacyNoticeConfig,
)
from campus247.domain.shared.values import generate_uuid7
from campus247.ports.identity import IdentityContext, IdentityRole
from campus247.presentation.identity import IdentityMiddleware
from campus247.presentation.privacy_notice import create_privacy_router


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
    notice = PrivacyNoticeConfig(
        notice_id=generate_uuid7(),
        version="1.0.0",
        effective_at=datetime.now(timezone.utc),
        status="ACTIVE",
        disclaimer={"statement": "HUCE demo synthetic data only"},
        data_categories=["ACCOUNT_CONTEXT", "CONVERSATION_CONTENT", "REQUEST_METADATA", "AUDIT_METADATA"],
        purposes=["SERVICE_DELIVERY", "SAFETY_HANDOVER", "QUALITY_FEEDBACK", "SECURITY_AUDIT"],
        retention_summary=[{"data_class": "ACCOUNT_CONTEXT", "configured_rule": "PRIV-RET-001"}],
    )
    consent_svc = PrivacyConsentService(active_notice=notice, audit_writer=audit)
    router = create_privacy_router(consent_svc)
    app.include_router(router)

    client = TestClient(app)
    return client, identity_adapter, consent_svc


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


def test_get_active_privacy_notice_public(setup_app):
    client, _, _ = setup_app
    resp = client.get("/v1/privacy/notice")
    assert resp.status_code == 200
    assert resp.headers.get("etag") == '"1.0.0"'
    data = resp.json()
    assert data["version"] == "1.0.0"
    assert data["status"] == "ACTIVE"


def test_get_notice_unavailable_fails_closed():
    app = FastAPI()
    audit = AuditWriter()
    consent_svc = PrivacyConsentService(active_notice=None, audit_writer=audit)
    router = create_privacy_router(consent_svc)
    app.include_router(router)
    client = TestClient(app)

    resp = client.get("/v1/privacy/notice")
    assert resp.status_code == 503


def test_list_consents_unauthenticated(setup_app):
    client, _, _ = setup_app
    resp = client.get("/v1/privacy/consents")
    assert resp.status_code == 401


def test_record_and_list_consent_flow(setup_app):
    client, adapter, _ = setup_app
    student_1 = generate_uuid7()
    student_2 = generate_uuid7()
    tok1 = make_token(adapter, student_1)
    tok2 = make_token(adapter, student_2)

    payload = {
        "purpose": "QUALITY_FEEDBACK",
        "decision": "GRANTED",
        "notice_version": "1.0.0",
    }
    resp = client.post(
        "/v1/privacy/consents",
        headers={"Authorization": f"Bearer {tok1}"},
        json=payload,
    )
    assert resp.status_code == 201
    assert "Location" in resp.headers
    data = resp.json()
    assert data["purpose"] == "QUALITY_FEEDBACK"
    assert data["decision"] == "GRANTED"

    # Verify student 1 sees the consent
    resp1 = client.get("/v1/privacy/consents", headers={"Authorization": f"Bearer {tok1}"})
    assert resp1.status_code == 200
    items1 = resp1.json()["items"]
    assert len(items1) == 1
    assert items1[0]["id"] == data["id"]

    # Verify student 2 does NOT see student 1's consent (isolation)
    resp2 = client.get("/v1/privacy/consents", headers={"Authorization": f"Bearer {tok2}"})
    assert resp2.status_code == 200
    assert len(resp2.json()["items"]) == 0


def test_record_consent_stale_notice_version_rejected(setup_app):
    client, adapter, _ = setup_app
    student_id = generate_uuid7()
    tok = make_token(adapter, student_id)

    payload = {
        "purpose": "QUALITY_FEEDBACK",
        "decision": "GRANTED",
        "notice_version": "0.9.0",
    }
    resp = client.post(
        "/v1/privacy/consents",
        headers={"Authorization": f"Bearer {tok}"},
        json=payload,
    )
    assert resp.status_code == 422


def test_record_consent_withdrawn_prospective(setup_app):
    client, adapter, _ = setup_app
    student_id = generate_uuid7()
    tok = make_token(adapter, student_id)

    payload = {
        "purpose": "OPTIONAL_PERSONALIZATION",
        "decision": "WITHDRAWN",
        "notice_version": "1.0.0",
    }
    resp = client.post(
        "/v1/privacy/consents",
        headers={"Authorization": f"Bearer {tok}"},
        json=payload,
    )
    assert resp.status_code == 201
    assert resp.json()["decision"] == "WITHDRAWN"
