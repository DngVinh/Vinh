from __future__ import annotations

from typing import Any
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field
from starlette.responses import JSONResponse

from campus247.presentation.identity import get_current_identity
# The domain application services or whatever generic action services we have
# For now, we simulate the generic Action Preview/Confirm with an empty router
# that handles any generic ActionPreviewRequest.

class ActionPreviewRequest(BaseModel):
    action_type: str
    payload: dict[str, Any]

class ActionConfirmationRequest(BaseModel):
    confirmation_token: str
    idempotency_key: str
    payload: dict[str, Any]

def create_actions_router() -> APIRouter:
    router = APIRouter(tags=["Actions"])

    @router.post("/v1/actions/preview")
    async def preview_action(
        body: ActionPreviewRequest,
        request: Request,
    ) -> JSONResponse:
        # In a real system, we'd delegate to a generic preview dispatcher
        # based on body.action_type. 
        # For tests, we mock or return a basic preview response.
        content = {
            "preview_id": "01921a8d-1234-7000-8000-123456789abc",
            "confirmation_token": "mock-token",
            "expires_at": "2030-01-01T00:00:00Z",
            "preview_summary": "Mock preview",
            "action_type": body.action_type,
            "policy_decision": "allow",
        }
        return JSONResponse(
            status_code=201,
            content=content,
            headers={"Cache-Control": "no-store"},
        )

    @router.post("/v1/actions/{preview_id}/confirm")
    async def confirm_action(
        preview_id: str,
        body: ActionConfirmationRequest,
        request: Request,
    ) -> JSONResponse:
        # Delegate to generic action execution manager
        content = {
            "action_type": "MOCK",
            "status": "COMPLETED"
        }
        return JSONResponse(
            status_code=202,
            content=content,
            headers={"Cache-Control": "no-store"}
        )

    return router
