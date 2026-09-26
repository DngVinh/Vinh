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

from campus247.infrastructure.identity.mock import SyntheticIdentityAdapter
from campus247.ports.identity import IdentityContext, IdentityRole
from campus247.presentation.identity import IdentityMiddleware, get_current_identity


@pytest.fixture
def test_app():
    adapter = SyntheticIdentityAdapter(secret_key="middleware-test-secret", environment="test")
    app = FastAPI()
    app.add_middleware(IdentityMiddleware, adapter=adapter)

    @app.get("/public")
    def public_route():
        return {"status": "ok"}

    @app.get("/protected")
    def protected_route(identity: IdentityContext = Depends(get_current_identity)):
        return {
            "subject_id": identity.subject_id,
            "roles": [r.value for r in identity.roles],
            "display_name": identity.display_name,
        }

    return app, adapter


def test_public_route_without_token(test_app):
    app, _ = test_app
    client = TestClient(app)
    resp = client.get("/public")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_protected_route_without_token(test_app):
    app, _ = test_app
    client = TestClient(app)
    resp = client.get("/protected")
    assert resp.status_code == 401
    data = resp.json()
    err_code = data.get("code") or (data.get("detail", {}).get("code") if isinstance(data.get("detail"), dict) else None)
    assert err_code == "AUTHENTICATION_REQUIRED"


def test_protected_route_with_valid_token(test_app):
    app, adapter = test_app
    token = adapter.mint_token(user_id_or_code="SV240000")
    client = TestClient(app)
    resp = client.get("/protected", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    data = resp.json()
    assert "STUDENT" in data["roles"]
    assert data["display_name"] != ""


def test_protected_route_with_invalid_token(test_app):
    app, _ = test_app
    client = TestClient(app)
    resp = client.get("/protected", headers={"Authorization": "Bearer invalid.token"})
    assert resp.status_code == 401
