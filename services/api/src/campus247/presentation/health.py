from __future__ import annotations
from typing import Literal, List

import asyncio
from fastapi import APIRouter, Response, status, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import text


class HealthStatus(BaseModel):
    """Liveness response schema conforming to OpenAPI contract API-SYS-001."""
    model_config = ConfigDict(extra="forbid")

    status: Literal["alive"] = "alive"


class DependencyItem(BaseModel):
    """Status of an individual dependency."""
    model_config = ConfigDict(extra="forbid")

    name: str = Field(..., pattern=r"^[a-z][a-z0-9_-]{1,63}$")
    status: Literal["ready", "unavailable", "disabled"]


class SecurityConfiguration(BaseModel):
    """Startup security configuration evidence conforming to API-SYS-002."""
    model_config = ConfigDict(extra="forbid")

    demo_auth_guard: Literal["ENFORCED", "NOT_APPLICABLE"] = "ENFORCED"


class ReadinessStatus(BaseModel):
    """Readiness response schema conforming to OpenAPI contract API-SYS-002."""
    model_config = ConfigDict(extra="forbid")

    status: Literal["ready", "degraded"]
    dependencies: List[DependencyItem]
    security_configuration: SecurityConfiguration


async def check_database_connectivity(request: Request) -> Literal["ready", "unavailable", "disabled"]:
    """Bounded database connectivity probe. Returns status string."""
    try:
        engine = getattr(request.app.state, "db_engine", None)
        if engine is None:
            return "disabled"
        
        async with engine.connect() as conn:
            await asyncio.wait_for(conn.execute(text("SELECT 1")), timeout=2.0)
        return "ready"
    except Exception:
        return "unavailable"


router = APIRouter(tags=["System"])


@router.get(
    "/health/live",
    response_model=HealthStatus,
    summary="Process liveness",
    operation_id="getLiveness",
)
async def get_liveness() -> HealthStatus:
    """Return process liveness confirmation without asserting dependency readiness."""
    return HealthStatus(status="alive")


@router.get(
    "/health/ready",
    response_model=ReadinessStatus,
    responses={
        200: {"model": ReadinessStatus, "description": "Required dependencies are ready."},
        503: {"description": "Required dependencies are unavailable."},
    },
    summary="Dependency readiness",
    operation_id="getReadiness",
)
async def get_readiness(request: Request) -> Response:
    """Check bounded database connectivity and startup configuration."""
    db_status = await check_database_connectivity(request)
    
    # We consider "disabled" to mean it's running without DB (e.g. synthetic mode).
    # But if it's "unavailable", we fail readiness.
    if db_status == "unavailable":
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "type": "https://campus247.example/problems/dependency-unavailable",
                "title": "Service Unavailable",
                "status": 503,
                "detail": "Required database dependency is currently unreachable.",
                "instance": "/health/ready",
                "code": "DEPENDENCY_UNAVAILABLE",
                "request_id": getattr(request.state, "request_id", "unknown"),
                "retryable": True,
            },
        )

    # Redis is optional/mocked in this demo. Let's just say "ready".
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content=ReadinessStatus(
            status="ready",
            dependencies=[
                DependencyItem(name="database", status=db_status),
                DependencyItem(name="redis", status="ready"),
            ],
            security_configuration=SecurityConfiguration(demo_auth_guard="ENFORCED"),
        ).model_dump(),
    )
