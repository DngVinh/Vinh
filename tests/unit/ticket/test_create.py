from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import sys
import pytest

ROOT = Path(__file__).resolve().parents[3]
API_SRC = ROOT / "services" / "api" / "src"
if str(API_SRC) not in sys.path:
    sys.path.insert(0, str(API_SRC))

from campus247.domain.ticket.model import (
    InvalidTicketStateError,
    InvalidTicketValidationError,
    Ticket,
    TicketCategory,
    TicketPriority,
    TicketStatus,
)


def test_create_ticket_draft_valid():
    ticket = Ticket.create_draft(
        requester_user_id="01923456-789a-7def-8123-456789abcde1",
        category=TicketCategory.GENERAL_SUPPORT,
        priority=TicketPriority.NORMAL,
        subject="Hỗ trợ đăng ký tín chỉ",
        description="Em cần hỗ trợ môn học bị trùng lịch.",
        queue_key="HUCE_GENERAL",
    )
    assert ticket.status == TicketStatus.DRAFT
    assert ticket.version == 1
    assert ticket.subject == "Hỗ trợ đăng ký tín chỉ"


def test_ticket_validation_errors():
    with pytest.raises(InvalidTicketValidationError, match="requester_user_id must be a valid UUIDv7"):
        Ticket.create_draft(
            requester_user_id="invalid-uuid",
            category=TicketCategory.GENERAL_SUPPORT,
            priority=TicketPriority.NORMAL,
            subject="Test",
            description="Desc",
            queue_key="HUCE_GENERAL",
        )

    with pytest.raises(InvalidTicketValidationError, match="subject cannot be empty"):
        Ticket.create_draft(
            requester_user_id="01923456-789a-7def-8123-456789abcde1",
            category=TicketCategory.GENERAL_SUPPORT,
            priority=TicketPriority.NORMAL,
            subject="",
            description="Desc",
            queue_key="HUCE_GENERAL",
        )


def test_ticket_creation_lifecycle():
    ticket = Ticket.create_draft(
        requester_user_id="01923456-789a-7def-8123-456789abcde1",
        category=TicketCategory.ACADEMIC_POLICY,
        priority=TicketPriority.HIGH,
        subject="Phúc khảo điểm",
        description="Nội dung phúc khảo",
        queue_key="HUCE_ACADEMIC",
    )
    assert ticket.status == TicketStatus.DRAFT

    req_conf = ticket.request_confirmation()
    assert req_conf.status == TicketStatus.CONFIRMATION_REQUIRED
    assert req_conf.version == 2

    opened = req_conf.confirm_create()
    assert opened.status == TicketStatus.OPEN
    assert opened.version == 3


def test_ticket_cancel_and_invalid_transition():
    ticket = Ticket.create_draft(
        requester_user_id="01923456-789a-7def-8123-456789abcde1",
        category=TicketCategory.OTHER,
        priority=TicketPriority.LOW,
        subject="Hủy thắc mắc",
        description="Đã tự giải quyết",
        queue_key="HUCE_GENERAL",
    )
    req_conf = ticket.request_confirmation()
    cancelled = req_conf.cancel()
    assert cancelled.status == TicketStatus.CANCELLED

    with pytest.raises(InvalidTicketStateError, match="Cannot transition from terminal state"):
        cancelled.confirm_create()

    # Cannot skip confirmation
    with pytest.raises(InvalidTicketStateError, match="Cannot confirm create from state DRAFT"):
        ticket.confirm_create()
