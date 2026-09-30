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

from campus247.domain.document_request.model import (
    DocumentDeliveryMethod,
    DocumentRequest,
)
from campus247.infrastructure.identity.mock import SyntheticIdentityAdapter
from campus247.presentation.document_requests import create_document_request_router
from campus247.presentation.identity import IdentityMiddleware


@pytest.fixture
def setup_app():
    app = FastAPI()
    identity_adapter = SyntheticIdentityAdapter(secret_key="secret-test-key-247")
    app.add_middleware(IdentityMiddleware, adapter=identity_adapter)

    doc_store: dict[str, DocumentRequest] = {}
    router = create_document_request_router(store=doc_store)
    app.include_router(router)

    client = TestClient(app)
    return client, identity_adapter, doc_store


def test_list_document_requests_unauthenticated(setup_app):
    client, _, _ = setup_app
    resp = client.get("/v1/document-requests")
    assert resp.status_code == 401


def test_list_document_requests_empty(setup_app):
    client, identity_adapter, _ = setup_app
    student_id = "4b419a1b-6d41-7dfb-8943-2edd9f071385"
    token = identity_adapter.mint_token(student_id)

    resp = client.get(
        "/v1/document-requests",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["items"] == []
    assert data["page"]["limit"] == 20


def test_get_document_request_not_found(setup_app):
    client, identity_adapter, _ = setup_app
    student_id = "4b419a1b-6d41-7dfb-8943-2edd9f071385"
    token = identity_adapter.mint_token(student_id)

    resp = client.get(
        "/v1/document-requests/01923456-789a-7def-8123-456789abcdef",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 404


def test_get_document_request_forbidden(setup_app):
    client, identity_adapter, doc_store = setup_app
    student_1 = "4b419a1b-6d41-7dfb-8943-2edd9f071385"
    student_2 = "97c5ab40-6399-7ad3-9838-eab50f267b2d"

    doc = DocumentRequest.create_draft(
        student_user_id=student_1,
        document_type="STUDENT_CERTIFICATE",
        purpose_code="VISA",
        delivery_method=DocumentDeliveryMethod.DIGITAL,
    )
    doc_store[doc.id] = doc

    token_2 = identity_adapter.mint_token(student_2)
    resp = client.get(
        f"/v1/document-requests/{doc.id}",
        headers={"Authorization": f"Bearer {token_2}"},
    )
    assert resp.status_code == 404


def test_get_document_request_success(setup_app):
    client, identity_adapter, doc_store = setup_app
    student_1 = "4b419a1b-6d41-7dfb-8943-2edd9f071385"

    doc = DocumentRequest.create_draft(
        student_user_id=student_1,
        document_type="TRANSCRIPT",
        purpose_code="JOB_APPLICATION",
        delivery_method=DocumentDeliveryMethod.PICKUP,
    )
    doc_store[doc.id] = doc

    token_1 = identity_adapter.mint_token(student_1)
    resp = client.get(
        f"/v1/document-requests/{doc.id}",
        headers={"Authorization": f"Bearer {token_1}"},
    )
    assert resp.status_code == 200
    assert resp.headers.get("etag") == f'"{doc.version}"'

    data = resp.json()
    assert data["id"] == doc.id
    assert data["document_type"] == "TRANSCRIPT"
    assert data["purpose_code"] == "JOB_APPLICATION"
    assert data["delivery_method"] == "PICKUP"
    assert data["is_synthetic"] is True
    assert data["disclaimer"] == "DỮ LIỆU MÔ PHỎNG — KHÔNG CÓ GIÁ TRỊ"
