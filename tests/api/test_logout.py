from __future__ import annotations

from pathlib import Path
import sys
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient
import pytest

ROOT = Path(__file__).resolve().parents[2]
API_SRC = ROOT / "services" / "api" / "src"
SYNTH_SRC = ROOT / "packages" / "synthetic" / "src"
for p in [API_SRC, SYNTH_SRC]:
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from campus247.application.identity.logout import InMemoryRevocationStore, LogoutService, RevocationError
from campus247.infrastructure.identity.mock import SyntheticIdentityAdapter
from campus247.presentation.identity import IdentityMiddleware, get_current_identity
from campus247.presentation.logout import create_logout_router


@pytest.fixture
def test_env():
    revocation_store = InMemoryRevocationStore()
    logout_service = LogoutService(revocation_store=revocation_store)
    adapter = SyntheticIdentityAdapter(secret_key="logout-test-secret", environment="test")

    app = FastAPI()

    # Modified middleware check that accounts for revocation
    class RevokingIdentityMiddleware(IdentityMiddleware):
        async def dispatch(self, request, call_next):
            auth_header = request.headers.get("Authorization")
            token = auth_header[7:].strip() if auth_header and auth_header.startswith("Bearer ") else None
            if token and revocation_store.is_revoked(token):
                request.state.identity = None
                return await call_next(request)
            return await super().dispatch(request, call_next)

    app.add_middleware(RevokingIdentityMiddleware, adapter=adapter)
    app.include_router(create_logout_router(logout_service=logout_service), prefix="/v1/auth")

    @app.get("/protected")
    def protected_route(identity=Depends(get_current_identity)):
        return {"user": identity.display_name}

    return app, adapter, logout_service, revocation_store


def test_logout_revokes_session_and_replay_denied(test_env):
    app, adapter, _, _ = test_env
    client = TestClient(app)
    token = adapter.mint_token("SV240000")

    # Request with token works
    resp1 = client.get("/protected", headers={"Authorization": f"Bearer {token}"})
    assert resp1.status_code == 200

    # Logout
    logout_resp = client.post("/v1/auth/logout", headers={"Authorization": f"Bearer {token}"})
    assert logout_resp.status_code == 200
    assert logout_resp.json()["status"] == "revoked"

    # Replay request is now denied (401)
    resp2 = client.get("/protected", headers={"Authorization": f"Bearer {token}"})
    assert resp2.status_code == 401


def test_logout_failure_returns_error_without_false_success(test_env):
    app, adapter, logout_service, _ = test_env

    # Simulate revocation store failure
    class FailingStore:
        def revoke(self, token: str) -> None:
            raise RevocationError("Store unavailable")
        def is_revoked(self, token: str) -> bool:
            return False

    failing_logout_service = LogoutService(revocation_store=FailingStore())
    failing_app = FastAPI()
    failing_app.include_router(create_logout_router(logout_service=failing_logout_service), prefix="/v1/auth")
    client = TestClient(failing_app)

    token = adapter.mint_token("SV240000")
    resp = client.post("/v1/auth/logout", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 500
    assert resp.json()["status"] != "revoked"
