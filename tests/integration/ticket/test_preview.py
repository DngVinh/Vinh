from __future__ import annotations

from datetime import datetime, timezone, timedelta
from pathlib import Path
import sys
import pytest

ROOT = Path(__file__).resolve().parents[3]
API_SRC = ROOT / "services" / "api" / "src"
if str(API_SRC) not in sys.path:
    sys.path.insert(0, str(API_SRC))

from campus247.application.ticket.preview import (
    CreateTicketPayload,
    TicketPreviewResult,
    TicketPreviewService,
)
from campus247.domain.action.confirmation import ConfirmationTokenService
from campus247.domain.policy.student import StudentPolicyEngine
from campus247.ports.identity import AccountState, IdentityContext, IdentityRole


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
def preview_service() -> TicketPreviewService:
    token_svc = ConfirmationTokenService(signing_key="secret-signing-key-247")
    policy_engine = StudentPolicyEngine()
    return TicketPreviewService(confirmation_service=token_svc, policy_engine=policy_engine)


@pytest.mark.asyncio
async def test_preview_create_ticket_success(preview_service: TicketPreviewService, student_identity: IdentityContext):
    payload = CreateTicketPayload(
        category="GENERAL_SUPPORT",
        priority="NORMAL",
        subject="Hỗ trợ đăng ký tín chỉ",
        description="Em cần hỗ trợ mở thêm lớp.",
    )
    res = await preview_service.preview_create_ticket(student_identity, payload)
    assert res.preview_id is not None
    assert len(res.confirmation_token.split(".")) == 2
    assert res.action_type == "CREATE_TICKET"
    assert "Hỗ trợ đăng ký tín chỉ" in res.preview_summary


@pytest.mark.asyncio
async def test_preview_create_ticket_validation_error(preview_service: TicketPreviewService, student_identity: IdentityContext):
    payload = CreateTicketPayload(
        category="GENERAL_SUPPORT",
        priority="NORMAL",
        subject="",
        description="No subject",
    )
    with pytest.raises(ValueError, match="subject cannot be empty"):
        await preview_service.preview_create_ticket(student_identity, payload)


@pytest.mark.asyncio
async def test_preview_create_ticket_policy_denial():
    token_svc = ConfirmationTokenService(signing_key="secret-signing-key-247")
    policy_engine = StudentPolicyEngine()
    service = TicketPreviewService(confirmation_service=token_svc, policy_engine=policy_engine)

    now = datetime.now(timezone.utc)
    staff_identity = IdentityContext(
        subject_id="01923456-789a-7def-8123-456789abcde2",
        external_subject="syn_staff",
        issuer="urn:campus247:issuer:synthetic",
        roles=(IdentityRole.SUPPORT_OFFICER,),
        display_name="Cán bộ B",
        auth_time=now,
        expires_at=now + timedelta(hours=1),
    )

    payload = CreateTicketPayload(
        category="GENERAL_SUPPORT",
        priority="NORMAL",
        subject="Ticket staff",
        description="Staff should not create student ticket",
    )
    with pytest.raises(PermissionError, match="Action not permitted by policy"):
        await service.preview_create_ticket(staff_identity, payload)
