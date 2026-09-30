from __future__ import annotations

from datetime import datetime, timezone, timedelta
from pathlib import Path
import sys
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient
import pytest

ROOT = Path(__file__).resolve().parents[2]
API_SRC = ROOT / "services" / "api" / "src"
if str(API_SRC) not in sys.path:
    sys.path.insert(0, str(API_SRC))

from campus247.domain.shared.values import generate_uuid7
from campus247.ports.identity import IdentityContext, IdentityRole
from campus247.presentation.identity import IdentityMiddleware
from campus247.presentation.middleware.abuse_limits import (
    AbuseLimiterMiddleware,
    InMemoryRateLimiterStore,
    RateLimitRule,
)


class DummyIdentityAdapter:
    def __init__(self):
        self.contexts: dict[str, IdentityContext] = {}

    def resolve_token(self, token: str) -> IdentityContext:
        if token in self.contexts:
            return self.contexts[token]
        raise ValueError("Invalid token")


def make_token(adapter: DummyIdentityAdapter, user_id: str) -> str:
    now = datetime.now(timezone.utc)
    ctx = IdentityContext(
        subject_id=user_id,
        external_subject=f"sub-{user_id[:8]}",
        issuer="https://auth.huce.edu.vn",
        roles=(IdentityRole.STUDENT,),
        display_name=f"User {user_id[:6]}",
        student_code="SV123456",
        auth_time=now,
        expires_at=now + timedelta(hours=1),
    )
    token = f"tok-{user_id}"
    adapter.contexts[token] = ctx
    return token


@pytest.fixture
def limiter_app():
    store = InMemoryRateLimiterStore()
    app = FastAPI()
    identity_adapter = DummyIdentityAdapter()
    
    # Abuse limiter middleware placed inside identity so request.state.identity is populated
    app.add_middleware(
        AbuseLimiterMiddleware,
        store=store,
        rules=[
            RateLimitRule(path_prefix="/v1/expensive", max_requests=3, window_seconds=60, fail_closed=True),
            RateLimitRule(path_prefix="/v1/open", max_requests=5, window_seconds=60, fail_closed=False),
        ],
    )
    app.add_middleware(IdentityMiddleware, adapter=identity_adapter)

    @app.get("/v1/expensive")
    async def expensive_endpoint(request: Request):
        return {"status": "ok", "message": "expensive work completed"}

    @app.get("/v1/open")
    async def open_endpoint(request: Request):
        return {"status": "ok"}

    client = TestClient(app)
    return client, identity_adapter, store


def test_rate_limit_exceeded_returns_429(limiter_app):
    """AC-TASK-API-ABUSE-001-01: Excess requests are rejected before expensive work."""
    client, _, _ = limiter_app

    # Send 3 allowed requests
    for i in range(3):
        resp = client.get("/v1/expensive")
        assert resp.status_code == 200

    # 4th request must be rejected with 429
    resp = client.get("/v1/expensive")
    assert resp.status_code == 429
    assert "Retry-After" in resp.headers
    data = resp.json()
    assert data.get("status") == 429 or "detail" in data or "title" in data


def test_client_forwarding_headers_cannot_spoof_key(limiter_app):
    """AC-TASK-API-ABUSE-001-02: Client-controlled forwarding headers cannot bypass or poison limiter key."""
    client, _, _ = limiter_app

    # Send 3 requests with spoofed X-Forwarded-For headers
    for i in range(3):
        resp = client.get(
            "/v1/expensive",
            headers={"X-Forwarded-For": f"198.51.100.{i+1}, 10.0.0.1", "X-Real-IP": f"203.0.113.{i+1}"},
        )
        assert resp.status_code == 200

    # 4th request from same socket client must be rejected despite changing forwarding header
    resp = client.get(
        "/v1/expensive",
        headers={"X-Forwarded-For": "198.51.100.99", "X-Real-IP": "203.0.113.99"},
    )
    assert resp.status_code == 429


def test_principal_aware_isolation(limiter_app):
    """Authenticated requests are limited by principal, isolating distinct users."""
    client, adapter, _ = limiter_app
    user_a = generate_uuid7()
    user_b = generate_uuid7()
    tok_a = make_token(adapter, user_a)
    tok_b = make_token(adapter, user_b)

    # Exhaust user A's quota
    for _ in range(3):
        resp = client.get("/v1/expensive", headers={"Authorization": f"Bearer {tok_a}"})
        assert resp.status_code == 200

    resp_a = client.get("/v1/expensive", headers={"Authorization": f"Bearer {tok_a}"})
    assert resp_a.status_code == 429

    # User B should still have quota available
    resp_b = client.get("/v1/expensive", headers={"Authorization": f"Bearer {tok_b}"})
    assert resp_b.status_code == 200


def test_fail_closed_on_limiter_store_error(limiter_app):
    """AC-TASK-API-ABUSE-001-03: Limiter degradation follows fail-closed policy on expensive endpoints."""
    client, _, store = limiter_app

    # Inject store failure
    store.inject_error(RuntimeError("Rate limit database connection lost"))

    # Fail closed on expensive endpoint -> 503 Service Unavailable
    resp_expensive = client.get("/v1/expensive")
    assert resp_expensive.status_code in (503, 429)

    # Bounded safe on non-fail-closed endpoint -> allows request or returns safe degradation
    resp_open = client.get("/v1/open")
    assert resp_open.status_code == 200
