from __future__ import annotations

from typing import Any
from fastapi import HTTPException, Request
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response

from campus247.domain.shared.values import ErrorCode, ProblemDetails, generate_uuid7
from campus247.ports.identity import IdentityContext


class IdentityMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: Any, adapter: Any) -> None:
        super().__init__(app)
        self._adapter = adapter

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        auth_header = request.headers.get("Authorization")
        token: str | None = None
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header[7:].strip()
        elif "auth_token" in request.cookies:
            token = request.cookies["auth_token"]

        identity: IdentityContext | None = None
        if token:
            try:
                identity = self._adapter.resolve_token(token)
            except Exception:
                identity = None

        request.state.identity = identity
        return await call_next(request)


def get_current_identity(request: Request) -> IdentityContext:
    identity = getattr(request.state, "identity", None)
    if identity is None or not isinstance(identity, IdentityContext):
        problem = ProblemDetails(
            type="https://campus247.example/problems/authentication-required",
            title="Authentication Required",
            status=401,
            detail="A valid Bearer token or signed session is required.",
            instance=str(request.url.path),
            code=ErrorCode.AUTHENTICATION_REQUIRED,
            request_id=generate_uuid7(),
            retryable=False,
        )
        raise HTTPException(status_code=401, detail=problem.to_dict())
    return identity


def create_identity_router() -> APIRouter:
    from fastapi import APIRouter
    from fastapi.responses import JSONResponse

    router = APIRouter(tags=["Identity"])

    @router.get("/v1/users/me")
    async def get_current_user_profile(request: Request) -> JSONResponse:
        identity = get_current_identity(request)
        content: dict[str, Any] = {
            "user_id": identity.subject_id,
            "display_name": identity.display_name,
            "roles": [r.value for r in identity.roles],
            "is_synthetic": identity.is_synthetic,
        }
        if identity.email:
            content["primary_email"] = identity.email
        if identity.faculty_code:
            content["faculty_code"] = identity.faculty_code
        if identity.student_code:
            content["student_code"] = identity.student_code

        return JSONResponse(
            status_code=200,
            content=content,
            headers={"Cache-Control": "no-store"},
        )

    return router


router = create_identity_router()

