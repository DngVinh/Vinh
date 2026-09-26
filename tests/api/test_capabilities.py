from __future__ import annotations

from pathlib import Path
import sys
from fastapi import FastAPI
from fastapi.testclient import TestClient
import pytest

ROOT = Path(__file__).resolve().parents[2]
API_SRC = ROOT / "services" / "api" / "src"
if str(API_SRC) not in sys.path:
    sys.path.insert(0, str(API_SRC))

from campus247.presentation.capabilities import (
    CapabilityManager,
    SystemState,
    create_capabilities_router,
)


@pytest.fixture
def setup_app():
    app = FastAPI()
    manager = CapabilityManager()
    router = create_capabilities_router(manager)
    app.include_router(router)
    client = TestClient(app)
    return client, manager


def test_get_capabilities_default_normal(setup_app):
    client, _ = setup_app
    resp = client.get("/v1/capabilities")
    assert resp.status_code == 200
    data = resp.json()
    assert data["system_state"] == "NORMAL"
    assert data["capabilities"]["chat_generation"] is True
    assert data["capabilities"]["document_search"] is True
    assert data["capabilities"]["ticket_create"] is True
    assert resp.headers.get("cache-control") is not None


def test_get_capabilities_operations_route(setup_app):
    client, _ = setup_app
    resp = client.get("/v1/operations/capabilities")
    assert resp.status_code == 200
    data = resp.json()
    assert data["system_state"] == "NORMAL"


def test_degraded_no_llm_state(setup_app):
    client, manager = setup_app
    manager.set_state(SystemState.DEGRADED_NO_LLM, reason="DeepSeek provider timeout circuit open")

    resp = client.get("/v1/capabilities")
    assert resp.status_code == 200
    data = resp.json()
    assert data["system_state"] == "DEGRADED_NO_LLM"
    assert data["capabilities"]["chat_generation"] is False
    assert data["capabilities"]["tool_planning"] is False
    assert data["capabilities"]["document_search"] is True
    assert data["degradation_reason"] == "DeepSeek provider timeout circuit open"
    assert data["banner_message"] is not None


def test_read_only_state(setup_app):
    client, manager = setup_app
    manager.set_state(SystemState.READ_ONLY, reason="Database replica lag")

    resp = client.get("/v1/capabilities")
    assert resp.status_code == 200
    data = resp.json()
    assert data["system_state"] == "READ_ONLY"
    assert data["capabilities"]["ticket_create"] is False
    assert data["capabilities"]["room_booking"] is False
    assert data["capabilities"]["document_search"] is True


def test_maintenance_state(setup_app):
    client, manager = setup_app
    manager.set_state(SystemState.MAINTENANCE, reason="Planned database schema upgrade")

    resp = client.get("/v1/capabilities")
    assert resp.status_code == 200
    data = resp.json()
    assert data["system_state"] == "MAINTENANCE"
    assert data["capabilities"]["chat_generation"] is False
    assert data["capabilities"]["ticket_create"] is False
    assert data["capabilities"]["document_search"] is False


def test_invalid_state_transition_rejected(setup_app):
    _, manager = setup_app
    with pytest.raises(ValueError, match="Invalid system state"):
        manager.set_state("INVALID_STATE")
