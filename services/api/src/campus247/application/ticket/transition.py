from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime, timezone
from typing import Any

from campus247.application.audit.writer import AuditWriter
from campus247.domain.shared.values import generate_uuid7
from campus247.domain.ticket.model import Ticket, TicketStatus
from campus247.ports.identity import IdentityContext
from campus247.ports.policy import (
    AuthorizationPolicyPort,
    PolicyEvaluationRequest,
    PolicyResourceContext,
)

ALLOWED_TRANSITIONS: dict[TicketStatus, set[TicketStatus]] = {
    TicketStatus.OPEN: {TicketStatus.ASSIGNED, TicketStatus.ESCALATED, TicketStatus.CANCELLED},
    TicketStatus.ASSIGNED: {TicketStatus.IN_PROGRESS, TicketStatus.ASSIGNED, TicketStatus.ESCALATED},
    TicketStatus.IN_PROGRESS: {TicketStatus.WAITING_STUDENT, TicketStatus.RESOLVED},
    TicketStatus.WAITING_STUDENT: {TicketStatus.IN_PROGRESS},
    TicketStatus.RESOLVED: {TicketStatus.IN_PROGRESS, TicketStatus.CLOSED},
    TicketStatus.ESCALATED: {TicketStatus.ASSIGNED},
}


@dataclass(frozen=True)
class TicketTransitionCommand:
    ticket_id: str
    target_status: str
    actor: IdentityContext
    assigned_user_id: str | None = None
    resolution_code: str | None = None
    resolution_summary: str | None = None
    comment: str | None = None


class StaffTicketTransitionService:
    def __init__(
        self,
        tickets: dict[str, Ticket],
        policy_engine: AuthorizationPolicyPort | None = None,
        audit_writer: AuditWriter | None = None,
    ) -> None:
        self._tickets = tickets
        self._policy_engine = policy_engine
        self._audit_writer = audit_writer

    async def transition_ticket(self, cmd: TicketTransitionCommand) -> Ticket:
        ticket = self._tickets.get(cmd.ticket_id)
        if not ticket:
            raise KeyError(f"Ticket not found: {cmd.ticket_id}")

        target_status = TicketStatus(cmd.target_status)
        action_name = "ticket.close" if target_status == TicketStatus.CLOSED else "ticket.update"

        if self._policy_engine is not None:
            eval_req = PolicyEvaluationRequest(
                actor=cmd.actor,
                action=action_name,
                resource_type="ticket",
                correlation_id=generate_uuid7(),
                resource=PolicyResourceContext(
                    owner_subject_id=ticket.requester_user_id,
                    assigned_unit_id=ticket.queue_key,
                ),
            )
            decision = self._policy_engine.evaluate(eval_req)
            if not decision.is_allowed:
                raise PermissionError(f"Action not permitted: {decision.reason_code}")

        allowed = ALLOWED_TRANSITIONS.get(ticket.status, set())
        if target_status not in allowed:
            raise ValueError(f"Invalid transition from {ticket.status} to {target_status}")

        now = datetime.now(timezone.utc)
        updates: dict[str, Any] = {
            "status": target_status,
            "updated_at": now,
            "version": ticket.version + 1,
        }

        if target_status == TicketStatus.ASSIGNED and cmd.assigned_user_id:
            updates["assigned_user_id"] = cmd.assigned_user_id
        elif target_status == TicketStatus.RESOLVED:
            updates["resolved_at"] = now
        elif target_status == TicketStatus.CLOSED:
            updates["closed_at"] = now

        updated_ticket = replace(ticket, **updates)
        self._tickets[ticket.id] = updated_ticket

        if self._audit_writer is not None:
            self._audit_writer.record_event(
                actor_type="STAFF",
                actor_id=cmd.actor.subject_id,
                action_code=f"ticket.transition_{target_status.value.lower()}",
                resource_type="ticket",
                resource_id=ticket.id,
                outcome="SUCCESS",
            )

        return updated_ticket
