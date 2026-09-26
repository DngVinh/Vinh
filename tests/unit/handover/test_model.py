from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import sys
import pytest

ROOT = Path(__file__).resolve().parents[3]
API_SRC = ROOT / "services" / "api" / "src"
if str(API_SRC) not in sys.path:
    sys.path.insert(0, str(API_SRC))

from campus247.domain.handover.model import (
    Handover,
    HandoverRiskLevel,
    HandoverStatus,
    InvalidHandoverStateError,
    InvalidHandoverValidationError,
)


def test_create_queued_handover():
    h = Handover.create_queued(
        conversation_id="01923456-789a-7def-8123-456789abcde1",
        requester_user_id="01923456-789a-7def-8123-456789abcde2",
        queue_key="UNIT_PSYCHOLOGY",
        reason_code="STUDENT_DISTRESS",
        risk_level=HandoverRiskLevel.HIGH,
        summary="Sinh viên báo căng thẳng thi cử.",
    )
    assert h.status == HandoverStatus.QUEUED
    assert h.risk_level == HandoverRiskLevel.HIGH
    assert h.version == 1


def test_handover_validation():
    with pytest.raises(InvalidHandoverValidationError, match="conversation_id must be a valid UUIDv7"):
        Handover.create_queued(
            conversation_id="invalid-id",
            requester_user_id="01923456-789a-7def-8123-456789abcde2",
            queue_key="UNIT_PSYCHOLOGY",
            reason_code="STUDENT_DISTRESS",
            risk_level=HandoverRiskLevel.HIGH,
            summary="Test",
        )


def test_handover_lifecycle():
    h = Handover.create_queued(
        conversation_id="01923456-789a-7def-8123-456789abcde1",
        requester_user_id="01923456-789a-7def-8123-456789abcde2",
        queue_key="UNIT_PSYCHOLOGY",
        reason_code="QUESTION",
        risk_level=HandoverRiskLevel.LOW,
        summary="Thắc mắc cần gặp chuyên viên.",
    )
    officer_id = "01923456-789a-7def-8123-456789abcde3"

    h = h.assign(officer_id)
    assert h.status == HandoverStatus.ASSIGNED
    assert h.assigned_user_id == officer_id

    h = h.accept()
    assert h.status == HandoverStatus.ACCEPTED
    assert h.accepted_at is not None

    h = h.start_work()
    assert h.status == HandoverStatus.IN_PROGRESS

    h = h.resolve()
    assert h.status == HandoverStatus.RESOLVED
    assert h.resolved_at is not None


def test_critical_handover_cannot_cancel():
    h = Handover.create_queued(
        conversation_id="01923456-789a-7def-8123-456789abcde1",
        requester_user_id="01923456-789a-7def-8123-456789abcde2",
        queue_key="UNIT_CRISIS",
        reason_code="CRISIS_EMERGENCY",
        risk_level=HandoverRiskLevel.CRITICAL,
        summary="Trường hợp khẩn cấp.",
    )
    with pytest.raises(InvalidHandoverStateError, match="Critical handover cannot be cancelled"):
        h.cancel()
