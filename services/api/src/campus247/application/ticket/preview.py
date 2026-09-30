from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from campus247.domain.action.confirmation import ConfirmationTokenService
from campus247.domain.action.preview import create_action_preview
from campus247.domain.shared.values import generate_uuid7
from campus247.domain.ticket.model import Ticket, TicketCategory, TicketPriority
from campus247.ports.identity import IdentityContext
from campus247.ports.policy import (
    AuthorizationPolicyPort,
    PolicyEvaluationRequest,
    PolicyResourceContext,
)


@dataclass(frozen=True)
class CreateTicketPayload:
    category: str
    priority: str
    subject: str
    description: str
    queue_key: str = "HUCE_GENERAL"


@dataclass(frozen=True)
class TicketPreviewResult:
    preview_id: str
    confirmation_token: str
    expires_at: datetime
    preview_summary: str
    policy_decision: str
    action_type: str = "CREATE_TICKET"


class TicketPreviewService:
    def __init__(
        self,
        confirmation_service: ConfirmationTokenService,
        policy_engine: AuthorizationPolicyPort | None = None,
    ) -> None:
        self._confirmation_service = confirmation_service
        self._policy_engine = policy_engine

    async def preview_create_ticket(
        self,
        actor: IdentityContext,
        payload: CreateTicketPayload,
    ) -> TicketPreviewResult:
        if self._policy_engine is not None:
            eval_req = PolicyEvaluationRequest(
                actor=actor,
                action="ticket.create",
                resource_type="ticket",
                correlation_id=generate_uuid7(),
                resource=PolicyResourceContext(owner_subject_id=actor.subject_id),
            )
            decision = self._policy_engine.evaluate(eval_req)
            if not decision.is_allowed:
                raise PermissionError(f"Action not permitted by policy: {decision.reason_code}")

        # Validate domain entity rules
        ticket_draft = Ticket.create_draft(
            requester_user_id=actor.subject_id,
            category=payload.category,
            priority=payload.priority,
            subject=payload.subject,
            description=payload.description,
            queue_key=payload.queue_key,
        )

        normalized_payload = {
            "requester_user_id": actor.subject_id,
            "category": ticket_draft.category.value,
            "priority": ticket_draft.priority.value,
            "subject": ticket_draft.subject,
            "description": ticket_draft.description_redacted,
            "queue_key": ticket_draft.queue_key,
        }

        preview = create_action_preview(
            actor_user_id=actor.subject_id,
            session_id=actor.session_id if hasattr(actor, "session_id") and actor.session_id else "none",
            action_type="CREATE_TICKET",
            payload=normalized_payload,
            ttl_seconds=300,
            policy_decision="ALLOW_WITH_CONFIRMATION",
        )

        token = self._confirmation_service.mint_token(preview)

        return TicketPreviewResult(
            preview_id=preview.id,
            confirmation_token=token,
            expires_at=preview.expires_at,
            preview_summary=f"Yêu cầu hỗ trợ: {ticket_draft.subject} ({ticket_draft.category.value})",
            policy_decision="ALLOW_WITH_CONFIRMATION",
            action_type="CREATE_TICKET",
        )
