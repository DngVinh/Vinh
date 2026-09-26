"""Comprehensive contract verification suite across API and Event boundaries (TASK-TEST-CONTRACT-001)."""

from pathlib import Path
import json
import pytest
import yaml
from jsonschema import Draft202012Validator, ValidationError
from referencing import Registry, Resource
from referencing.jsonschema import DRAFT202012

ROOT = Path(__file__).resolve().parents[2]
OPENAPI_PATH = ROOT / "contracts" / "openapi" / "v1" / "openapi.yaml"
ASYNCAPI_PATH = ROOT / "contracts" / "asyncapi" / "v1" / "asyncapi.yaml"
TOOL_REGISTRY_PATH = ROOT / "contracts" / "tools" / "tool-registry.yaml"
JSON_SCHEMAS_DIR = ROOT / "contracts" / "json-schema"


def test_openapi_boundary_contract():
    assert OPENAPI_PATH.is_file()
    with OPENAPI_PATH.open("r", encoding="utf-8") as f:
        spec = yaml.safe_load(f)

    assert spec.get("openapi", "").startswith("3.1")
    paths = spec.get("paths", {})
    # Verify core domain boundaries are present in contract
    assert "/health/live" in paths
    assert any("/conversations" in p for p in paths), "Conversations endpoint missing in contract"
    assert any("/rooms" in p for p in paths), "Room endpoints missing in contract"
    assert any("/knowledge" in p for p in paths), "Knowledge endpoints missing in contract"
    assert any("/tickets" in p for p in paths), "Tickets endpoints missing in contract"


def test_asyncapi_event_contract():
    assert ASYNCAPI_PATH.is_file()
    with ASYNCAPI_PATH.open("r", encoding="utf-8") as f:
        spec = yaml.safe_load(f)

    assert spec.get("asyncapi") == "3.0.0"
    messages = spec.get("components", {}).get("messages", {})
    expected_event_types = {
        "ticket.created.v1",
        "handover.queued.v1",
        "action.execution_completed.v1",
        "knowledge.version_published.v1",
    }
    actual_names = {m.get("name") for m in messages.values()}
    for expected in expected_event_types:
        assert expected in actual_names, f"Event {expected} missing in AsyncAPI spec"


def test_tool_registry_boundary_contract():
    assert TOOL_REGISTRY_PATH.is_file()
    with TOOL_REGISTRY_PATH.open("r", encoding="utf-8") as f:
        registry = yaml.safe_load(f)

    tools = registry.get("tools", [])
    tool_ids = {t.get("tool_id") for t in tools}
    assert "TOOL-SCHEDULE-001" in tool_ids
    assert "TOOL-TICKET-001" in tool_ids
    assert "TOOL-HITL-001" in tool_ids


def test_event_payload_negative_validation():
    with ASYNCAPI_PATH.open("r", encoding="utf-8") as f:
        asyncapi_spec = yaml.safe_load(f)

    registry = Registry()
    asyncapi_res = Resource.from_contents(asyncapi_spec, default_specification=DRAFT202012)
    doc_id = asyncapi_spec.get("id", "urn:campus247:asyncapi:events:v1")
    registry = registry.with_resource(doc_id, asyncapi_res)

    for schema_file in JSON_SCHEMAS_DIR.glob("**/*.schema.json"):
        with open(schema_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        res = Resource.from_contents(data, default_specification=DRAFT202012)
        if "$id" in data:
            registry = registry.with_resource(data["$id"], res)
        rel_path = f"../../json-schema/{schema_file.relative_to(JSON_SCHEMAS_DIR).as_posix()}"
        registry = registry.with_resource(rel_path, res)

    schema = {"$ref": f"{doc_id}#/components/schemas/TicketCreatedV1"}
    validator = Draft202012Validator(schema, registry=registry)

    invalid_event = {
        "event_id": "not-a-valid-uuidv7",
        "event_type": "ticket.created",
        "event_version": 1,
        "occurred_at": "2026-09-22T10:00:00Z",
        "producer": "ticket-domain",
    }
    with pytest.raises(ValidationError):
        validator.validate(invalid_event)
