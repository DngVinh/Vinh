from __future__ import annotations

import json
from pathlib import Path
import sys
from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.testclient import TestClient
import jsonschema
from pydantic import BaseModel, Field
import pytest
import yaml

ROOT = Path(__file__).resolve().parents[2]
API_SRC = ROOT / "services" / "api" / "src"
if str(API_SRC) not in sys.path:
    sys.path.insert(0, str(API_SRC))

from campus247.presentation.errors import (
    http_exception_handler,
    validation_exception_handler,
)
from campus247.bootstrap.app import RequestIdMiddleware

SCHEMA_PATH = ROOT / "contracts" / "json-schema" / "common" / "error.schema.json"


def load_error_schema() -> dict:
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


class SampleBody(BaseModel):
    name: str = Field(..., min_length=2)
    count: int = Field(..., ge=1)


@pytest.fixture
def error_test_app():
    app = FastAPI()
    app.add_middleware(RequestIdMiddleware)
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)

    @app.get("/test/404")
    def trigger_404():
        raise HTTPException(status_code=404, detail="Không tìm thấy mục yêu cầu")

    @app.get("/test/403")
    def trigger_403():
        raise HTTPException(status_code=403, detail="Forbidden: conversation ownership required")

    @app.post("/test/422")
    def trigger_422(body: SampleBody):
        return {"ok": True}

    return app


def test_problem_details_404_conforms_to_schema(error_test_app):
    schema = load_error_schema()
    client = TestClient(error_test_app)

    resp = client.get("/test/404")
    assert resp.status_code == 404
    assert resp.headers["Content-Type"] == "application/problem+json"

    data = resp.json()
    assert data["code"] == "RESOURCE_NOT_FOUND"
    assert data["status"] == 404
    assert data["title"] == "Tài nguyên không tồn tại"
    assert data["type"] == "https://campus247.example/problems/resource-not-found"
    assert "request_id" in data
    assert data["instance"] == f"urn:request:{data['request_id']}"
    assert data["retryable"] is False

    jsonschema.validate(instance=data, schema=schema)


def test_problem_details_403_conforms_to_schema(error_test_app):
    schema = load_error_schema()
    client = TestClient(error_test_app)

    resp = client.get("/test/403")
    assert resp.status_code == 403
    assert resp.headers["Content-Type"] == "application/problem+json"

    data = resp.json()
    assert data["code"] == "FORBIDDEN"
    jsonschema.validate(instance=data, schema=schema)


def test_problem_details_422_conforms_to_schema(error_test_app):
    schema = load_error_schema()
    client = TestClient(error_test_app)

    resp = client.post("/test/422", json={"name": "a", "count": 0})
    assert resp.status_code == 422
    assert resp.headers["Content-Type"] == "application/problem+json"

    data = resp.json()
    assert data["code"] == "VALIDATION_FAILED"
    assert "errors" in data
    assert len(data["errors"]) >= 1

    jsonschema.validate(instance=data, schema=schema)
