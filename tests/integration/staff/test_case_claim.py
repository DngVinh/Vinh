from __future__ import annotations

import asyncio
from datetime import datetime, timezone, timedelta
import pytest

from campus247.application.audit.writer import AuditWriter
from campus247.application.staff.claim import (
    CaseClaimConflictError,
    CaseClaimRecord,
    CaseClaimResult,
    StaffCaseClaimService,
)
from campus247.domain.handover.model import Handover, HandoverRiskLevel
from campus247.domain.shared.values import generate_uuid7
from campus247.domain.ticket.model import Ticket, TicketCategory, TicketPriority
from campus247.ports.identity import IdentityContext, IdentityRole


def make_officer(
    user_id: str | None = None,
    unit_ids: tuple[str, ...] = ("STUDENT_SUPPORT_GENERAL",),
    role: IdentityRole = IdentityRole.SUPPORT_OFFICER,
) -> IdentityContext:
    now = datetime.now(timezone.utc)
    uid = user_id or generate_uuid7()
    return IdentityContext(
        subject_id=uid,
        external_subject=f"sub-{uid[:8]}",
        issuer="https://auth.huce.edu.vn",
        roles=(role,),
        display_name=f"Officer {uid[:4]}",
        student_code="SV123456" if role == IdentityRole.STUDENT else None,
        unit_ids=unit_ids,
        auth_time=now,
        expires_at=now + timedelta(hours=1),
    )


@pytest.fixture
def service() -> StaffCaseClaimService:
    audit = AuditWriter()
    return StaffCaseClaimService(audit_writer=audit)


@pytest.mark.asyncio
async def test_claim_case_success(service: StaffCaseClaimService):
    officer = make_officer(unit_ids=("STUDENT_SUPPORT_GENERAL",))
    case_id = generate_uuid7()
    case = CaseClaimRecord(
        case_id=case_id,
        queue_key="STUDENT_SUPPORT_GENERAL",
        assigned_user_id=None,
    )
    service.register_case(case)

    result = await service.claim_case(officer, case_id)
    assert result.status == "CLAIMED"
    assert result.assignee_id == officer.subject_id
    assert not result.is_conflict


@pytest.mark.asyncio
async def test_claim_handover_success(service: StaffCaseClaimService):
    officer = make_officer(unit_ids=("STUDENT_SUPPORT_GENERAL",))
    handover = Handover.create_queued(
        conversation_id=generate_uuid7(),
        requester_user_id=generate_uuid7(),
        queue_key="STUDENT_SUPPORT_GENERAL",
        reason_code="USER_REQUESTED_HUMAN",
        risk_level=HandoverRiskLevel.LOW,
        summary="Cần hỗ trợ học vụ",
    )
    service.register_case(handover)

    result = await service.claim_case(officer, handover.id)
    assert result.status == "CLAIMED"
    assert result.assignee_id == officer.subject_id


@pytest.mark.asyncio
async def test_concurrent_claims_exact_one_winner(service: StaffCaseClaimService):
    case_id = generate_uuid7()
    case = CaseClaimRecord(
        case_id=case_id,
        queue_key="STUDENT_SUPPORT_GENERAL",
        assigned_user_id=None,
    )
    service.register_case(case)

    officers = [make_officer() for _ in range(10)]

    results: list[CaseClaimResult] = await asyncio.gather(
        *(service.claim_case(o, case_id) for o in officers)
    )

    claimed_results = [r for r in results if r.status == "CLAIMED"]
    conflict_results = [r for r in results if r.status == "CONFLICT"]

    assert len(claimed_results) == 1
    assert len(conflict_results) == 9

    winner = claimed_results[0]
    for c in conflict_results:
        assert c.is_conflict
        assert c.conflict_owner_id == winner.assignee_id


@pytest.mark.asyncio
async def test_claim_case_unauthorized_role(service: StaffCaseClaimService):
    student = make_officer(role=IdentityRole.STUDENT)
    case_id = generate_uuid7()
    case = CaseClaimRecord(case_id=case_id, queue_key="STUDENT_SUPPORT_GENERAL")
    service.register_case(case)

    with pytest.raises(PermissionError, match="SUPPORT_OFFICER"):
        await service.claim_case(student, case_id)


@pytest.mark.asyncio
async def test_claim_case_out_of_scope_queue(service: StaffCaseClaimService):
    officer = make_officer(unit_ids=("STUDENT_SUPPORT_GENERAL",))
    case_id = generate_uuid7()
    case = CaseClaimRecord(case_id=case_id, queue_key="SAFETY_RESTRICTED")
    service.register_case(case)

    with pytest.raises(PermissionError, match="outside officer's authorized queues"):
        await service.claim_case(officer, case_id)


@pytest.mark.asyncio
async def test_claim_nonexistent_case(service: StaffCaseClaimService):
    officer = make_officer()
    with pytest.raises(KeyError, match="not found"):
        await service.claim_case(officer, generate_uuid7())
