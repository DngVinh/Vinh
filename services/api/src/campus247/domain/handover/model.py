from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime, timezone
from enum import StrEnum

from campus247.domain.shared.values import generate_uuid7, is_valid_uuid7


class HandoverRiskLevel(StrEnum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class HandoverStatus(StrEnum):
    QUEUED = "QUEUED"
    ASSIGNED = "ASSIGNED"
    ACCEPTED = "ACCEPTED"
    IN_PROGRESS = "IN_PROGRESS"
    RESOLVED = "RESOLVED"
    RETURNED = "RETURNED"
    CANCELLED = "CANCELLED"


TERMINAL_STATES = {HandoverStatus.RESOLVED, HandoverStatus.CANCELLED}


class InvalidHandoverValidationError(ValueError):
    pass


class InvalidHandoverStateError(Exception):
    pass


@dataclass(frozen=True)
class Handover:
    id: str
    conversation_id: str
    requester_user_id: str
    queue_key: str
    reason_code: str
    risk_level: HandoverRiskLevel
    status: HandoverStatus
    summary_redacted: str
    created_at: datetime
    updated_at: datetime
    context_reference_ids: str | None = None
    assigned_user_id: str | None = None
    accepted_at: datetime | None = None
    resolved_at: datetime | None = None
    version: int = 1

    def __post_init__(self) -> None:
        if not is_valid_uuid7(self.conversation_id):
            raise InvalidHandoverValidationError(
                f"conversation_id must be a valid UUIDv7 string, got: {self.conversation_id}"
            )
        if not is_valid_uuid7(self.requester_user_id):
            raise InvalidHandoverValidationError(
                f"requester_user_id must be a valid UUIDv7 string, got: {self.requester_user_id}"
            )
        if not self.queue_key or not self.queue_key.strip():
            raise InvalidHandoverValidationError("queue_key cannot be empty")
        if not self.reason_code or not self.reason_code.strip():
            raise InvalidHandoverValidationError("reason_code cannot be empty")
        if not self.summary_redacted or not self.summary_redacted.strip():
            raise InvalidHandoverValidationError("summary_redacted cannot be empty")

    @classmethod
    def create_queued(
        cls,
        conversation_id: str,
        requester_user_id: str,
        queue_key: str,
        reason_code: str,
        risk_level: HandoverRiskLevel | str,
        summary: str,
        context_reference_ids: str | None = None,
    ) -> Handover:
        now = datetime.now(timezone.utc)
        return cls(
            id=generate_uuid7(),
            conversation_id=conversation_id,
            requester_user_id=requester_user_id,
            queue_key=queue_key.strip(),
            reason_code=reason_code.strip(),
            risk_level=HandoverRiskLevel(risk_level),
            status=HandoverStatus.QUEUED,
            summary_redacted=summary.strip(),
            created_at=now,
            updated_at=now,
            context_reference_ids=context_reference_ids,
            version=1,
        )

    def _transition(self, new_status: HandoverStatus, **kwargs) -> Handover:
        if self.status in TERMINAL_STATES:
            raise InvalidHandoverStateError(f"Cannot transition from terminal state {self.status}")
        now = datetime.now(timezone.utc)
        return replace(self, status=new_status, updated_at=now, version=self.version + 1, **kwargs)

    def assign(self, assigned_user_id: str) -> Handover:
        if self.status not in (HandoverStatus.QUEUED, HandoverStatus.ASSIGNED):
            raise InvalidHandoverStateError(f"Cannot assign from state {self.status}")
        if not is_valid_uuid7(assigned_user_id):
            raise InvalidHandoverValidationError(f"assigned_user_id must be valid UUIDv7, got {assigned_user_id}")
        return self._transition(HandoverStatus.ASSIGNED, assigned_user_id=assigned_user_id)

    def accept(self) -> Handover:
        if self.status != HandoverStatus.ASSIGNED:
            raise InvalidHandoverStateError(f"Cannot accept from state {self.status}")
        now = datetime.now(timezone.utc)
        return self._transition(HandoverStatus.ACCEPTED, accepted_at=now)

    def start_work(self) -> Handover:
        if self.status not in (HandoverStatus.ASSIGNED, HandoverStatus.ACCEPTED):
            raise InvalidHandoverStateError(f"Cannot start work from state {self.status}")
        return self._transition(HandoverStatus.IN_PROGRESS)

    def resolve(self) -> Handover:
        if self.status != HandoverStatus.IN_PROGRESS:
            raise InvalidHandoverStateError(f"Cannot resolve from state {self.status}")
        now = datetime.now(timezone.utc)
        return self._transition(HandoverStatus.RESOLVED, resolved_at=now)

    def return_to_queue(self, reason: str) -> Handover:
        if self.status not in (HandoverStatus.ASSIGNED, HandoverStatus.ACCEPTED, HandoverStatus.IN_PROGRESS):
            raise InvalidHandoverStateError(f"Cannot return from state {self.status}")
        return self._transition(HandoverStatus.RETURNED)

    def cancel(self) -> Handover:
        if self.risk_level == HandoverRiskLevel.CRITICAL:
            raise InvalidHandoverStateError("Critical handover cannot be cancelled")
        if self.status != HandoverStatus.QUEUED:
            raise InvalidHandoverStateError(f"Cannot cancel from state {self.status}")
        return self._transition(HandoverStatus.CANCELLED)
