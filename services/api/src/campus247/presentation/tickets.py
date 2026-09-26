from __future__ import annotations

from typing import Any
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field
from starlette.responses import JSONResponse

from campus247.application.ticket.confirm import TicketConfirmationService
from campus247.application.ticket.preview import (
    CreateTicketPayload,
    TicketPreviewService,
)
from campus247.presentation.identity import get_current_identity


class TicketRequestBody(BaseModel):
    category: str
    priority: str
    subject: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., min_length=1)
    queue_key: str = "HUCE_GENERAL"


class ConfirmRequestBody(BaseModel):
    confirmation_token: str
    idempotency_key: str
    payload: TicketRequestBody


def create_ticket_router(
    preview_svc: TicketPreviewService,
    confirm_svc: TicketConfirmationService,
) -> APIRouter:
    router = APIRouter(tags=["Tickets"])

    @router.post("/v1/tickets/preview")
    async def preview_ticket(
        body: TicketRequestBody,
        request: Request,
    ) -> JSONResponse:
        identity = get_current_identity(request)

        try:
            domain_payload = CreateTicketPayload(
                category=body.category,
                priority=body.priority,
                subject=body.subject,
                description=body.description,
                queue_key=body.queue_key,
            )
            res = await preview_svc.preview_create_ticket(identity, domain_payload)
        except PermissionError as e:
            raise HTTPException(status_code=403, detail=str(e))
        except ValueError as e:
            raise HTTPException(status_code=422, detail=str(e))

        content = {
            "preview_id": res.preview_id,
            "confirmation_token": res.confirmation_token,
            "expires_at": res.expires_at.isoformat(),
            "preview_summary": res.preview_summary,
            "action_type": res.action_type,
            "policy_decision": res.policy_decision,
        }
        return JSONResponse(
            status_code=201,
            content=content,
            headers={"Cache-Control": "no-store"},
        )

    @router.post("/v1/tickets/{preview_id}/confirm")
    async def confirm_ticket(
        preview_id: str,
        body: ConfirmRequestBody,
        request: Request,
    ) -> JSONResponse:
        identity = get_current_identity(request)

        try:
            domain_payload = CreateTicketPayload(
                category=body.payload.category,
                priority=body.payload.priority,
                subject=body.payload.subject,
                description=body.payload.description,
                queue_key=body.payload.queue_key,
            )
            res = await confirm_svc.confirm_ticket(
                actor=identity,
                preview_id=preview_id,
                confirmation_token=body.confirmation_token,
                idempotency_key=body.idempotency_key,
                payload=domain_payload,
            )
        except ValueError as e:
            raise HTTPException(status_code=422, detail=str(e))

        content = {
            "ticket_id": res.ticket.id,
            "status": res.ticket.status.value,
            "is_replay": res.is_replay,
        }
        return JSONResponse(
            status_code=201,
            content=content,
            headers={
                "Location": f"/v1/tickets/{res.ticket.id}",
                "Cache-Control": "no-store",
            },
        )

    return router
