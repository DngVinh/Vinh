from __future__ import annotations

import json
from pathlib import Path
import pytest
import yaml
from jsonschema import Draft202012Validator, ValidationError
from referencing import Registry, Resource
from referencing.jsonschema import DRAFT202012

ROOT = Path(__file__).resolve().parents[2]
ASYNCAPI_PATH = ROOT / "contracts" / "asyncapi" / "v1" / "asyncapi.yaml"
JSON_SCHEMAS_DIR = ROOT / "contracts" / "json-schema"


@pytest.fixture(scope="module")
def asyncapi_spec() -> dict:
    with open(ASYNCAPI_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


@pytest.fixture(scope="module")
def schema_registry(asyncapi_spec: dict) -> Registry:
    registry = Registry()
    # Register asyncapi document
    asyncapi_res = Resource.from_contents(asyncapi_spec, default_specification=DRAFT202012)
    registry = registry.with_resource(asyncapi_spec.get("id", "urn:campus247:asyncapi:events:v1"), asyncapi_res)

    # Register local json-schemas for relative resolution
    for schema_file in JSON_SCHEMAS_DIR.glob("**/*.schema.json"):
        with open(schema_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        res = Resource.from_contents(data, default_specification=DRAFT202012)
        if "$id" in data:
            registry = registry.with_resource(data["$id"], res)
        # Also register relative path from asyncapi dir: ../../json-schema/...
        rel_path = f"../../json-schema/{schema_file.relative_to(JSON_SCHEMAS_DIR).as_posix()}"
        registry = registry.with_resource(rel_path, res)

    return registry


def test_asyncapi_structure_and_metadata(asyncapi_spec: dict):
    """Verify AsyncAPI 3.0.0 top-level structural integrity and channels."""
    assert asyncapi_spec["asyncapi"] == "3.0.0"
    assert asyncapi_spec["id"] == "urn:campus247:asyncapi:events:v1"
    assert "channels" in asyncapi_spec
    assert "operations" in asyncapi_spec
    assert "components" in asyncapi_spec

    expected_channels = {
        "ticketEvents",
        "handoverEvents",
        "actionEvents",
        "knowledgeEvents",
        "notificationRequests",
    }
    assert expected_channels.issubset(set(asyncapi_spec["channels"].keys()))


def test_ticket_created_event_positive_and_negative(asyncapi_spec: dict, schema_registry: Registry):
    """Verify TicketCreatedV1 schema validates conforming event and rejects invalid payload."""
    doc_id = asyncapi_spec["id"]
    schema = {"$ref": f"{doc_id}#/components/schemas/TicketCreatedV1"}
    validator = Draft202012Validator(schema, registry=schema_registry)

    valid_event = {
        "event_id": "018f6c4a-5b6c-7123-8abc-def012345678",
        "event_type": "ticket.created",
        "event_version": 1,
        "occurred_at": "2026-09-22T10:00:00Z",
        "producer": "ticket-domain",
        "aggregate_type": "ticket",
        "aggregate_id": "018f6c4a-5b6c-7123-8abc-def012345679",
        "aggregate_version": 1,
        "partition_key": "018f6c4a-5b6c-7123-8abc-def012345679",
        "correlation_id": "018f6c4a-5b6c-7123-8abc-def012345670",
        "causation_id": None,
        "data_classification": "PERSONAL",
        "payload": {
            "ticket_id": "018f6c4a-5b6c-7123-8abc-def012345679",
            "requester_user_id": "018f6c4a-5b6c-7123-8abc-def012345671",
            "category": "GENERAL_SUPPORT",
            "priority": "NORMAL",
            "queue_key": "HUCE_GENERAL",
            "status": "OPEN",
            "created_at": "2026-09-22T10:00:00Z",
        },
    }
    validator.validate(valid_event)

    # Negative 1: invalid UUIDv7 format in event_id
    invalid_event_bad_uuid = dict(valid_event, event_id="not-a-valid-uuidv7")
    with pytest.raises(ValidationError):
        validator.validate(invalid_event_bad_uuid)

    # Negative 2: missing required payload fields
    invalid_event_missing_payload = dict(valid_event, payload={"ticket_id": valid_event["aggregate_id"]})
    with pytest.raises(ValidationError):
        validator.validate(invalid_event_missing_payload)

    # Negative 3: invalid classification
    invalid_event_bad_class = dict(valid_event, data_classification="TOP_SECRET")
    with pytest.raises(ValidationError):
        validator.validate(invalid_event_bad_class)
