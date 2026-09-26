from __future__ import annotations

from datetime import datetime, timezone, timedelta
import pytest

from campus247.application.audit.writer import AuditWriter
from campus247.application.staff.transfer import (
    StaffCaseTransferCommand,
    StaffCaseTransferResult,
    StaffCaseTransferService,
    TransferHistoryEntry,
)
from campus247.domain.handover.model import Handover, HandoverRiskLevel, HandoverStatus
from campus247.domain.shared.values import generate_uuid7
from campus247.ports.identity import IdentityContext, IdentityRole


def make_officer(
    user_id: str | None = None,
    unit_ids: tuple[str, ...] = ("STUDENT_SUPPORT_GENERAL", "ACADEMIC_POLICY"),
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
def service() -> StaffCaseTransferService:
    audit = AuditWriter()
    return StaffCaseTransferService(audit_writer=audit)


def test_transfer_case_success_retains_history_and_sla(service: StaffCaseTransferService):
    officer = make_officer()
    original_created_at = datetime.now(timezone.utc) - timedelta(hours=3)

    handover = Handover(
        id=generate_uuid7(),
        conversation_id=generate_uuid7(),
        requester_user_id=generate_uuid7(),
        queue_key="STUDENT_SUPPORT_GENERAL",
        reason_code="USER_REQUESTED_HUMAN",
        risk_level=HandoverRiskLevel.LOW,
        status=HandoverStatus.ASSIGNED,
        summary_redacted="Thắc mắc học phần chuyển nhượng",
        assigned_user_id=officer.subject_id,
        created_at=original_created_at,
        updated_at=original_created_at,
        version=2,
    )
    service.register_case(handover)

    cmd = StaffCaseTransferCommand(
        case_id=handover.id,
        target_queue="ACADEMIC_POLICY",
        reason="Câu hỏi liên quan quy chế đào tạo chuyên sâu",
    )

    result = service.transfer_case(officer, cmd)
    assert isinstance(result, StaffCaseTransferResult)
    assert result.case.queue_key == "ACADEMIC_POLICY"
    assert result.case.status == HandoverStatus.QUEUED
    assert result.case.assigned_user_id is None
    # Immutable SLA timestamp preserved
    assert result.case.created_at == original_created_at
    assert result.case.version == 3

    # History record verification
    history = service.get_case_history(handover.id)
    assert len(history) == 1
    entry = history[0]
    assert entry.from_queue == "STUDENT_SUPPORT_GENERAL"
    assert entry.to_queue == "ACADEMIC_POLICY"
    assert entry.transferred_by_user_id == officer.subject_id
    assert entry.previous_assignee_user_id == officer.subject_id
    assert entry.reason == cmd.reason


def test_transfer_invalid_destination_rejected_no_partial_state(service: StaffCaseTransferService):
    officer = make_officer()
    handover = Handover.create_queued(
        conversation_id=generate_uuid7(),
        requester_user_id=generate_uuid7(),
        queue_key="STUDENT_SUPPORT_GENERAL",
        reason_code="USER_REQUESTED_HUMAN",
        risk_level=HandoverRiskLevel.LOW,
        summary="Thắc mắc chung",
    )
    service.register_case(handover)

    cmd = StaffCaseTransferCommand(
        case_id=handover.id,
        target_queue="INVALID_UNKNOWN_QUEUE",
        reason="Lỗi đích đến",
    )

    with pytest.raises(ValueError, match="Invalid destination queue"):
        service.transfer_case(officer, cmd)

    # Verify no partial mutation
    stored = service.get_case(handover.id)
    assert stored.queue_key == "STUDENT_SUPPORT_GENERAL"
    assert len(service.get_case_history(handover.id)) == 0


def test_transfer_same_queue_rejected(service: StaffCaseTransferService):
    officer = make_officer()
    handover = Handover.create_queued(
        conversation_id=generate_uuid7(),
        requester_user_id=generate_uuid7(),
        queue_key="STUDENT_SUPPORT_GENERAL",
        reason_code="USER_REQUESTED_HUMAN",
        risk_level=HandoverRiskLevel.LOW,
        summary="Thắc mắc",
    )
    service.register_case(handover)

    cmd = StaffCaseTransferCommand(
        case_id=handover.id,
        target_queue="STUDENT_SUPPORT_GENERAL",
        reason="Chuyển trùng queue",
    )

    with pytest.raises(ValueError, match="Target queue cannot be the same"):
        service.transfer_case(officer, cmd)


def test_transfer_empty_reason_rejected(service: StaffCaseTransferService):
    officer = make_officer()
    handover = Handover.create_queued(
        conversation_id=generate_uuid7(),
        requester_user_id=generate_uuid7(),
        queue_key="STUDENT_SUPPORT_GENERAL",
        reason_code="USER_REQUESTED_HUMAN",
        risk_level=HandoverRiskLevel.LOW,
        summary="Thắc mắc",
    )
    service.register_case(handover)

    cmd = StaffCaseTransferCommand(
        case_id=handover.id,
        target_queue="ACADEMIC_POLICY",
        reason="   ",
    )

    with pytest.raises(ValueError, match="Transfer reason cannot be empty"):
        service.transfer_case(officer, cmd)


def test_transfer_terminal_state_rejected(service: StaffCaseTransferService):
    officer = make_officer()
    now = datetime.now(timezone.utc)
    handover = Handover(
        id=generate_uuid7(),
        conversation_id=generate_uuid7(),
        requester_user_id=generate_uuid7(),
        queue_key="STUDENT_SUPPORT_GENERAL",
        reason_code="USER_REQUESTED_HUMAN",
        risk_level=HandoverRiskLevel.LOW,
        status=HandoverStatus.RESOLVED,
        summary_redacted="Case đã đóng",
        created_at=now,
        updated_at=now,
        resolved_at=now,
    )
    service.register_case(handover)

    cmd = StaffCaseTransferCommand(
        case_id=handover.id,
        target_queue="ACADEMIC_POLICY",
        reason="Chuyển case đã kết thúc",
    )

    with pytest.raises(ValueError, match="Cannot transfer case in terminal status"):
        service.transfer_case(officer, cmd)


def test_transfer_unauthorized_officer_rejected(service: StaffCaseTransferService):
    officer = make_officer(unit_ids=("ACADEMIC_POLICY",))  # missing STUDENT_SUPPORT_GENERAL
    handover = Handover.create_queued(
        conversation_id=generate_uuid7(),
        requester_user_id=generate_uuid7(),
        queue_key="STUDENT_SUPPORT_GENERAL",
        reason_code="USER_REQUESTED_HUMAN",
        risk_level=HandoverRiskLevel.LOW,
        summary="Thắc mắc",
    )
    service.register_case(handover)

    cmd = StaffCaseTransferCommand(
        case_id=handover.id,
        target_queue="ACADEMIC_POLICY",
        reason="Chuyển case ngoài quyền",
    )

    with pytest.raises(PermissionError, match="outside officer's authorized queues"):
        service.transfer_case(officer, cmd)
