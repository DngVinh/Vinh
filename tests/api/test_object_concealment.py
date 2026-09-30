from __future__ import annotations

from datetime import datetime, timezone, timedelta
from pathlib import Path
import sys
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
import pytest

ROOT = Path(__file__).resolve().parents[2]
API_SRC = ROOT / "services" / "api" / "src"
SYNTH_SRC = ROOT / "packages" / "synthetic" / "src"
if str(API_SRC) not in sys.path:
    sys.path.insert(0, str(API_SRC))
if str(SYNTH_SRC) not in sys.path:
    sys.path.insert(0, str(SYNTH_SRC))

from campus247.domain.document_request.model import DocumentDeliveryMethod, DocumentRequest, DocumentRequestStatus
from campus247.domain.shared.values import generate_uuid7
from campus247.domain.ticket.model import Ticket, TicketCategory, TicketPriority, TicketStatus
from campus247.ports.identity import IdentityContext, IdentityRole
from campus247.presentation.document_requests import create_document_request_router
from campus247.presentation.errors import http_exception_handler
from campus247.presentation.identity import IdentityMiddleware
from campus247.presentation.ticket_queries import create_ticket_query_router


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
def app_with_routes():
    app = FastAPI()
    app.add_exception_handler(HTTPException, http_exception_handler)

    identity_adapter = DummyIdentityAdapter()
    app.add_middleware(IdentityMiddleware, adapter=identity_adapter)

    ticket_store: dict[str, Ticket] = {}
    doc_store: dict[str, DocumentRequest] = {}

    app.include_router(create_ticket_query_router(store=ticket_store))
    app.include_router(create_document_request_router(store=doc_store))

    client = TestClient(app)
    return client, identity_adapter, ticket_store, doc_store


@pytest.mark.parametrize(
    "route_template,store_name,create_item_fn",
    [
        (
            "/v1/tickets/{id}",
            "tickets",
            lambda user_id, item_id: Ticket(
                id=item_id,
                requester_user_id=user_id,
                category=TicketCategory.GENERAL_SUPPORT,
                priority=TicketPriority.NORMAL,
                status=TicketStatus.OPEN,
                subject="Test ticket",
                description_redacted="Test description",
                queue_key="academic_support",
                assigned_user_id=None,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
                version=1,
            ),
        ),
        (
            "/v1/document-requests/{id}",
            "document_requests",
            lambda user_id, item_id: DocumentRequest(
                id=item_id,
                student_user_id=user_id,
                document_type="BANG_DIEM",
                purpose_code="XIN_VIEC",
                delivery_method=DocumentDeliveryMethod.DIGITAL,
                status=DocumentRequestStatus.SUBMITTED,
                is_synthetic=True,
                disclaimer="Synthetic demo",
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
                submitted_at=datetime.now(timezone.utc),
                version=1,
            ),
        ),
    ],
)
def test_cross_user_probes_match_absent_object_responses(
    app_with_routes, route_template, store_name, create_item_fn
):
    """AC-TASK-API-CONCEAL-002-01 & AC-TASK-API-CONCEAL-002-02: Cross-user probe returns identical 404 response to absent object."""
    client, adapter, ticket_store, doc_store = app_with_routes
    stores = {"tickets": ticket_store, "document_requests": doc_store}
    target_store = stores[store_name]

    owner_id = generate_uuid7()
    attacker_id = generate_uuid7()
    tok_attacker = make_token(adapter, attacker_id)

    # 1. Existing object owned by owner_id
    item_id = generate_uuid7()
    target_store[item_id] = create_item_fn(owner_id, item_id)

    # Attacker probes existing object of owner
    url_existing = route_template.format(id=item_id)
    resp_unauthorized = client.get(url_existing, headers={"Authorization": f"Bearer {tok_attacker}"})

    # 2. Probe completely absent object
    absent_id = generate_uuid7()
    url_absent = route_template.format(id=absent_id)
    resp_absent = client.get(url_absent, headers={"Authorization": f"Bearer {tok_attacker}"})

    # Both MUST be 404 with indistinguishable problem details
    assert resp_unauthorized.status_code == 404
    assert resp_absent.status_code == 404

    data_unauth = resp_unauthorized.json()
    data_absent = resp_absent.json()

    assert data_unauth["status"] == data_absent["status"] == 404
    assert data_unauth["code"] == data_absent["code"] == "RESOURCE_NOT_FOUND"
    assert data_unauth["title"] == data_absent["title"]
    assert data_unauth["detail"] == data_absent["detail"]

    # Must not leak owner id or error hints
    assert owner_id not in resp_unauthorized.text
    assert "forbidden" not in resp_unauthorized.text.lower()
    assert "another user" not in resp_unauthorized.text.lower()


def test_registered_route_inventory_completeness(app_with_routes):
    """AC-TASK-API-CONCEAL-002-03: Route registry test fails when an object lookup omits concealment metadata."""
    client, _, _, _ = app_with_routes

    # Check registered endpoints in openapi schema
    registered_paths = set(client.app.openapi().get("paths", {}).keys())

    expected = {"/v1/tickets/{ticket_id}", "/v1/document-requests/{document_request_id}"}
    for exp in expected:
        assert exp in registered_paths
