from __future__ import annotations

from typing import Sequence
from fastapi import APIRouter, HTTPException, Query, Request
from starlette.responses import JSONResponse

from campus247.domain.ticket.model import Ticket
from campus247.presentation.identity import get_current_identity


def create_ticket_query_router(
    store: dict[str, Ticket] | None = None,
) -> APIRouter:
    router = APIRouter(tags=["Tickets"])
    storage: dict[str, Ticket] = store if store is not None else {}

    @router.get("/v1/tickets")
    async def list_my_tickets(
        request: Request,
        cursor: str | None = Query(None),
        limit: int = Query(20, ge=1, le=100),
        status: list[str] | None = Query(None),
    ) -> JSONResponse:
        identity = get_current_identity(request)

        user_tickets = [
            t for t in storage.values() if t.requester_user_id == identity.subject_id
        ]
        if status:
            user_tickets = [t for t in user_tickets if t.status.value in status]

        user_tickets.sort(key=lambda t: (t.created_at, t.id))

        offset = 0
        if cursor:
            try:
                offset = int(cursor)
            except ValueError:
                offset = 0

        paged = user_tickets[offset : offset + limit]
        has_more = (offset + limit) < len(user_tickets)
        next_cursor = str(offset + limit) if has_more else None

        items = [
            {
                "id": t.id,
                "requester_user_id": t.requester_user_id,
                "category": t.category.value,
                "priority": t.priority.value,
                "status": t.status.value,
                "subject": t.subject,
                "description_redacted": t.description_redacted,
                "queue_key": t.queue_key,
                "assigned_user_id": t.assigned_user_id,
                "created_at": t.created_at.isoformat(),
                "updated_at": t.updated_at.isoformat(),
                "version": t.version,
            }
            for t in paged
        ]

        content = {
            "items": items,
            "page": {
                "next_cursor": next_cursor,
                "has_more": has_more,
                "limit": limit,
            },
        }
        return JSONResponse(status_code=200, content=content, headers={"Cache-Control": "no-store"})

    @router.get("/v1/tickets/{ticket_id}")
    async def get_ticket(
        ticket_id: str,
        request: Request,
    ) -> JSONResponse:
        identity = get_current_identity(request)

        ticket = storage.get(ticket_id)
        if not ticket:
            raise HTTPException(status_code=404, detail="Ticket not found")

        if ticket.requester_user_id != identity.subject_id:
            raise HTTPException(status_code=403, detail="Forbidden: access to another user's ticket denied")

        content = {
            "id": ticket.id,
            "requester_user_id": ticket.requester_user_id,
            "category": ticket.category.value,
            "priority": ticket.priority.value,
            "status": ticket.status.value,
            "subject": ticket.subject,
            "description_redacted": ticket.description_redacted,
            "queue_key": ticket.queue_key,
            "assigned_user_id": ticket.assigned_user_id,
            "created_at": ticket.created_at.isoformat(),
            "updated_at": ticket.updated_at.isoformat(),
            "version": ticket.version,
        }
        return JSONResponse(
            status_code=200,
            content=content,
            headers={
                "ETag": f'"{ticket.version}"',
                "Cache-Control": "no-store",
            },
        )

    return router
