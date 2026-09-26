from __future__ import annotations

from typing import Any
from fastapi import APIRouter, HTTPException, Query, Request
from starlette.responses import JSONResponse

from campus247.domain.handover.model import Handover
from campus247.ports.identity import IdentityRole
from campus247.presentation.identity import get_current_identity


def _serialize_handover(h: Handover) -> dict[str, Any]:
    context_ids = [cid.strip() for cid in h.context_reference_ids.split(",") if cid.strip()] if h.context_reference_ids else []
    data: dict[str, Any] = {
        "handover_id": h.id,
        "conversation_id": h.conversation_id,
        "requester_user_id": h.requester_user_id,
        "queue_key": h.queue_key,
        "reason_code": h.reason_code,
        "risk_level": h.risk_level.value,
        "status": h.status.value,
        "summary_redacted": h.summary_redacted,
        "context_reference_ids": context_ids,
        "citations": [],
        "created_at": h.created_at.isoformat(),
        "version": h.version,
    }
    if h.assigned_user_id:
        data["assigned_user_id"] = h.assigned_user_id
    if h.accepted_at:
        data["accepted_at"] = h.accepted_at.isoformat()
    if h.resolved_at:
        data["resolved_at"] = h.resolved_at.isoformat()
    return data


def create_handover_router(store: dict[str, Handover] | None = None) -> APIRouter:
    router = APIRouter(tags=["Handovers"])
    storage: dict[str, Handover] = store if store is not None else {}

    @router.get("/v1/staff/handovers")
    async def list_staff_handovers(
        request: Request,
        cursor: str | None = Query(None),
        limit: int = Query(20, ge=1, le=100),
        queue_key: str | None = Query(None),
        risk_level: list[str] | None = Query(None),
    ) -> JSONResponse:
        identity = get_current_identity(request)
        if not (identity.has_role(IdentityRole.SUPPORT_OFFICER) or identity.has_role(IdentityRole.SYSTEM_ADMIN)):
            raise HTTPException(status_code=403, detail="Forbidden: Staff handover access requires SUPPORT_OFFICER role")

        if not identity.unit_ids:
            raise HTTPException(status_code=403, detail="Forbidden: Officer has no authorized queues configured")

        if queue_key is not None and queue_key not in identity.unit_ids:
            raise HTTPException(status_code=403, detail="Forbidden: Requested queue is outside officer's authorized scope")

        authorized_queues = {queue_key} if queue_key else set(identity.unit_ids)
        cases = [h for h in storage.values() if h.queue_key in authorized_queues]

        if risk_level:
            cases = [h for h in cases if h.risk_level.value in risk_level]

        cases.sort(key=lambda h: (h.created_at, h.id))

        offset = 0
        if cursor:
            try:
                offset = int(cursor)
            except ValueError:
                offset = 0

        paged = cases[offset : offset + limit]
        has_more = (offset + limit) < len(cases)
        next_cursor = str(offset + limit) if has_more else None

        content = {
            "items": [_serialize_handover(h) for h in paged],
            "page": {
                "next_cursor": next_cursor,
                "has_more": has_more,
                "limit": limit,
            },
        }
        return JSONResponse(status_code=200, content=content, headers={"Cache-Control": "no-store"})

    @router.get("/v1/handovers/{handover_id}")
    async def get_handover(handover_id: str, request: Request) -> JSONResponse:
        identity = get_current_identity(request)
        handover = storage.get(handover_id)
        if not handover:
            raise HTTPException(status_code=404, detail="Handover not found")

        is_owner = handover.requester_user_id == identity.subject_id
        is_authorized_staff = (
            (identity.has_role(IdentityRole.SUPPORT_OFFICER) or identity.has_role(IdentityRole.SYSTEM_ADMIN))
            and handover.queue_key in identity.unit_ids
        )

        if not (is_owner or is_authorized_staff):
            raise HTTPException(status_code=404, detail="Handover not found")

        return JSONResponse(
            status_code=200,
            content=_serialize_handover(handover),
            headers={
                "ETag": f'"{handover.version}"',
                "Cache-Control": "no-store",
            },
        )

    return router
