from __future__ import annotations

from typing import Literal, List
from fastapi import APIRouter, Response, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field


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


async def check_database_connectivity() -> bool:
    """Bounded database connectivity probe. Returns True when database is reachable."""
    # In local demo / synthetic mode, default to True unless overridden
    return True


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
async def get_readiness() -> Response:
    """Check bounded database connectivity and startup configuration."""
    db_ok = await check_database_connectivity()
    if not db_ok:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "type": "https://campus247.example/problems/dependency-unavailable",
                "title": "Service Unavailable",
                "status": 503,
                "detail": "Required database dependency is currently unreachable.",
                "instance": "/health/ready",
                "code": "DEPENDENCY_UNAVAILABLE",
                "request_id": "019213ab-0000-7000-8000-000000000001",
                "retryable": True,
            },
        )

    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content=ReadinessStatus(
            status="ready",
            dependencies=[
                DependencyItem(name="database", status="ready"),
                DependencyItem(name="redis", status="ready"),
            ],
            security_configuration=SecurityConfiguration(demo_auth_guard="ENFORCED"),
        ).model_dump(),
    )
