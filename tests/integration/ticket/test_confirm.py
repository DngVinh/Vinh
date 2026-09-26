from __future__ import annotations

from datetime import datetime, timezone, timedelta
from pathlib import Path
import sys
import pytest

ROOT = Path(__file__).resolve().parents[3]
API_SRC = ROOT / "services" / "api" / "src"
if str(API_SRC) not in sys.path:
    sys.path.insert(0, str(API_SRC))

from campus247.application.action.idempotency import IdempotencyLedger
from campus247.application.audit.writer import AuditWriter
from campus247.application.ticket.confirm import TicketConfirmationService
from campus247.application.ticket.preview import (
    CreateTicketPayload,
    TicketPreviewService,
)
from campus247.domain.action.confirmation import ConfirmationTokenService
from campus247.domain.policy.student import StudentPolicyEngine
from campus247.domain.ticket.model import TicketStatus
from campus247.ports.identity import IdentityContext, IdentityRole


@pytest.fixture
def student_identity() -> IdentityContext:
    now = datetime.now(timezone.utc)
    return IdentityContext(
        subject_id="01923456-789a-7def-8123-456789abcde1",
        external_subject="syn_01923456",
        issuer="urn:campus247:issuer:synthetic",
        roles=(IdentityRole.STUDENT,),
        display_name="Sinh viên A",
        student_code="651234",
        auth_time=now,
        expires_at=now + timedelta(hours=1),
    )


@pytest.fixture
def services():
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
    return preview_svc, confirm_svc, audit_writer


@pytest.mark.asyncio
async def test_confirm_ticket_creation_success(services, student_identity):
    preview_svc, confirm_svc, audit_writer = services

    payload = CreateTicketPayload(
        category="GENERAL_SUPPORT",
        priority="NORMAL",
        subject="Hỗ trợ thời khóa biểu",
        description="Môn học bị trùng phòng.",
    )
    preview = await preview_svc.preview_create_ticket(student_identity, payload)

    res = await confirm_svc.confirm_ticket(
        actor=student_identity,
        preview_id=preview.preview_id,
        confirmation_token=preview.confirmation_token,
        idempotency_key="idem-key-1234567890abcdef",
        payload=payload,
    )

    assert res.ticket.status == TicketStatus.OPEN
    assert res.is_replay is False
    assert len(audit_writer._log) == 1
    assert audit_writer._log[0].action_code == "ticket.confirm_create"


@pytest.mark.asyncio
async def test_confirm_ticket_creation_idempotent_replay(services, student_identity):
    preview_svc, confirm_svc, audit_writer = services

    payload = CreateTicketPayload(
        category="GENERAL_SUPPORT",
        priority="NORMAL",
        subject="Hỗ trợ thời khóa biểu",
        description="Môn học bị trùng phòng.",
    )
    preview = await preview_svc.preview_create_ticket(student_identity, payload)

    res1 = await confirm_svc.confirm_ticket(
        actor=student_identity,
        preview_id=preview.preview_id,
        confirmation_token=preview.confirmation_token,
        idempotency_key="idem-key-1234567890abcdef",
        payload=payload,
    )

    res2 = await confirm_svc.confirm_ticket(
        actor=student_identity,
        preview_id=preview.preview_id,
        confirmation_token=preview.confirmation_token,
        idempotency_key="idem-key-1234567890abcdef",
        payload=payload,
    )

    assert res2.is_replay is True
    assert res2.ticket.id == res1.ticket.id
    # Exactly one audit event recorded
    assert len(audit_writer._log) == 1


@pytest.mark.asyncio
async def test_confirm_ticket_invalid_token(services, student_identity):
    _, confirm_svc, _ = services
    payload = CreateTicketPayload(
        category="GENERAL_SUPPORT",
        priority="NORMAL",
        subject="Hỗ trợ",
        description="Chi tiết",
    )

    with pytest.raises(ValueError, match="Invalid confirmation token"):
        await confirm_svc.confirm_ticket(
            actor=student_identity,
            preview_id="01923456-789a-7def-8123-456789abcde1",
            confirmation_token="invalid.token",
            idempotency_key="idem-key-1234567890abcdef",
            payload=payload,
        )
