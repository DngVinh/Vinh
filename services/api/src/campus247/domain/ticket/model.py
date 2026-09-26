from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime, timezone
from enum import StrEnum

from campus247.domain.shared.values import generate_uuid7, is_valid_uuid7


class TicketCategory(StrEnum):
    GENERAL_SUPPORT = "GENERAL_SUPPORT"
    ACADEMIC_POLICY = "ACADEMIC_POLICY"
    DOCUMENT_REQUEST_SUPPORT = "DOCUMENT_REQUEST_SUPPORT"
    FACILITY = "FACILITY"
    COMPLAINT = "COMPLAINT"
    OTHER = "OTHER"


class TicketPriority(StrEnum):
    LOW = "LOW"
    NORMAL = "NORMAL"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class TicketStatus(StrEnum):
    DRAFT = "DRAFT"
    CONFIRMATION_REQUIRED = "CONFIRMATION_REQUIRED"
    OPEN = "OPEN"
    ASSIGNED = "ASSIGNED"
    IN_PROGRESS = "IN_PROGRESS"
    WAITING_STUDENT = "WAITING_STUDENT"
    RESOLVED = "RESOLVED"
    CLOSED = "CLOSED"
    ESCALATED = "ESCALATED"
    CANCELLED = "CANCELLED"


TERMINAL_STATES = {TicketStatus.CLOSED, TicketStatus.CANCELLED}


class InvalidTicketValidationError(ValueError):
    pass


class InvalidTicketStateError(Exception):
    pass


@dataclass(frozen=True)
class Ticket:
    id: str
    requester_user_id: str
    category: TicketCategory
    priority: TicketPriority
    status: TicketStatus
    subject: str
    description_redacted: str
    queue_key: str
    created_at: datetime
    updated_at: datetime
    assigned_user_id: str | None = None
    sla_due_at: datetime | None = None
    resolved_at: datetime | None = None
    closed_at: datetime | None = None
    version: int = 1

    def __post_init__(self) -> None:
        if not is_valid_uuid7(self.requester_user_id):
            raise InvalidTicketValidationError(
                f"requester_user_id must be a valid UUIDv7 string, got: {self.requester_user_id}"
            )
        if not self.subject or not self.subject.strip():
            raise InvalidTicketValidationError("subject cannot be empty")
        if len(self.subject) > 200:
            raise InvalidTicketValidationError("subject cannot exceed 200 characters")
        if not self.description_redacted or not self.description_redacted.strip():
            raise InvalidTicketValidationError("description_redacted cannot be empty")

    @classmethod
    def create_draft(
        cls,
        requester_user_id: str,
        category: TicketCategory | str,
        priority: TicketPriority | str,
        subject: str,
        description: str,
        queue_key: str = "HUCE_GENERAL",
    ) -> Ticket:
        now = datetime.now(timezone.utc)
        return cls(
            id=generate_uuid7(),
            requester_user_id=requester_user_id,
            category=TicketCategory(category),
            priority=TicketPriority(priority),
            status=TicketStatus.DRAFT,
            subject=subject.strip(),
            description_redacted=description.strip(),
            queue_key=queue_key,
            created_at=now,
            updated_at=now,
            version=1,
        )

    def _check_terminal(self) -> None:
        if self.status in TERMINAL_STATES:
            raise InvalidTicketStateError(f"Cannot transition from terminal state {self.status}")

    def request_confirmation(self) -> Ticket:
        self._check_terminal()
        if self.status != TicketStatus.DRAFT:
            raise InvalidTicketStateError(f"Cannot request confirmation from state {self.status}")
        now = datetime.now(timezone.utc)
        return replace(
            self,
            status=TicketStatus.CONFIRMATION_REQUIRED,
            updated_at=now,
            version=self.version + 1,
        )

    def confirm_create(self) -> Ticket:
        self._check_terminal()
        if self.status != TicketStatus.CONFIRMATION_REQUIRED:
            raise InvalidTicketStateError(f"Cannot confirm create from state {self.status}")
        now = datetime.now(timezone.utc)
        return replace(
            self,
            status=TicketStatus.OPEN,
            updated_at=now,
            version=self.version + 1,
        )

    def cancel(self) -> Ticket:
        self._check_terminal()
        if self.status not in (TicketStatus.CONFIRMATION_REQUIRED, TicketStatus.OPEN):
            raise InvalidTicketStateError(f"Cannot cancel from state {self.status}")
        now = datetime.now(timezone.utc)
        return replace(
            self,
            status=TicketStatus.CANCELLED,
            updated_at=now,
            version=self.version + 1,
        )
