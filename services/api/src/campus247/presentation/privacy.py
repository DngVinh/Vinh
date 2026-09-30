from __future__ import annotations

from typing import Any
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field
from starlette.responses import JSONResponse

from campus247.application.privacy.consent import (
    ConsentRequiredError,
    CrossSubjectUnauthorizedError,
    DuplicateOperationError,
    LegalHoldConflictError,
    PrivacyConsentService,
    PrivacyOperationAuthorizationService,
)
from campus247.presentation.identity import get_current_identity


class PrivacyOperationRequest(BaseModel):
    operation_type: str = Field(..., min_length=1, max_length=50)
    target_subject_id: str = Field(..., min_length=1, max_length=100)
    purpose: str = Field(..., min_length=1, max_length=100)
    scope: list[str] = Field(..., min_length=1)
    requester_note: str | None = Field(None, max_length=1000)


def create_privacy_authorization_router(
    consent_service: PrivacyConsentService,
    authz_service: PrivacyOperationAuthorizationService,
) -> APIRouter:
    router = APIRouter(tags=["Privacy Authorization"])

    @router.post("/v1/privacy/operations")
    async def request_privacy_operation(
        body: PrivacyOperationRequest,
        request: Request,
    ) -> JSONResponse:
        identity = get_current_identity(request)
        try:
            record = authz_service.authorize_and_queue(
                actor=identity,
                operation_type=body.operation_type,
                target_subject_id=body.target_subject_id,
                purpose=body.purpose,
                scope=body.scope,
                requester_note=body.requester_note,
            )
        except CrossSubjectUnauthorizedError:
            # AC-TASK-API-PRIVFIX-001-03: Denied requests disclose no cross-subject existence or protected metadata.
            raise HTTPException(
                status_code=404,
                detail="Privacy resource or target subject not accessible",
            )
        except ConsentRequiredError as e:
            # AC-TASK-API-PRIVFIX-001-02: Revoked or absent consent cannot be treated as implicit approval.
            raise HTTPException(
                status_code=403,
                detail=str(e),
            )
        except LegalHoldConflictError as e:
            # Statutory / legal hold conflict blocks erasure
            raise HTTPException(
                status_code=409,
                detail=str(e),
            )
        except DuplicateOperationError as e:
            # In-flight duplicate rejected
            raise HTTPException(
                status_code=409,
                detail=str(e),
            )
        except ValueError as e:
            # Invalid scope, purpose, or unsupported operation
            raise HTTPException(
                status_code=422,
                detail=str(e),
            )

        content = {
            "operation_id": record.id,
            "operation_type": record.operation_type,
            "status": record.status,
            "tracking_reference": record.tracking_reference,
            "created_at": record.created_at.isoformat(),
        }
        return JSONResponse(
            status_code=201,
            content=content,
            headers={
                "Location": f"/v1/privacy/operations/{record.id}",
                "Cache-Control": "no-store",
            },
        )

    return router
