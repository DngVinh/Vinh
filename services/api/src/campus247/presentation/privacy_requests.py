from __future__ import annotations

from typing import Any
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field
from starlette.responses import JSONResponse

from campus247.application.privacy.requests import PrivacyRequestService
from campus247.presentation.identity import get_current_identity


class CreatePrivacyRequestBody(BaseModel):
    request_type: str
    correction_summary: str | None = Field(None, min_length=1, max_length=1000)
    requester_note: str | None = Field(None, min_length=1, max_length=1000)


def create_privacy_request_router(service: PrivacyRequestService) -> APIRouter:
    router = APIRouter(tags=["Privacy"])

    @router.post("/v1/privacy/requests")
    async def create_privacy_request(
        body: CreatePrivacyRequestBody,
        request: Request,
    ) -> JSONResponse:
        identity = get_current_identity(request)
        try:
            record, receipt = service.create_request(
                actor=identity,
                request_type=body.request_type,
                correction_summary=body.correction_summary,
                requester_note=body.requester_note,
            )
        except ValueError as e:
            raise HTTPException(status_code=422, detail=str(e))

        content = {
            "request_id": receipt.request_id,
            "request_type": receipt.request_type,
            "status": receipt.status,
            "received_at": receipt.received_at,
            "tracking_reference": receipt.tracking_reference,
        }
        return JSONResponse(
            status_code=201,
            content=content,
            headers={
                "Location": f"/v1/privacy/requests/{record.id}",
                "Cache-Control": "no-store",
            },
        )

    @router.get("/v1/privacy/requests/{privacy_request_id}")
    async def get_my_privacy_request_status(
        privacy_request_id: str,
        request: Request,
    ) -> JSONResponse:
        identity = get_current_identity(request)
        status_view = service.get_my_request_status(identity, privacy_request_id)
        if not status_view:
            raise HTTPException(status_code=404, detail="Privacy request not found")

        content = {
            "request_id": status_view.request_id,
            "request_type": status_view.request_type,
            "status": status_view.status,
            "received_at": status_view.received_at,
            "updated_at": status_view.updated_at,
            "next_action": status_view.next_action,
        }
        return JSONResponse(
            status_code=200,
            content=content,
            headers={"Cache-Control": "no-store"},
        )

    return router
