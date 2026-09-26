from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from campus247.application.audit.writer import AuditWriter
from campus247.domain.handover.model import Handover
from campus247.domain.ticket.model import Ticket
from campus247.ports.identity import IdentityContext, IdentityRole


class CaseClaimConflictError(Exception):
    def __init__(self, case_id: str, current_owner_id: str, message: str | None = None) -> None:
        self.case_id = case_id
        self.current_owner_id = current_owner_id
        super().__init__(message or f"Case {case_id} is already claimed by {current_owner_id}")


@dataclass
class CaseClaimRecord:
    case_id: str
    queue_key: str
    assigned_user_id: str | None = None
    status: str = "QUEUED"
    version: int = 1


@dataclass(frozen=True)
class CaseClaimResult:
    case_id: str
    assignee_id: str
    status: str
    conflict_owner_id: str | None = None
    version: int = 1

    @property
    def is_conflict(self) -> bool:
        return self.status == "CONFLICT"


class StaffCaseClaimService:
    def __init__(self, audit_writer: AuditWriter | None = None) -> None:
        self._audit_writer = audit_writer or AuditWriter()
        self._cases: dict[str, Any] = {}
        self._locks: dict[str, asyncio.Lock] = {}
        self._global_lock = asyncio.Lock()

    def register_case(self, case: Any) -> None:
        case_id = getattr(case, "id", getattr(case, "case_id", None))
        if not case_id:
            raise ValueError("Case must have an 'id' or 'case_id'")
        self._cases[case_id] = case

    async def _get_lock(self, case_id: str) -> asyncio.Lock:
        async with self._global_lock:
            if case_id not in self._locks:
                self._locks[case_id] = asyncio.Lock()
            return self._locks[case_id]

    async def claim_case(self, actor: IdentityContext, case_id: str) -> CaseClaimResult:
        if not (actor.has_role(IdentityRole.SUPPORT_OFFICER) or actor.has_role(IdentityRole.SYSTEM_ADMIN)):
            raise PermissionError("Actor requires SUPPORT_OFFICER role to claim cases")

        if case_id not in self._cases:
            raise KeyError(f"Case {case_id} not found")

        lock = await self._get_lock(case_id)
        async with lock:
            case = self._cases[case_id]
            queue_key = getattr(case, "queue_key", None)
            if not queue_key or queue_key not in actor.unit_ids:
                raise PermissionError(f"Case {case_id} queue '{queue_key}' is outside officer's authorized queues")

            current_assignee = getattr(case, "assigned_user_id", None)
            if current_assignee is not None and current_assignee != actor.subject_id:
                self._audit_writer.record_event(
                    actor_type="SUPPORT_OFFICER",
                    actor_id=actor.subject_id,
                    action_code="case.claim_conflict",
                    resource_type="case",
                    resource_id=case_id,
                    outcome="CONFLICT",
                )
                return CaseClaimResult(
                    case_id=case_id,
                    assignee_id=actor.subject_id,
                    status="CONFLICT",
                    conflict_owner_id=current_assignee,
                    version=getattr(case, "version", 1),
                )

            # Atomically update assignment
            if isinstance(case, Handover):
                updated_case = case.assign(actor.subject_id)
                self._cases[case_id] = updated_case
                new_version = updated_case.version
            elif isinstance(case, CaseClaimRecord):
                case.assigned_user_id = actor.subject_id
                case.status = "ASSIGNED"
                case.version += 1
                new_version = case.version
            else:
                setattr(case, "assigned_user_id", actor.subject_id)
                new_version = getattr(case, "version", 1) + 1
                setattr(case, "version", new_version)

            self._audit_writer.record_event(
                actor_type="SUPPORT_OFFICER",
                actor_id=actor.subject_id,
                action_code="case.claim",
                resource_type="case",
                resource_id=case_id,
                outcome="SUCCESS",
            )

            return CaseClaimResult(
                case_id=case_id,
                assignee_id=actor.subject_id,
                status="CLAIMED",
                version=new_version,
            )
