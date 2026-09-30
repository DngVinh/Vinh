from __future__ import annotations

from typing import Any
from fastapi import APIRouter, HTTPException, Query, Request
from starlette.responses import JSONResponse

from campus247.domain.document_request.model import DocumentRequest
from campus247.presentation.identity import get_current_identity


def create_document_request_router(
    store: dict[str, DocumentRequest] | None = None,
) -> APIRouter:
    router = APIRouter(tags=["DocumentRequests"])
    storage: dict[str, DocumentRequest] = store if store is not None else {}

    @router.get("/v1/document-requests")
    async def list_my_document_requests(
        request: Request,
        cursor: str | None = Query(None),
        limit: int = Query(20, ge=1, le=100),
    ) -> JSONResponse:
        identity = get_current_identity(request)

        user_docs = [
            doc for doc in storage.values() if doc.student_user_id == identity.subject_id
        ]
        user_docs.sort(key=lambda d: (d.created_at, d.id))

        offset = 0
        if cursor:
            try:
                offset = int(cursor)
            except ValueError:
                offset = 0

        paged = user_docs[offset : offset + limit]
        has_more = (offset + limit) < len(user_docs)
        next_cursor = str(offset + limit) if has_more else None

        items = [
            {
                "id": doc.id,
                "document_type": doc.document_type,
                "purpose_code": doc.purpose_code,
                "delivery_method": doc.delivery_method.value,
                "status": doc.status.value,
                "is_synthetic": doc.is_synthetic,
                "disclaimer": doc.disclaimer,
                "created_at": doc.created_at.isoformat(),
                "submitted_at": doc.submitted_at.isoformat() if doc.submitted_at else None,
                "version": doc.version,
            }
            for doc in paged
        ]

        content = {
            "items": items,
            "page": {
                "next_cursor": next_cursor,
                "has_more": has_more,
                "limit": limit,
            },
        }

        return JSONResponse(status_code=200, content=content)

    @router.get("/v1/document-requests/{document_request_id}")
    async def get_document_request(
        document_request_id: str,
        request: Request,
    ) -> JSONResponse:
        identity = get_current_identity(request)

        doc = storage.get(document_request_id)
        if not doc or doc.student_user_id != identity.subject_id:
            # AC-TASK-API-CONCEAL-002-01 & 02: Conceal existence with uniform 404
            raise HTTPException(status_code=404, detail="Không tìm thấy tài nguyên")

        content = {
            "id": doc.id,
            "document_type": doc.document_type,
            "purpose_code": doc.purpose_code,
            "delivery_method": doc.delivery_method.value,
            "status": doc.status.value,
            "is_synthetic": doc.is_synthetic,
            "disclaimer": doc.disclaimer,
            "created_at": doc.created_at.isoformat(),
            "submitted_at": doc.submitted_at.isoformat() if doc.submitted_at else None,
            "version": doc.version,
        }

        return JSONResponse(
            status_code=200,
            content=content,
            headers={
                "ETag": f'"{doc.version}"',
                "Cache-Control": "no-store",
            },
        )

    return router
