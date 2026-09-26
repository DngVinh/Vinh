from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import sys
from fastapi import FastAPI
from fastapi.testclient import TestClient
import pytest

ROOT = Path(__file__).resolve().parents[2]
API_SRC = ROOT / "services" / "api" / "src"
SYNTH_SRC = ROOT / "packages" / "synthetic" / "src"
if str(API_SRC) not in sys.path:
    sys.path.insert(0, str(API_SRC))
if str(SYNTH_SRC) not in sys.path:
    sys.path.insert(0, str(SYNTH_SRC))

from campus247.domain.policy.student import StudentPolicyEngine
from campus247.infrastructure.identity.mock import SyntheticIdentityAdapter
from campus247.infrastructure.schedule.synthetic import SyntheticScheduleAdapter
from campus247.presentation.identity import IdentityMiddleware
from campus247.presentation.schedule import create_schedule_router


@pytest.fixture
def client() -> TestClient:
    app = FastAPI()
    identity_adapter = SyntheticIdentityAdapter(secret_key="secret-test-key-247")
    app.add_middleware(IdentityMiddleware, adapter=identity_adapter)
    
    policy_engine = StudentPolicyEngine()
    schedule_adapter = SyntheticScheduleAdapter()
    
    router = create_schedule_router(schedule_adapter, policy_engine)
    app.include_router(router)
    
    return TestClient(app)


def test_schedule_me_unauthenticated(client: TestClient):
    resp = client.get("/v1/students/me/schedule?from=2026-10-01T00:00:00Z&to=2026-10-31T23:59:59Z")
    assert resp.status_code == 401


def test_schedule_me_authenticated_student(client: TestClient):
    identity_adapter = SyntheticIdentityAdapter(secret_key="secret-test-key-247")
    student_id = "4b419a1b-6d41-7dfb-8943-2edd9f071385"
    token = identity_adapter.mint_token(student_id)

    headers = {"Authorization": f"Bearer {token}"}
    resp = client.get(
        "/v1/students/me/schedule?from=2026-10-01T00:00:00Z&to=2026-10-31T23:59:59Z",
        headers=headers,
    )
    assert resp.status_code == 200
    assert resp.headers.get("cache-control") == "no-store"
    data = resp.json()
    assert "items" in data
    assert "page" in data
    assert len(data["items"]) > 0
    assert data["items"][0]["source_system"] == "SYNTHETIC_SIS"


def test_schedule_me_invalid_range(client: TestClient):
    identity_adapter = SyntheticIdentityAdapter(secret_key="secret-test-key-247")
    student_id = "4b419a1b-6d41-7dfb-8943-2edd9f071385"
    token = identity_adapter.mint_token(student_id)

    headers = {"Authorization": f"Bearer {token}"}
    resp = client.get(
        "/v1/students/me/schedule?from=2026-10-31T00:00:00Z&to=2026-10-01T00:00:00Z",
        headers=headers,
    )
    assert resp.status_code == 422


def test_schedule_me_pagination(client: TestClient):
    identity_adapter = SyntheticIdentityAdapter(secret_key="secret-test-key-247")
    student_id = "4b419a1b-6d41-7dfb-8943-2edd9f071385"
    token = identity_adapter.mint_token(student_id)

    headers = {"Authorization": f"Bearer {token}"}
    resp = client.get(
        "/v1/students/me/schedule?from=2026-10-01T00:00:00Z&to=2026-10-31T23:59:59Z&limit=1",
        headers=headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["items"]) == 1
    assert data["page"]["limit"] == 1


def test_schedule_me_non_student_denied(client: TestClient):
    identity_adapter = SyntheticIdentityAdapter(secret_key="secret-test-key-247")
    staff_id = "29bd0539-5a74-7638-b04b-713ce38305ab"
    token = identity_adapter.mint_token(staff_id)

    headers = {"Authorization": f"Bearer {token}"}
    resp = client.get(
        "/v1/students/me/schedule?from=2026-10-01T00:00:00Z&to=2026-10-31T23:59:59Z",
        headers=headers,
    )
    assert resp.status_code == 403

