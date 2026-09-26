from __future__ import annotations

import json
from pathlib import Path
import pytest
from jsonschema import Draft202012Validator, ValidationError

ROOT = Path(__file__).resolve().parents[2]
SCHEMAS_DIR = ROOT / "contracts" / "json-schema"


def test_every_json_schema_is_valid_draft_2020_12():
    """Verify all machine JSON schema contracts are valid Draft 2020-12 specifications."""
    schema_files = list(SCHEMAS_DIR.glob("**/*.schema.json"))
    assert len(schema_files) >= 9, f"Expected at least 9 schemas, found {len(schema_files)}"

    for schema_path in schema_files:
        with open(schema_path, "r", encoding="utf-8") as f:
            schema = json.load(f)
        Draft202012Validator.check_schema(schema)


def test_error_schema_positive_and_negative_validation():
    """Verify common error schema validates conforming and rejects invalid payloads."""
    error_schema_path = SCHEMAS_DIR / "common" / "error.schema.json"
    with open(error_schema_path, "r", encoding="utf-8") as f:
        schema = json.load(f)

    validator = Draft202012Validator(schema)

    # Positive sample
    valid_payload = {
        "type": "https://campus247.example/problems/authentication-required",
        "title": "Authentication Required",
        "status": 401,
        "detail": "Bearer token missing or expired.",
        "instance": "/v1/users/me",
        "code": "AUTHENTICATION_REQUIRED",
        "request_id": "019213ab-0000-7000-8000-000000000001",
        "retryable": False,
    }
    validator.validate(valid_payload)

    # Negative sample (invalid code enum and missing required fields)
    invalid_payload = {
        "type": "https://campus247.example/problems/not-a-valid-code",
        "title": "Bad Request",
        "status": 400,
        "detail": "Test error",
        "instance": "/test",
        "code": "NON_EXISTENT_ERROR_CODE",
        "request_id": "invalid-uuid",
        "retryable": False,
    }
    with pytest.raises(ValidationError):
        validator.validate(invalid_payload)
