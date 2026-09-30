from __future__ import annotations

import json
import os
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime, timezone, timedelta
from enum import StrEnum
from typing import Any, Callable, Dict, Optional


class ReviewerRole(StrEnum):
    STUDENT = "student"
    STAFF = "staff"
    ADMIN = "admin"


ROLE_LEVELS: Dict[ReviewerRole, int] = {
    ReviewerRole.STUDENT: 0,
    ReviewerRole.STAFF: 1,
    ReviewerRole.ADMIN: 2,
}


class InterruptStatus(StrEnum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"


class ReviewDecision(StrEnum):
    APPROVED = "approved"
    REJECTED = "rejected"


@dataclass
class InterruptRecord:
    interrupt_id: str
    session_id: str
    turn_id: str
    state_version: int
    reason: str
    min_role: ReviewerRole
    summary: str
    payload: Dict[str, Any]
    status: InterruptStatus
    created_at: str
    expires_at: str
    resolved_by: Optional[str] = None
    resolved_at: Optional[str] = None
    decision: Optional[ReviewDecision] = None


class DurableInterruptManager:
    """Manages durable human interrupts, ensuring survival across restarts,

    enforcing reviewer role hierarchy, and avoiding duplicate actions.
    """

    def __init__(self, storage_dir: str) -> None:
        self.storage_dir = storage_dir
        os.makedirs(storage_dir, exist_ok=True)

    def _file_path(self, interrupt_id: str) -> str:
        return os.path.join(self.storage_dir, f"{interrupt_id}.json")

    def create_interrupt(
        self,
        session_id: str,
        turn_id: str,
        state_version: int,
        reason: str,
        min_role: ReviewerRole,
        summary: str,
        payload: Dict[str, Any],
        expires_in_seconds: int = 3600,
    ) -> InterruptRecord:
        interrupt_id = f"hitl-{uuid.uuid4().hex[:12]}"
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(seconds=expires_in_seconds)

        record = InterruptRecord(
            interrupt_id=interrupt_id,
            session_id=session_id,
            turn_id=turn_id,
            state_version=state_version,
            reason=reason,
            min_role=min_role,
            summary=summary,
            payload=payload,
            status=InterruptStatus.PENDING,
            created_at=now.isoformat(),
            expires_at=expires_at.isoformat(),
        )
        self._save(record)
        return record

    def get_interrupt(self, interrupt_id: str) -> Optional[InterruptRecord]:
        fp = self._file_path(interrupt_id)
        if not os.path.exists(fp):
            return None
        with open(fp, "r", encoding="utf-8") as f:
            data = json.load(f)

        return InterruptRecord(
            interrupt_id=data["interrupt_id"],
            session_id=data["session_id"],
            turn_id=data["turn_id"],
            state_version=data["state_version"],
            reason=data["reason"],
            min_role=ReviewerRole(data["min_role"]),
            summary=data["summary"],
            payload=data["payload"],
            status=InterruptStatus(data["status"]),
            created_at=data["created_at"],
            expires_at=data["expires_at"],
            resolved_by=data.get("resolved_by"),
            resolved_at=data.get("resolved_at"),
            decision=ReviewDecision(data["decision"]) if data.get("decision") else None,
        )

    def _save(self, record: InterruptRecord) -> None:
        fp = self._file_path(record.interrupt_id)
        with open(fp, "w", encoding="utf-8") as f:
            json.dump(asdict(record), f, indent=2)

    def resolve_interrupt(
        self,
        interrupt_id: str,
        decision: ReviewDecision,
        reviewer_id: str,
        reviewer_role: ReviewerRole,
        expected_state_version: int,
    ) -> InterruptRecord:
        record = self.get_interrupt(interrupt_id)
        if record is None:
            raise ValueError(f"Interrupt '{interrupt_id}' not found")

        if record.status != InterruptStatus.PENDING:
            raise RuntimeError(f"Interrupt already resolved with status {record.status}")

        now = datetime.now(timezone.utc)
        expires_at = datetime.fromisoformat(record.expires_at)
        if now > expires_at:
            record.status = InterruptStatus.EXPIRED
            self._save(record)
            raise RuntimeError("Interrupt has expired")

        # Check state version
        if record.state_version != expected_state_version:
            raise ValueError(
                f"State version mismatch: expected {expected_state_version}, currently at {record.state_version}"
            )

        # Check role level
        if ROLE_LEVELS[reviewer_role] < ROLE_LEVELS[record.min_role]:
            raise PermissionError(
                f"Insufficient reviewer role '{reviewer_role}'. Minimum required: '{record.min_role}'"
            )

        record.status = InterruptStatus.APPROVED if decision == ReviewDecision.APPROVED else InterruptStatus.REJECTED
        record.state_version += 1
        record.resolved_by = reviewer_id
        record.resolved_at = now.isoformat()
        record.decision = decision

        self._save(record)
        return record

    def resolve_and_execute(
        self,
        interrupt_id: str,
        decision: ReviewDecision,
        reviewer_id: str,
        reviewer_role: ReviewerRole,
        expected_state_version: int,
        action_handler: Callable[[], Any],
    ) -> InterruptRecord:
        # Atomic step: resolve first
        resolved = self.resolve_interrupt(
            interrupt_id=interrupt_id,
            decision=decision,
            reviewer_id=reviewer_id,
            reviewer_role=reviewer_role,
            expected_state_version=expected_state_version,
        )

        if resolved.status == InterruptStatus.APPROVED:
            action_handler()

        return resolved
