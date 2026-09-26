from __future__ import annotations

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

from campus247.domain.ticket.model import Ticket, TicketCategory, TicketPriority
from campus247.infrastructure.identity.mock import SyntheticIdentityAdapter
from campus247.presentation.identity import IdentityMiddleware
from campus247.presentation.ticket_queries import create_ticket_query_router


@pytest.fixture
def setup_app():
    app = FastAPI()
    identity_adapter = SyntheticIdentityAdapter(secret_key="secret-test-key-247")
    app.add_middleware(IdentityMiddleware, adapter=identity_adapter)

    ticket_store: dict[str, Ticket] = {}
    router = create_ticket_query_router(store=ticket_store)
    app.include_router(router)

    client = TestClient(app)
    return client, identity_adapter, ticket_store


def test_list_tickets_unauthenticated(setup_app):
    client, _, _ = setup_app
    resp = client.get("/v1/tickets")
    assert resp.status_code == 401


def test_list_tickets_owner_scoped(setup_app):
    client, identity_adapter, ticket_store = setup_app
    student_1 = "4b419a1b-6d41-7dfb-8943-2edd9f071385"
    student_2 = "97c5ab40-6399-7ad3-9838-eab50f267b2d"

    t1 = Ticket.create_draft(student_1, TicketCategory.GENERAL_SUPPORT, TicketPriority.NORMAL, "T1", "Desc").request_confirmation().confirm_create()
    t2 = Ticket.create_draft(student_2, TicketCategory.GENERAL_SUPPORT, TicketPriority.NORMAL, "T2", "Desc").request_confirmation().confirm_create()
    ticket_store[t1.id] = t1
    ticket_store[t2.id] = t2

    token_1 = identity_adapter.mint_token(student_1)
    resp = client.get("/v1/tickets", headers={"Authorization": f"Bearer {token_1}"})
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["items"]) == 1
    assert data["items"][0]["id"] == t1.id


def test_get_ticket_not_found(setup_app):
    client, identity_adapter, _ = setup_app
    student_1 = "4b419a1b-6d41-7dfb-8943-2edd9f071385"
    token_1 = identity_adapter.mint_token(student_1)

    resp = client.get("/v1/tickets/01923456-789a-7def-8123-456789abcde1", headers={"Authorization": f"Bearer {token_1}"})
    assert resp.status_code == 404


def test_get_ticket_forbidden_other_student(setup_app):
    client, identity_adapter, ticket_store = setup_app
    student_1 = "4b419a1b-6d41-7dfb-8943-2edd9f071385"
    student_2 = "97c5ab40-6399-7ad3-9838-eab50f267b2d"

    t1 = Ticket.create_draft(student_1, TicketCategory.GENERAL_SUPPORT, TicketPriority.NORMAL, "T1", "Desc").request_confirmation().confirm_create()
    ticket_store[t1.id] = t1

    token_2 = identity_adapter.mint_token(student_2)
    resp = client.get(f"/v1/tickets/{t1.id}", headers={"Authorization": f"Bearer {token_2}"})
    assert resp.status_code == 403


def test_get_ticket_success(setup_app):
    client, identity_adapter, ticket_store = setup_app
    student_1 = "4b419a1b-6d41-7dfb-8943-2edd9f071385"

    t1 = Ticket.create_draft(student_1, TicketCategory.GENERAL_SUPPORT, TicketPriority.NORMAL, "T1", "Desc").request_confirmation().confirm_create()
    ticket_store[t1.id] = t1

    token_1 = identity_adapter.mint_token(student_1)
    resp = client.get(f"/v1/tickets/{t1.id}", headers={"Authorization": f"Bearer {token_1}"})
    assert resp.status_code == 200
    assert resp.headers.get("etag") == f'"{t1.version}"'
    assert resp.json()["id"] == t1.id
