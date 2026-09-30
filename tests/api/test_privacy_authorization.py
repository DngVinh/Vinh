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
    PrivacyOperationAuthorizationService,
    LegalHoldRegistry,
)
from campus247.domain.shared.values import generate_uuid7
from campus247.ports.identity import IdentityContext, IdentityRole
from campus247.presentation.identity import IdentityMiddleware
from campus247.presentation.privacy import create_privacy_authorization_router


class DummyIdentityAdapter:
    def __init__(self):
        self.contexts: dict[str, IdentityContext] = {}

    def resolve_token(self, token: str) -> IdentityContext:
        if token in self.contexts:
            return self.contexts[token]
        raise ValueError("Invalid token")


def make_token(
    adapter: DummyIdentityAdapter,
    user_id: str,
    role: IdentityRole = IdentityRole.STUDENT,
) -> str:
    now = datetime.now(timezone.utc)
    ctx = IdentityContext(
        subject_id=user_id,
        external_subject=f"sub-{user_id[:8]}",
        issuer="https://auth.huce.edu.vn",
        roles=(role,),
        display_name=f"User {user_id[:6]}",
        student_code="SV123456" if role == IdentityRole.STUDENT else None,
        auth_time=now,
        expires_at=now + timedelta(hours=1),
    )
    token = f"tok-{user_id}"
    adapter.contexts[token] = ctx
    return token


@pytest.fixture
def privacy_system():
    notice = PrivacyNoticeConfig(
        notice_id=generate_uuid7(),
        version="1.0.0",
        effective_at=datetime.now(timezone.utc),
        status="ACTIVE",
        disclaimer={"statement": "HUCE demo synthetic data only"},
        data_categories=["ACCOUNT_CONTEXT", "CONVERSATION_CONTENT", "REQUEST_METADATA", "AUDIT_METADATA"],
        purposes=["SERVICE_DELIVERY", "QUALITY_FEEDBACK", "DATA_PORTABILITY", "ACCOUNT_CLOSURE"],
        retention_summary=[{"data_class": "ACCOUNT_CONTEXT", "configured_rule": "PRIV-RET-001"}],
    )
    audit = AuditWriter()
    consent_svc = PrivacyConsentService(active_notice=notice, audit_writer=audit)
    legal_holds = LegalHoldRegistry()
    authz_svc = PrivacyOperationAuthorizationService(
        consent_service=consent_svc,
        legal_hold_registry=legal_holds,
        audit_writer=audit,
    )

    app = FastAPI()
    identity_adapter = DummyIdentityAdapter()
    app.add_middleware(IdentityMiddleware, adapter=identity_adapter)

    router = create_privacy_authorization_router(
        consent_service=consent_svc,
        authz_service=authz_svc,
    )
    app.include_router(router)

    client = TestClient(app)
    return client, identity_adapter, consent_svc, legal_holds, authz_svc


