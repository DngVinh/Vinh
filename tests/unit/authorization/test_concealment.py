from __future__ import annotations

from pathlib import Path
import sys
from fastapi import FastAPI, HTTPException, Request
from fastapi.testclient import TestClient
import pytest

ROOT = Path(__file__).resolve().parents[3]
API_SRC = ROOT / "services" / "api" / "src"
if str(API_SRC) not in sys.path:
    sys.path.insert(0, str(API_SRC))

from campus247.application.audit.writer import AuditWriter
from campus247.application.authorization.concealment import (
    AccessDenialReason,
    ConcealedAccessResult,
    ExistenceConcealmentService,
)
from campus247.domain.shared.values import generate_uuid7
from campus247.presentation.errors import http_exception_handler


class MockAuditWriter(AuditWriter):
    def __init__(self):
        super().__init__()
        self.recorded_events: list[dict] = []

    def record_event(self, **kwargs) -> str:
        self.recorded_events.append(kwargs)
        return "audit-event-id"


@pytest.fixture
def concealment_system():
    audit = MockAuditWriter()
    service = ExistenceConcealmentService(audit_writer=audit)

    app = FastAPI()
    app.add_exception_handler(HTTPException, http_exception_handler)

    from campus247.application.authorization.concealment import ResourceNotFoundError
    from campus247.presentation.errors import create_problem_details
    @app.exception_handler(ResourceNotFoundError)
    async def resource_not_found_handler(request: Request, exc: ResourceNotFoundError):
        return create_problem_details(
            request=request,
            status=404,
            code="RESOURCE_NOT_FOUND",
            title="Tài nguyên không tồn tại",
            detail=str(exc)
        )

    @app.get("/v1/items/{item_id}")
    async def get_item(item_id: str, request: Request):
        actor_id = request.headers.get("X-Test-Actor-Id", "actor-default")
        # Route delegates to concealment service
        outcome = service.evaluate_read_access(
            actor_id=actor_id,
            resource_type="ticket",
            resource_id=item_id,
        )
        if not outcome.is_accessible:
            # Conceal existence: raise standardized 404
            service.audit_and_conceal(actor_id=actor_id, outcome=outcome)
        return {"id": item_id, "data": "item content"}

    client = TestClient(app)
    return client, service, audit


def test_absent_object_and_unauthorized_object_return_identical_semantics(concealment_system):
    """AC-TASK-API-CONCEAL-001-01: External callers cannot distinguish absent from unauthorized objects."""
    client, service, _ = concealment_system

    # Register an item owned by user-owner
    item_id = generate_uuid7()
    service.register_resource(
        resource_id=item_id,
        resource_type="ticket",
        owner_id="user-owner",
        tenant_id="tenant-huce",
    )

    # 1. Access by unauthorized user
    resp_unauth = client.get(
        f"/v1/items/{item_id}",
        headers={"X-Test-Actor-Id": "user-attacker"},
    )
    assert resp_unauth.status_code == 404
    body_unauth = resp_unauth.json()

    # 2. Access to non-existent object
    non_existent_id = generate_uuid7()
    resp_absent = client.get(
        f"/v1/items/{non_existent_id}",
        headers={"X-Test-Actor-Id": "user-attacker"},
    )
    assert resp_absent.status_code == 404
    body_absent = resp_absent.json()

    # AC-TASK-API-CONCEAL-001-01: Same status, title, type, and detail format
    assert resp_unauth.status_code == resp_absent.status_code == 404
    assert body_unauth["type"] == body_absent["type"]
    assert body_unauth["title"] == body_absent["title"]
    assert body_unauth["code"] == body_absent["code"]
    assert body_unauth["detail"] == body_absent["detail"]
    assert "user-owner" not in resp_unauth.text
    assert "tenant-huce" not in resp_unauth.text


def test_cross_tenant_access_concealed_identically(concealment_system):
    """Cross-tenant requests disclose no cross-tenant existence."""
    client, service, _ = concealment_system

    item_id = generate_uuid7()
    service.register_resource(
        resource_id=item_id,
        resource_type="ticket",
        owner_id="user-foreign",
        tenant_id="tenant-foreign",
    )

    resp = client.get(
        f"/v1/items/{item_id}",
        headers={"X-Test-Actor-Id": "user-local"},
    )
    assert resp.status_code == 404
    data = resp.json()
    assert data["code"] == "RESOURCE_NOT_FOUND"
    assert "tenant-foreign" not in resp.text


def test_internal_audit_records_true_denial_category(concealment_system):
    """AC-TASK-API-CONCEAL-001-02: Internal audit retains true denial category without leaking to caller."""
    client, service, audit = concealment_system

    item_id = generate_uuid7()
    service.register_resource(
        resource_id=item_id,
        resource_type="ticket",
        owner_id="user-owner",
        tenant_id="tenant-huce",
    )

    resp = client.get(
        f"/v1/items/{item_id}",
        headers={"X-Test-Actor-Id": "user-attacker"},
    )
    assert resp.status_code == 404

    # Check recorded audit event
    assert len(audit.recorded_events) >= 1
    event = audit.recorded_events[-1]
    assert event["action_code"] == "authorization.access_denied"
    assert event["outcome"] == "DENIED"
    assert event["metadata"]["denial_reason"] == AccessDenialReason.UNAUTHORIZED_OWNER.value
    assert event["metadata"]["resource_id"] == item_id

    # Caller must NOT see the denial reason
    assert "UNAUTHORIZED_OWNER" not in resp.text


def test_authorized_access_succeeds(concealment_system):
    """AC-TASK-API-CONCEAL-001-03: Authorized caller receives resource data normally."""
    client, service, _ = concealment_system

    item_id = generate_uuid7()
    service.register_resource(
        resource_id=item_id,
        resource_type="ticket",
        owner_id="user-owner",
        tenant_id="tenant-huce",
    )

    resp = client.get(
        f"/v1/items/{item_id}",
        headers={"X-Test-Actor-Id": "user-owner"},
    )
    assert resp.status_code == 200
    assert resp.json()["id"] == item_id
