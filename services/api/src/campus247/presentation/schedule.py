from __future__ import annotations

from datetime import datetime
from typing import Any
from fastapi import APIRouter, HTTPException, Query, Request
from starlette.responses import JSONResponse

from campus247.domain.shared.values import generate_uuid7
from campus247.ports.policy import (
    AuthorizationPolicyPort,
    PolicyEvaluationRequest,
    PolicyResourceContext,
)
from campus247.ports.schedule import ScheduleQuery, ScheduleReadPort
from campus247.presentation.identity import get_current_identity


def create_schedule_router(
    schedule_adapter: ScheduleReadPort,
    policy_engine: AuthorizationPolicyPort | None = None,
) -> APIRouter:
    router = APIRouter(tags=["Schedule"])

    @router.get("/v1/students/me/schedule")
    async def list_my_schedule(
        request: Request,
        from_time: str = Query(..., alias="from"),
        to_time: str = Query(..., alias="to"),
        cursor: str | None = Query(None),
        limit: int = Query(20, ge=1, le=100),
    ) -> JSONResponse:
        identity = get_current_identity(request)

        if policy_engine is not None:
            eval_req = PolicyEvaluationRequest(
                actor=identity,
                action="schedule.read",
                resource_type="schedule",
                correlation_id=generate_uuid7(),
                resource=PolicyResourceContext(owner_subject_id=identity.subject_id),
            )
            decision = policy_engine.evaluate(eval_req)
            if not decision.is_allowed:
                raise HTTPException(
                    status_code=403,
                    detail={"error": "forbidden", "reason": decision.reason_code},
                )

        try:
            starts_at = datetime.fromisoformat(from_time.replace("Z", "+00:00"))
            ends_at = datetime.fromisoformat(to_time.replace("Z", "+00:00"))
        except Exception:
            raise HTTPException(status_code=422, detail="Invalid date format for 'from' or 'to'")

        if starts_at >= ends_at:
            raise HTTPException(status_code=422, detail="'from' must be before 'to'")

        query = ScheduleQuery(
            internal_user_id=identity.subject_id,
            starts_at=starts_at,
            ends_at=ends_at,
            cursor=cursor,
            limit=limit,
        )

        page = await schedule_adapter.list_schedule(query)

        content = {
            "items": [
                {
                    "id": item.id,
                    "course_code": item.course_code,
                    "course_name": item.course_name,
                    "starts_at": item.starts_at.isoformat(),
                    "ends_at": item.ends_at.isoformat(),
                    "location_label": item.location_label,
                    "instructor_display_name": item.instructor_display_name,
                    "source_system": item.source_system,
                }
                for item in page.items
            ],
            "page": {
                "next_cursor": page.page.next_cursor,
                "has_more": page.page.has_more,
                "limit": page.page.limit,
            },
        }

        return JSONResponse(
            status_code=200,
            content=content,
            headers={"Cache-Control": "no-store"},
        )

    return router
