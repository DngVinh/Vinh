from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from campus247.application.audit.writer import AuditWriter
from campus247.domain.shared.values import generate_uuid7
from campus247.ports.identity import IdentityContext, IdentityRole


class AuditUnavailableError(RuntimeError):
    pass


@dataclass(frozen=True)
class TimelineEvent:
    id: str
    case_id: str
    actor_id: str
    actor_role: str
    event_type: str
    content_redacted: str
    created_at: datetime
    sequence_no: int


@dataclass(frozen=True)
class StaffResponseCommand:
    case_id: str
    content: str
    is_internal_note: bool = False


@dataclass(frozen=True)
class StaffResponseResult:
    case_id: str
    event: TimelineEvent
    is_internal_note: bool = False


class StaffResponseService:
    def __init__(self, audit_writer: AuditWriter | None = None) -> None:
        self._audit_writer = audit_writer or AuditWriter()
        self._cases: dict[str, Any] = {}
        self._timelines: dict[str, list[TimelineEvent]] = {}

    def register_case(self, case: Any) -> None:
        case_id = getattr(case, "id", getattr(case, "case_id", None))
        if not case_id:
            raise ValueError("Case must have an 'id' or 'case_id'")
        self._cases[case_id] = case

    def get_case_timeline(self, case_id: str) -> list[TimelineEvent]:
        return list(self._timelines.get(case_id, []))

    async def respond_to_case(
        self,
        actor: IdentityContext,
        cmd: StaffResponseCommand,
    ) -> StaffResponseResult:
        if not (actor.has_role(IdentityRole.SUPPORT_OFFICER) or actor.has_role(IdentityRole.SYSTEM_ADMIN)):
            raise PermissionError("Actor requires SUPPORT_OFFICER role to respond to cases")

        if cmd.case_id not in self._cases:
            raise KeyError(f"Case {cmd.case_id} not found")

        clean_content = cmd.content.strip()
        if not clean_content:
            raise ValueError("Response content cannot be empty")

        case = self._cases[cmd.case_id]
        queue_key = getattr(case, "queue_key", None)
        if not queue_key or queue_key not in actor.unit_ids:
            raise PermissionError(f"Case {cmd.case_id} queue '{queue_key}' is outside officer's authorized queues")

        assigned_user_id = getattr(case, "assigned_user_id", None)
        if assigned_user_id != actor.subject_id:
            raise PermissionError(f"Case {cmd.case_id} is not assigned to this officer")

        event_type = "INTERNAL_NOTE" if cmd.is_internal_note else "STAFF_RESPONSE"
        existing_timeline = self._timelines.get(cmd.case_id, [])
        seq = len(existing_timeline) + 1
        now = datetime.now(timezone.utc)

        event = TimelineEvent(
            id=generate_uuid7(),
            case_id=cmd.case_id,
            actor_id=actor.subject_id,
            actor_role=actor.roles[0].value if actor.roles else "SUPPORT_OFFICER",
            event_type=event_type,
            content_redacted=clean_content,
            created_at=now,
            sequence_no=seq,
        )

        # Mandatory audit check before commit (fail closed)
        try:
            self._audit_writer.record_event(
                actor_type="SUPPORT_OFFICER",
                actor_id=actor.subject_id,
                action_code="case.respond" if not cmd.is_internal_note else "case.internal_note",
                resource_type="case",
                resource_id=cmd.case_id,
                outcome="SUCCESS",
                metadata={"event_id": event.id, "sequence_no": seq},
            )
        except Exception as e:
            raise AuditUnavailableError(f"Audit recording unavailable; mutation failed closed: {e}") from e

        # Commit timeline only after successful audit
        if cmd.case_id not in self._timelines:
            self._timelines[cmd.case_id] = []
        self._timelines[cmd.case_id].append(event)

        return StaffResponseResult(case_id=cmd.case_id, event=event, is_internal_note=cmd.is_internal_note)