def test_purpose_limited_and_subject_authorized_success(privacy_system):
    """AC-TASK-API-PRIVFIX-001-01: Valid purpose and subject authorized queues durable work."""
    client, adapter, consent_svc, _, _ = privacy_system
    user_id = generate_uuid7()
    token = make_token(adapter, user_id)

    # Record granted consent for feedback/export
    consent_svc.record_consent(
        actor=adapter.contexts[token],
        purpose="QUALITY_FEEDBACK",
        decision="GRANTED",
        notice_version="1.0.0",
    )

    payload = {
        "operation_type": "EXPORT",
        "target_subject_id": user_id,
        "purpose": "DATA_PORTABILITY",
        "scope": ["ACCOUNT_CONTEXT", "CONVERSATION_CONTENT"],
    }
    resp = client.post(
        "/v1/privacy/operations",
        headers={"Authorization": f"Bearer {token}"},
        json=payload,
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["operation_type"] == "EXPORT"
    assert data["status"] == "ACCEPTED"
    assert "tracking_reference" in data
    assert "operation_id" in data


def test_absent_consent_rejected_fail_closed(privacy_system):
    """AC-TASK-API-PRIVFIX-001-02: Absent consent cannot be treated as implicit approval."""
    client, adapter, _, _, _ = privacy_system
    user_id = generate_uuid7()
    token = make_token(adapter, user_id)

    # No consent ever granted for optional purpose
    payload = {
        "operation_type": "EXPORT",
        "target_subject_id": user_id,
        "purpose": "OPTIONAL_PERSONALIZATION",
        "scope": ["CONVERSATION_CONTENT"],
    }
    resp = client.post(
        "/v1/privacy/operations",
        headers={"Authorization": f"Bearer {token}"},
        json=payload,
    )
    assert resp.status_code == 403
    err = resp.json()
    assert "detail" in err or "title" in err
    detail_str = str(err).lower()
    assert "consent" in detail_str


def test_revoked_consent_rejected_fail_closed(privacy_system):
    """AC-TASK-API-PRIVFIX-001-02: Revoked consent cannot be treated as implicit approval."""
    client, adapter, consent_svc, _, _ = privacy_system
    user_id = generate_uuid7()
    token = make_token(adapter, user_id)

    # First grant, then withdraw
    consent_svc.record_consent(
        actor=adapter.contexts[token],
        purpose="QUALITY_FEEDBACK",
        decision="GRANTED",
        notice_version="1.0.0",
    )
    consent_svc.record_consent(
        actor=adapter.contexts[token],
        purpose="QUALITY_FEEDBACK",
        decision="WITHDRAWN",
        notice_version="1.0.0",
    )

    payload = {
        "operation_type": "EXPORT",
        "target_subject_id": user_id,
        "purpose": "QUALITY_FEEDBACK",
        "scope": ["CONVERSATION_CONTENT"],
    }
    resp = client.post(
        "/v1/privacy/operations",
        headers={"Authorization": f"Bearer {token}"},
        json=payload,
    )
    assert resp.status_code == 403
    detail_str = str(resp.json()).lower()
    assert "consent" in detail_str


def test_cross_subject_unauthorized_discloses_no_metadata(privacy_system):
    """AC-TASK-API-PRIVFIX-001-03: Denied requests disclose no cross-subject existence or protected metadata."""
    client, adapter, _, _, _ = privacy_system
    student_a = generate_uuid7()
    student_b = generate_uuid7()
    token_a = make_token(adapter, student_a, role=IdentityRole.STUDENT)

    # Student A tries to invoke operation targeting Student B
    payload = {
        "operation_type": "EXPORT",
        "target_subject_id": student_b,
        "purpose": "DATA_PORTABILITY",
        "scope": ["ACCOUNT_CONTEXT"],
    }
    resp = client.post(
        "/v1/privacy/operations",
        headers={"Authorization": f"Bearer {token_a}"},
        json=payload,
    )
    # Fail closed: must not return Student B info or confirm Student B existence
    assert resp.status_code in (403, 404)
    resp_text = resp.text
    assert student_b not in resp_text
    assert "SV123456" not in resp_text


def test_legal_hold_blocks_erasure(privacy_system):
    """AC-TASK-API-PRIVFIX-001-01 & AC-TASK-API-PRIVFIX-001-03: Legal hold conflicts block erasure."""
    client, adapter, _, legal_holds, _ = privacy_system
    user_id = generate_uuid7()
    token = make_token(adapter, user_id)

    # Place legal hold on student
    legal_holds.add_hold(
        user_id=user_id,
        reason="Disciplinary and academic record investigation",
        hold_reference="HOLD-2026-09-001",
    )

    payload = {
        "operation_type": "ERASURE",
        "target_subject_id": user_id,
        "purpose": "ACCOUNT_CLOSURE",
        "scope": ["ACCOUNT_CONTEXT"],
    }
    resp = client.post(
        "/v1/privacy/operations",
        headers={"Authorization": f"Bearer {token}"},
        json=payload,
    )
    assert resp.status_code == 409
    detail_str = str(resp.json()).lower()
    assert "legal hold" in detail_str


def test_overbroad_scope_rejected_unprocessable(privacy_system):
    """AC-TASK-API-PRIVFIX-001-01: Invalid or overbroad scope rejected."""
    client, adapter, _, _, _ = privacy_system
    user_id = generate_uuid7()
    token = make_token(adapter, user_id)

    payload = {
        "operation_type": "EXPORT",
        "target_subject_id": user_id,
        "purpose": "DATA_PORTABILITY",
        "scope": ["ACCOUNT_CONTEXT", "UNAUTHORIZED_SYSTEM_INTERNALS"],
    }
    resp = client.post(
        "/v1/privacy/operations",
        headers={"Authorization": f"Bearer {token}"},
        json=payload,
    )
    assert resp.status_code == 422


def test_duplicate_pending_operation_conflict(privacy_system):
    """AC-TASK-API-PRIVFIX-001-01: Duplicate in-flight operations rejected with 409."""
    client, adapter, _, _, _ = privacy_system
    user_id = generate_uuid7()
    token = make_token(adapter, user_id)

    payload = {
        "operation_type": "EXPORT",
        "target_subject_id": user_id,
        "purpose": "DATA_PORTABILITY",
        "scope": ["ACCOUNT_CONTEXT"],
    }
    resp1 = client.post(
        "/v1/privacy/operations",
        headers={"Authorization": f"Bearer {token}"},
        json=payload,
    )
    assert resp1.status_code == 201

    # Duplicate same operation while pending
    resp2 = client.post(
        "/v1/privacy/operations",
        headers={"Authorization": f"Bearer {token}"},
        json=payload,
    )
    assert resp2.status_code == 409
    detail_str = str(resp2.json()).lower()
    assert "duplicate" in detail_str or "in-flight" in detail_str or "conflict" in detail_str


def test_staff_authorized_delegate_path(privacy_system):
    """Staff with appropriate role can submit request for subject."""
    client, adapter, _, _, _ = privacy_system
    staff_id = generate_uuid7()
    target_student_id = generate_uuid7()
    token_staff = make_token(adapter, staff_id, role=IdentityRole.SUPPORT_OFFICER)

    payload = {
        "operation_type": "EXPORT",
        "target_subject_id": target_student_id,
        "purpose": "DATA_PORTABILITY",
        "scope": ["ACCOUNT_CONTEXT"],
        "requester_note": "Assisting student per in-person authorization.",
    }
    resp = client.post(
        "/v1/privacy/operations",
        headers={"Authorization": f"Bearer {token_staff}"},
        json=payload,
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["status"] == "ACCEPTED"
