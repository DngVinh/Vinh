from __future__ import annotations

from fastapi import APIRouter, Header, HTTPException
from starlette.responses import JSONResponse

from campus247.application.identity.logout import LogoutService, RevocationError


def create_logout_router(logout_service: LogoutService) -> APIRouter:
    router = APIRouter()

    @router.post("/logout")
    async def logout(authorization: str | None = Header(default=None)):
        token = None
        if authorization and authorization.startswith("Bearer "):
            token = authorization[7:].strip()
        if not token:
            token = authorization

        if not token:
            raise HTTPException(status_code=400, detail="Missing authorization token")

        try:
            logout_service.logout(token)
            return JSONResponse(status_code=200, content={"status": "revoked"})
        except RevocationError as e:
            return JSONResponse(status_code=500, content={"status": "error", "detail": str(e)})

    return router
