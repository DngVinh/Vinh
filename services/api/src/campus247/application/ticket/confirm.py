from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
from typing import Any

from campus247.application.action.idempotency import IdempotencyLedger, ReservationStatus
from campus247.application.audit.writer import AuditWriter
from campus247.application.ticket.preview import CreateTicketPayload
from campus247.domain.action.confirmation import ConfirmationTokenService
from campus247.domain.shared.values import generate_uuid7
from campus247.domain.ticket.model import Ticket, TicketCategory, TicketPriority, TicketStatus
from campus247.ports.identity import IdentityContext


@dataclass(frozen=True)
class TicketConfirmationResult:
    ticket: Ticket
    is_replay: bool = False


class TicketConfirmationService:
    def __init__(
        self,
        confirmation_service: ConfirmationTokenService,
        idempotency_ledger: IdempotencyLedger,
        audit_writer: AuditWriter,
    ) -> None:
        self._confirmation_service = confirmation_service
        self._idempotency_ledger = idempotency_ledger
        self._audit_writer = audit_writer
        self._tickets: dict[str, Ticket] = {}

    async def confirm_ticket(
        self,
        actor: IdentityContext,
        preview_id: str,
        confirmation_token: str,
        idempotency_key: str,
        payload: CreateTicketPayload,
    ) -> TicketConfirmationResult:
        normalized_dict = {
            "requester_user_id": actor.subject_id,
            "category": TicketCategory(payload.category).value,
            "priority": TicketPriority(payload.priority).value,
            "subject": payload.subject.strip(),
            "description": payload.description.strip(),
            "queue_key": payload.queue_key,
        }
        normalized_str = json.dumps(normalized_dict, sort_keys=True, separators=(",", ":"))
        payload_hash = hashlib.sha256(normalized_str.encode("utf-8")).hexdigest()

        # 1. Validate confirmation token
        val_result = self._confirmation_service.validate_token(
            token=confirmation_token,
            expected_preview_id=preview_id,
            expected_actor_id=actor.subject_id,
            expected_payload_hash=payload_hash,
        )
        if not val_result.is_valid:
            raise ValueError(f"Invalid confirmation token: {val_result.error_code}")

        # 2. Idempotency reservation
        reservation = self._idempotency_ledger.reserve(
            actor_user_id=actor.subject_id,
            operation_id="ticket.create",
            idempotency_key=idempotency_key,
            request_fingerprint=payload_hash,
        )

        if reservation.status == ReservationStatus.REPLAY:
            ticket_id = reservation.record.response_reference if reservation.record else None
            existing_ticket = self._tickets.get(ticket_id) if ticket_id else None
            if existing_ticket:
                return TicketConfirmationResult(ticket=existing_ticket, is_replay=True)

        if reservation.status in (ReservationStatus.CONFLICT_REUSED, ReservationStatus.CONFLICT_IN_PROGRESS):
            raise ValueError("Idempotency conflict: concurrent or reused key with mismatching fingerprint")

        # 3. Create Ticket
        now = datetime.now(timezone.utc)
        ticket = Ticket(
            id=generate_uuid7(),
            requester_user_id=actor.subject_id,
            category=TicketCategory(payload.category),
            priority=TicketPriority(payload.priority),
            status=TicketStatus.OPEN,
            subject=payload.subject.strip(),
            description_redacted=payload.description.strip(),
            queue_key=payload.queue_key,
            created_at=now,
            updated_at=now,
            version=1,
        )
        self._tickets[ticket.id] = ticket

        # 4. Audit Log
        self._audit_writer.record_event(
            actor_type="STUDENT",
            actor_id=actor.subject_id,
            action_code="ticket.confirm_create",
            resource_type="ticket",
            resource_id=ticket.id,
            outcome="SUCCESS",
        )

        # 5. Complete idempotency ledger
        self._idempotency_ledger.complete(
            actor_user_id=actor.subject_id,
            operation_id="ticket.create",
            idempotency_key=idempotency_key,
            http_status=201,
            response_payload=ticket.id,
        )

        return TicketConfirmationResult(ticket=ticket, is_replay=False)
