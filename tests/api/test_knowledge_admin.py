from __future__ import annotations

from datetime import datetime, timezone, timedelta
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

from campus247.domain.shared.values import generate_uuid7
from campus247.ports.identity import IdentityContext, IdentityRole
from campus247.presentation.identity import IdentityMiddleware
from campus247.presentation.knowledge import create_knowledge_router


class DummyIdentityAdapter:
    def __init__(self):
        self.contexts: dict[str, IdentityContext] = {}

    def resolve_token(self, token: str) -> IdentityContext:
        if token in self.contexts:
            return self.contexts[token]
        raise ValueError("Invalid token")


@pytest.fixture
def setup_app():
    app = FastAPI()
    identity_adapter = DummyIdentityAdapter()
    app.add_middleware(IdentityMiddleware, adapter=identity_adapter)

    sources_store: dict[str, dict] = {}
    versions_store: dict[str, dict] = {}
    router = create_knowledge_router(sources=sources_store, versions=versions_store)
    app.include_router(router)

    client = TestClient(app)
    return client, identity_adapter, sources_store, versions_store


def make_token(
    adapter: DummyIdentityAdapter,
    user_id: str,
    role: IdentityRole = IdentityRole.KNOWLEDGE_ADMIN,
) -> str:
    now = datetime.now(timezone.utc)
    ctx = IdentityContext(
        subject_id=user_id,
        external_subject=f"sub-{user_id[:8]}",
        issuer="https://auth.huce.edu.vn",
        roles=(role,),
        display_name="Admin Test",
        student_code="SV123456" if role == IdentityRole.STUDENT else None,
        auth_time=now,
        expires_at=now + timedelta(hours=1),
    )
    token = f"tok-{user_id}"
    adapter.contexts[token] = ctx
    return token


def test_list_knowledge_sources_unauthenticated(setup_app):
    client, _, _, _ = setup_app
    resp = client.get("/v1/knowledge/sources")
    assert resp.status_code == 401


def test_list_knowledge_sources_forbidden_for_student(setup_app):
    client, adapter, _, _ = setup_app
    student_id = generate_uuid7()
    token = make_token(adapter, student_id, role=IdentityRole.STUDENT)
    resp = client.get("/v1/knowledge/sources", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 403


def test_list_knowledge_sources_forbidden_for_support_officer(setup_app):
    client, adapter, _, _ = setup_app
    officer_id = generate_uuid7()
    token = make_token(adapter, officer_id, role=IdentityRole.SUPPORT_OFFICER)
    resp = client.get("/v1/knowledge/sources", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 403


def test_list_knowledge_sources_success_for_admin(setup_app):
    client, adapter, sources_store, _ = setup_app
    admin_id = generate_uuid7()
    token = make_token(adapter, admin_id, role=IdentityRole.KNOWLEDGE_ADMIN)

    s1 = {
        "id": generate_uuid7(),
        "source_type": "OFFICIAL_DOCUMENT",
        "canonical_uri": "https://huce.edu.vn/docs/qd-123.pdf",
        "title": "Quy chế đào tạo đại học",
        "owner_unit": "Phòng Đào tạo",
        "authority_level": 90,
        "approval_status": "APPROVED",
        "is_synthetic": True,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "version": 1,
    }
    sources_store[s1["id"]] = s1

    resp = client.get("/v1/knowledge/sources", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["items"]) == 1
    assert data["items"][0]["id"] == s1["id"]
    assert data["items"][0]["title"] == s1["title"]


def test_get_knowledge_source(setup_app):
    client, adapter, sources_store, _ = setup_app
    admin_id = generate_uuid7()
    token = make_token(adapter, admin_id, role=IdentityRole.KNOWLEDGE_ADMIN)

    s_id = generate_uuid7()
    s1 = {
        "id": s_id,
        "source_type": "OFFICIAL_WEB",
        "canonical_uri": "https://huce.edu.vn/thong-bao",
        "title": "Thông báo học vụ",
        "owner_unit": "Ban Giám hiệu",
        "authority_level": 80,
        "approval_status": "APPROVED",
        "is_synthetic": True,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "version": 2,
    }
    sources_store[s_id] = s1

    resp = client.get(f"/v1/knowledge/sources/{s_id}", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert resp.headers.get("etag") == '"2"'
    assert resp.json()["id"] == s_id

    resp_404 = client.get(f"/v1/knowledge/sources/{generate_uuid7()}", headers={"Authorization": f"Bearer {token}"})
    assert resp_404.status_code == 404


def test_get_document_version(setup_app):
    client, adapter, _, versions_store = setup_app
    admin_id = generate_uuid7()
    token = make_token(adapter, admin_id, role=IdentityRole.KNOWLEDGE_ADMIN)

    v_id = generate_uuid7()
    source_id = generate_uuid7()
    v1 = {
        "id": v_id,
        "source_id": source_id,
        "version_label": "1.0.0",
        "content_checksum": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        "effective_from": None,
        "effective_until": None,
        "status": "PUBLISHED",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "published_at": datetime.now(timezone.utc).isoformat(),
        "version": 1,
    }
    versions_store[v_id] = v1

    resp = client.get(f"/v1/knowledge/document-versions/{v_id}", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert resp.headers.get("etag") == '"1"'
    assert resp.json()["id"] == v_id

    resp_404 = client.get(f"/v1/knowledge/document-versions/{generate_uuid7()}", headers={"Authorization": f"Bearer {token}"})
    assert resp_404.status_code == 404
