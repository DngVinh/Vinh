from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime, timezone
from typing import Any

from campus247.application.audit.writer import AuditWriter
from campus247.domain.handover.model import Handover, HandoverStatus, TERMINAL_STATES
from campus247.domain.shared.values import generate_uuid7
from campus247.ports.identity import IdentityContext, IdentityRole

VALID_QUEUES = {
    "STUDENT_SUPPORT_GENERAL",
    "ACADEMIC_POLICY",
    "DOCUMENT_SERVICES",
    "FACILITIES_ROOM",
    "SAFETY_RESTRICTED",
    "PRIVACY_SECURITY",
    "KNOWLEDGE_QUALITY",
    "OPERATIONS_FALLBACK",
}


@dataclass(frozen=True)
class TransferHistoryEntry:
    id: str
    case_id: str
    from_queue: str
    to_queue: str
    transferred_by_user_id: str
    previous_assignee_user_id: str | None
    reason: str
    transferred_at: datetime


@dataclass(frozen=True)
class StaffCaseTransferCommand:
    case_id: str
    target_queue: str
    reason: str


@dataclass(frozen=True)
class StaffCaseTransferResult:
    case_id: str
    case: Any
    history_entry: TransferHistoryEntry


class StaffCaseTransferService:
    def __init__(self, audit_writer: AuditWriter | None = None) -> None:
        self._audit_writer = audit_writer or AuditWriter()
        self._cases: dict[str, Any] = {}
        self._histories: dict[str, list[TransferHistoryEntry]] = {}

    def register_case(self, case: Any) -> None:
        case_id = getattr(case, "id", getattr(case, "case_id", None))
        if not case_id:
            raise ValueError("Case must have an 'id' or 'case_id'")
        self._cases[case_id] = case

    def get_case(self, case_id: str) -> Any:
        return self._cases.get(case_id)

    def get_case_history(self, case_id: str) -> list[TransferHistoryEntry]:
        return list(self._histories.get(case_id, []))

    def transfer_case(
        self,
        actor: IdentityContext,
        cmd: StaffCaseTransferCommand,
    ) -> StaffCaseTransferResult:
        if not (actor.has_role(IdentityRole.SUPPORT_OFFICER) or actor.has_role(IdentityRole.SYSTEM_ADMIN)):
            raise PermissionError("Actor requires SUPPORT_OFFICER role to transfer cases")

        if cmd.case_id not in self._cases:
            raise KeyError(f"Case {cmd.case_id} not found")

        clean_target_queue = cmd.target_queue.strip().upper()
        if clean_target_queue not in VALID_QUEUES:
            raise ValueError(f"Invalid destination queue: {cmd.target_queue}")

        clean_reason = cmd.reason.strip()
        if not clean_reason:
            raise ValueError("Transfer reason cannot be empty")

        case = self._cases[cmd.case_id]
        current_queue = getattr(case, "queue_key", "")
        if current_queue == clean_target_queue:
            raise ValueError("Target queue cannot be the same as current queue")

        if not current_queue or current_queue not in actor.unit_ids:
            raise PermissionError(f"Case {cmd.case_id} current queue '{current_queue}' is outside officer's authorized queues")

        # State machine check
        status_val = getattr(case, "status", None)
        if status_val in TERMINAL_STATES or str(status_val) in ("RESOLVED", "CLOSED", "CANCELLED"):
            raise ValueError(f"Cannot transfer case in terminal status: {status_val}")

        previous_assignee = getattr(case, "assigned_user_id", None)
        now = datetime.now(timezone.utc)

        history_entry = TransferHistoryEntry(
            id=generate_uuid7(),
            case_id=cmd.case_id,
            from_queue=current_queue,
            to_queue=clean_target_queue,
            transferred_by_user_id=actor.subject_id,
            previous_assignee_user_id=previous_assignee,
            reason=clean_reason,
            transferred_at=now,
        )

        # Apply transfer mutation while preserving SLA (created_at) and incrementing version
        if isinstance(case, Handover):
            updated_case = replace(
                case,
                queue_key=clean_target_queue,
                status=HandoverStatus.QUEUED,
                assigned_user_id=None,
                accepted_at=None,
                updated_at=now,
                version=case.version + 1,
            )
        else:
            new_version = getattr(case, "version", 1) + 1
            updated_case = replace(
                case,
                queue_key=clean_target_queue,
                status="QUEUED",
                assigned_user_id=None,
                updated_at=now,
                version=new_version,
            )

        self._cases[cmd.case_id] = updated_case
        if cmd.case_id not in self._histories:
            self._histories[cmd.case_id] = []
        self._histories[cmd.case_id].append(history_entry)

        self._audit_writer.record_event(
            actor_type="SUPPORT_OFFICER",
            actor_id=actor.subject_id,
            action_code="case.transfer",
            resource_type="case",
            resource_id=cmd.case_id,
            outcome="SUCCESS",
            metadata={
                "from_queue": current_queue,
                "to_queue": clean_target_queue,
                "reason": clean_reason,
                "previous_assignee": previous_assignee,
            },
        )

        return StaffCaseTransferResult(case_id=cmd.case_id, case=updated_case, history_entry=history_entry)
