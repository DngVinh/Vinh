from __future__ import annotations

from datetime import date, datetime, timezone
import json
from pathlib import Path
import sys
import pytest
from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[3]
API_SRC = ROOT / "services" / "api" / "src"
if str(API_SRC) not in sys.path:
    sys.path.insert(0, str(API_SRC))

from campus247.domain.shared.values import (
    ErrorCode,
    FieldError,
    ProblemDetails,
    format_date,
    format_rfc3339,
    generate_uuid7,
    is_valid_uuid7,
    now_utc,
    parse_date,
    parse_rfc3339,
)

ROOT = Path(__file__).resolve().parents[3]
ERROR_SCHEMA_PATH = ROOT / "contracts" / "json-schema" / "common" / "error.schema.json"


def test_uuid7_generation_and_validation():
    uuid_str = generate_uuid7()
    assert is_valid_uuid7(uuid_str)
    assert not is_valid_uuid7("not-a-uuid")
    # UUIDv4 is not UUIDv7
    assert not is_valid_uuid7("4a66a1e8-7e3e-4b67-96a9-8566a7ecf30b")


def test_rfc3339_timestamp_handling():
    now = now_utc()
    assert now.tzinfo is not None
    formatted = format_rfc3339(now)
    assert formatted.endswith("Z")
    parsed = parse_rfc3339(formatted)
    assert parsed.tzinfo == timezone.utc

    with pytest.raises(ValueError, match="must end with Z"):
        parse_rfc3339("2026-09-22T10:00:00+07:00")


def test_date_handling():
    d = date(2026, 9, 22)
    formatted = format_date(d)
    assert formatted == "2026-09-22"
    parsed = parse_date(formatted)
    assert parsed == d


def test_problem_details_conforms_to_schema():
    req_id = generate_uuid7()
    problem = ProblemDetails(
        type="https://campus247.example/problems/resource-not-found",
        title="Resource Not Found",
        status=404,
        detail="The requested ticket could not be found.",
        instance="/v1/tickets/018f6c4a-5b6c-7123-8abc-def012345678",
        code=ErrorCode.RESOURCE_NOT_FOUND,
        request_id=req_id,
        retryable=False,
        errors=[FieldError(code="NOT_FOUND", pointer="/ticket_id", detail="Ticket ID missing")],
    )
    data = problem.to_dict()

    with open(ERROR_SCHEMA_PATH, "r", encoding="utf-8") as f:
        schema = json.load(f)
    validator = Draft202012Validator(schema)
    validator.validate(data)


def test_problem_details_negative_validation():
    req_id = generate_uuid7()
    # Invalid status code
    with pytest.raises(ValueError, match="HTTP status code must be between 400 and 599"):
        ProblemDetails(
            type="https://campus247.example/problems/validation-failed",
            title="Bad",
            status=200,
            detail="detail",
            instance="/test",
            code=ErrorCode.VALIDATION_FAILED,
            request_id=req_id,
            retryable=False,
        )

    # Invalid request_id (not uuid7)
    with pytest.raises(ValueError, match="request_id must be valid UUIDv7"):
        ProblemDetails(
            type="https://campus247.example/problems/validation-failed",
            title="Bad",
            status=400,
            detail="detail",
            instance="/test",
            code=ErrorCode.VALIDATION_FAILED,
            request_id="invalid-uuid",
            retryable=False,
        )
