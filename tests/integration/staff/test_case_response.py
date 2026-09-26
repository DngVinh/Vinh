from __future__ import annotations

from datetime import datetime, timezone, timedelta
import pytest

from campus247.application.audit.writer import AuditWriter
from campus247.application.staff.respond import (
    AuditUnavailableError,
    StaffResponseCommand,
    StaffResponseResult,
    StaffResponseService,
    TimelineEvent,
)
from campus247.domain.handover.model import Handover, HandoverRiskLevel
from campus247.domain.shared.values import generate_uuid7
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


class FailingAuditWriter(AuditWriter):
    def record_event(self, *args, **kwargs):
        raise RuntimeError("Audit persistence disk failure")


@pytest.mark.asyncio
async def test_staff_response_success_appends_timeline_and_audit():
    audit = AuditWriter()
    service = StaffResponseService(audit_writer=audit)
    officer = make_officer()

    handover = Handover.create_queued(
        conversation_id=generate_uuid7(),
        requester_user_id=generate_uuid7(),
        queue_key="STUDENT_SUPPORT_GENERAL",
        reason_code="USER_REQUESTED_HUMAN",
        risk_level=HandoverRiskLevel.LOW,
        summary="Cần hướng dẫn",
    ).assign(officer.subject_id)
    service.register_case(handover)

    cmd = StaffResponseCommand(
        case_id=handover.id,
        content="Chào bạn, phòng Đào tạo đã tiếp nhận yêu cầu và sẽ hỗ trợ xử lý trong 24h.",
    )

    result = await service.respond_to_case(officer, cmd)
    assert isinstance(result, StaffResponseResult)
    assert result.event.actor_id == officer.subject_id
    assert result.event.actor_role == "SUPPORT_OFFICER"
    assert result.event.content_redacted == cmd.content
    assert result.event.sequence_no == 1

    timeline = service.get_case_timeline(handover.id)
    assert len(timeline) == 1
    assert timeline[0].id == result.event.id

    audit_records = audit.get_history()
    assert len(audit_records) == 1
    assert audit_records[0].action_code == "case.respond"
    assert audit_records[0].resource_id == handover.id


@pytest.mark.asyncio
async def test_audit_failure_fails_closed():
    failing_audit = FailingAuditWriter()
    service = StaffResponseService(audit_writer=failing_audit)
    officer = make_officer()

    handover = Handover.create_queued(
        conversation_id=generate_uuid7(),
        requester_user_id=generate_uuid7(),
        queue_key="STUDENT_SUPPORT_GENERAL",
        reason_code="USER_REQUESTED_HUMAN",
        risk_level=HandoverRiskLevel.LOW,
        summary="Cần hướng dẫn",
    ).assign(officer.subject_id)
    service.register_case(handover)

    cmd = StaffResponseCommand(
        case_id=handover.id,
        content="Thông điệp bảo mật",
    )

    with pytest.raises(AuditUnavailableError, match="Audit recording unavailable"):
        await service.respond_to_case(officer, cmd)

    # Fail closed: No timeline event was appended!
    timeline = service.get_case_timeline(handover.id)
    assert len(timeline) == 0


@pytest.mark.asyncio
async def test_response_unassigned_case_rejected():
    audit = AuditWriter()
    service = StaffResponseService(audit_writer=audit)
    officer = make_officer()
    other_officer = make_officer()

    handover = Handover.create_queued(
        conversation_id=generate_uuid7(),
        requester_user_id=generate_uuid7(),
        queue_key="STUDENT_SUPPORT_GENERAL",
        reason_code="USER_REQUESTED_HUMAN",
        risk_level=HandoverRiskLevel.LOW,
        summary="Cần hướng dẫn",
    ).assign(other_officer.subject_id)
    service.register_case(handover)

    cmd = StaffResponseCommand(
        case_id=handover.id,
        content="Cố gắng trả lời case người khác",
    )

    with pytest.raises(PermissionError, match="not assigned to this officer"):
        await service.respond_to_case(officer, cmd)


@pytest.mark.asyncio
async def test_response_out_of_scope_queue_rejected():
    audit = AuditWriter()
    service = StaffResponseService(audit_writer=audit)
    officer = make_officer(unit_ids=("STUDENT_SUPPORT_GENERAL",))

    handover = Handover.create_queued(
        conversation_id=generate_uuid7(),
        requester_user_id=generate_uuid7(),
        queue_key="SAFETY_RESTRICTED",
        reason_code="POTENTIAL_SELF_HARM",
        risk_level=HandoverRiskLevel.CRITICAL,
        summary="Case ngoài quyền",
    ).assign(officer.subject_id)
    service.register_case(handover)

    cmd = StaffResponseCommand(
        case_id=handover.id,
        content="Trả lời case ngoài hàng đợi được phân quyền",
    )

    with pytest.raises(PermissionError, match="outside officer's authorized queues"):
        await service.respond_to_case(officer, cmd)


@pytest.mark.asyncio
async def test_response_empty_content_rejected():
    audit = AuditWriter()
    service = StaffResponseService(audit_writer=audit)
    officer = make_officer()

    handover = Handover.create_queued(
        conversation_id=generate_uuid7(),
        requester_user_id=generate_uuid7(),
        queue_key="STUDENT_SUPPORT_GENERAL",
        reason_code="USER_REQUESTED_HUMAN",
        risk_level=HandoverRiskLevel.LOW,
        summary="Cần hướng dẫn",
    ).assign(officer.subject_id)
    service.register_case(handover)

    cmd = StaffResponseCommand(
        case_id=handover.id,
        content="    ",
    )

    with pytest.raises(ValueError, match="Response content cannot be empty"):
        await service.respond_to_case(officer, cmd)
