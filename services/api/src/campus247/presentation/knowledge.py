from __future__ import annotations

from typing import Any
from fastapi import APIRouter, HTTPException, Query, Request
from starlette.responses import JSONResponse

from campus247.ports.identity import IdentityRole
from campus247.presentation.identity import get_current_identity


def create_knowledge_router(
    sources: dict[str, dict[str, Any]] | None = None,
    versions: dict[str, dict[str, Any]] | None = None,
) -> APIRouter:
    router = APIRouter(tags=["Knowledge"])
    sources_store: dict[str, dict[str, Any]] = sources if sources is not None else {}
    versions_store: dict[str, dict[str, Any]] = versions if versions is not None else {}

    def _require_admin(request: Request) -> None:
        identity = get_current_identity(request)
        if not (identity.has_role(IdentityRole.KNOWLEDGE_ADMIN) or identity.has_role(IdentityRole.SYSTEM_ADMIN)):
            raise HTTPException(
                status_code=403,
                detail="Forbidden: Knowledge operations require KNOWLEDGE_ADMIN or SYSTEM_ADMIN role",
            )

    @router.get("/v1/knowledge/sources")
    async def list_knowledge_sources(
        request: Request,
        cursor: str | None = Query(None),
        limit: int = Query(20, ge=1, le=100),
    ) -> JSONResponse:
        _require_admin(request)

        items_list = list(sources_store.values())
        items_list.sort(key=lambda s: (s.get("created_at", ""), s.get("id", "")))

        offset = 0
        if cursor:
            try:
                offset = int(cursor)
            except ValueError:
                offset = 0

        paged = items_list[offset : offset + limit]
        has_more = (offset + limit) < len(items_list)
        next_cursor = str(offset + limit) if has_more else None

        content = {
            "items": paged,
            "page": {
                "next_cursor": next_cursor,
                "has_more": has_more,
                "limit": limit,
            },
        }
        return JSONResponse(status_code=200, content=content, headers={"Cache-Control": "no-store"})

    @router.get("/v1/knowledge/sources/{source_id}")
    async def get_knowledge_source(source_id: str, request: Request) -> JSONResponse:
        _require_admin(request)
        source = sources_store.get(source_id)
        if not source:
            raise HTTPException(status_code=404, detail="Knowledge source not found")

        version_num = source.get("version", 1)
        return JSONResponse(
            status_code=200,
            content=source,
            headers={
                "ETag": f'"{version_num}"',
                "Cache-Control": "no-store",
            },
        )

    @router.get("/v1/knowledge/document-versions/{document_version_id}")
    async def get_document_version(document_version_id: str, request: Request) -> JSONResponse:
        _require_admin(request)
        version_item = versions_store.get(document_version_id)
        if not version_item:
            raise HTTPException(status_code=404, detail="Document version not found")

        # Exclude private storage object key from presentation response (SEC-CTRL-012)
        safe_item = {k: v for k, v in version_item.items() if k != "storage_object_key"}
        version_num = safe_item.get("version", 1)
        return JSONResponse(
            status_code=200,
            content=safe_item,
            headers={
                "ETag": f'"{version_num}"',
                "Cache-Control": "no-store",
            },
        )

    return router
