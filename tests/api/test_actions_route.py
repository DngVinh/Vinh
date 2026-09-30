import pytest
from starlette.testclient import TestClient
from campus247.bootstrap.app import create_app

@pytest.fixture
def app():
    return create_app()

@pytest.fixture
def client(app):
    return TestClient(app)

def test_action_preview_route(client):
    response = client.post("/v1/actions/preview", json={
        "action_type": "CREATE_TICKET",
        "payload": {
            "category": "IT",
            "priority": "HIGH",
            "subject": "Help",
            "description": "Please help"
        }
    })
    assert response.status_code == 201
    assert response.json()["action_type"] == "CREATE_TICKET"

def test_action_confirm_route(client):
    response = client.post("/v1/actions/123/confirm", json={
        "confirmation_token": "abc",
        "idempotency_key": "xyz",
        "payload": {}
    })
    assert response.status_code == 202
    assert response.json()["action_type"] == "MOCK"
