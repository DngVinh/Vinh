from __future__ import annotations

from datetime import datetime, timezone, timedelta
import pytest

from campus247.application.action.idempotency import IdempotencyLedger
from campus247.application.audit.writer import AuditWriter
from campus247.application.handover.create import (
    CreateHandoverCommand,
    HandoverCreationService,
    HandoverCreationResult,
    route_handover,
)
from campus247.domain.handover.model import HandoverRiskLevel, HandoverStatus
from campus247.domain.shared.values import generate_uuid7
from campus247.ports.identity import IdentityContext


from campus247.ports.identity import IdentityContext, IdentityRole


def make_actor(role: IdentityRole = IdentityRole.STUDENT) -> IdentityContext:
    now = datetime.now(timezone.utc)
    return IdentityContext(
        subject_id=generate_uuid7(),
        external_subject="sub-test-01",
        issuer="https://auth.huce.edu.vn",
        roles=(role,),
        display_name="Sinh Vien Test",
        student_code="SV123456" if role == IdentityRole.STUDENT else None,
        auth_time=now,
        expires_at=now + timedelta(hours=1),
    )


@pytest.fixture
def service() -> HandoverCreationService:
    ledger = IdempotencyLedger()
    audit = AuditWriter()
    return HandoverCreationService(idempotency_ledger=ledger, audit_writer=audit)


def test_create_handover_success_user_request(service: HandoverCreationService) -> None:
    actor = make_actor()
    conv_id = generate_uuid7()
    cmd = CreateHandoverCommand(
        conversation_id=conv_id,
        category="USER_REQUEST",
        severity="normal",
        summary="Cần gặp cán bộ giải đáp thắc mắc về học phần",
        reason_codes=["USER_REQUESTED_HUMAN"],
        related_reference_ids=["REF-001"],
    )

    result = service.create_handover(actor=actor, command=cmd)

    assert isinstance(result, HandoverCreationResult)
    assert not result.is_replay
    handover = result.handover
    assert handover.conversation_id == conv_id
    assert handover.requester_user_id == actor.subject_id
    assert handover.queue_key == "STUDENT_SUPPORT_GENERAL"
    assert handover.status == HandoverStatus.QUEUED
    assert handover.risk_level in (HandoverRiskLevel.LOW, HandoverRiskLevel.MEDIUM)
    assert handover.summary_redacted == cmd.summary

    # Truthful receipt verification
    receipt = result.receipt
    assert receipt.handover_id == handover.id
    assert receipt.queue_key == "STUDENT_SUPPORT_GENERAL"
    assert receipt.status == "QUEUED"
    assert "QUEUED" in receipt.truthful_notice
    assert "thời gian thực" in receipt.truthful_notice


def test_routing_sensitive_wellbeing_deterministic(service: HandoverCreationService) -> None:
    actor = make_actor()
    conv_id = generate_uuid7()
    cmd = CreateHandoverCommand(
        conversation_id=conv_id,
        category="SENSITIVE_WELLBEING",
        severity="high",
        summary="Nguy cơ tự hại được phát hiện",
        reason_codes=["POTENTIAL_SELF_HARM"],
    )

    result = service.create_handover(actor=actor, command=cmd)
    assert result.handover.queue_key == "SAFETY_RESTRICTED"
    assert result.handover.risk_level == HandoverRiskLevel.CRITICAL


def test_routing_privacy_security_deterministic(service: HandoverCreationService) -> None:
    actor = make_actor()
    conv_id = generate_uuid7()
    cmd = CreateHandoverCommand(
        conversation_id=conv_id,
        category="PRIVACY_OR_SECURITY",
        severity="critical",
        summary="Nghi ngờ rò rỉ dữ liệu cá nhân",
        reason_codes=["DATA_PRIVACY_INCIDENT"],
    )

    result = service.create_handover(actor=actor, command=cmd)
    assert result.handover.queue_key == "PRIVACY_SECURITY"
    assert result.handover.risk_level == HandoverRiskLevel.CRITICAL


def test_routing_academic_rights(service: HandoverCreationService) -> None:
    actor = make_actor()
    conv_id = generate_uuid7()
    cmd = CreateHandoverCommand(
        conversation_id=conv_id,
        category="ACADEMIC_RIGHTS",
        severity="normal",
        summary="Khiếu nại điểm thi kết thúc học phần",
        reason_codes=["ACADEMIC_RIGHTS_IMPACT"],
    )

    result = service.create_handover(actor=actor, command=cmd)
    assert result.handover.queue_key == "ACADEMIC_POLICY"


def test_routing_tool_uncertainty(service: HandoverCreationService) -> None:
    actor = make_actor()
    conv_id = generate_uuid7()
    cmd = CreateHandoverCommand(
        conversation_id=conv_id,
        category="TOOL_UNCERTAINTY",
        severity="normal",
        summary="Tool thất bại không thể xác định kết quả",
        reason_codes=["TOOL_OR_INTEGRATION_FAILURE"],
    )

    result = service.create_handover(actor=actor, command=cmd)
    assert result.handover.queue_key == "OPERATIONS_FALLBACK"


def test_idempotent_creation(service: HandoverCreationService) -> None:
    actor = make_actor()
    conv_id = generate_uuid7()
    cmd = CreateHandoverCommand(
        conversation_id=conv_id,
        category="USER_REQUEST",
        severity="normal",
        summary="Cần hỗ trợ xin xác nhận sinh viên",
        reason_codes=["USER_REQUESTED_HUMAN"],
    )

    res1 = service.create_handover(actor=actor, command=cmd, idempotency_key="idemp-hitl-0000001")
    res2 = service.create_handover(actor=actor, command=cmd, idempotency_key="idemp-hitl-0000001")

    assert not res1.is_replay
    assert res2.is_replay
    assert res1.handover.id == res2.handover.id


def test_validation_failure_invalid_category(service: HandoverCreationService) -> None:
    actor = make_actor()
    conv_id = generate_uuid7()
    cmd = CreateHandoverCommand(
        conversation_id=conv_id,
        category="INVALID_CAT",
        severity="normal",
        summary="Kiểm tra phân loại lỗi",
        reason_codes=["USER_REQUESTED_HUMAN"],
    )

    with pytest.raises(ValueError, match="Invalid handover category"):
        service.create_handover(actor=actor, command=cmd)


def test_validation_failure_invalid_reason_code(service: HandoverCreationService) -> None:
    actor = make_actor()
    conv_id = generate_uuid7()
    cmd = CreateHandoverCommand(
        conversation_id=conv_id,
        category="USER_REQUEST",
        severity="normal",
        summary="Kiểm tra mã lý do",
        reason_codes=["INVALID_REASON"],
    )

    with pytest.raises(ValueError, match="Invalid reason code"):
        service.create_handover(actor=actor, command=cmd)


def test_validation_failure_empty_summary(service: HandoverCreationService) -> None:
    actor = make_actor()
    conv_id = generate_uuid7()
    cmd = CreateHandoverCommand(
        conversation_id=conv_id,
        category="USER_REQUEST",
        severity="normal",
        summary="   ",
        reason_codes=["USER_REQUESTED_HUMAN"],
    )

    with pytest.raises(ValueError, match="Summary cannot be empty"):
        service.create_handover(actor=actor, command=cmd)
