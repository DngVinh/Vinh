"""Offline validation for Campus 24/7 event, tool and evaluation contracts.

No network access, provider call, fixture generation or file mutation is performed.
Run from repository root: python evals/validate_contracts.py
"""

from __future__ import annotations

import json
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any

import yaml
from jsonschema import Draft202012Validator, FormatChecker


ROOT = Path(__file__).resolve().parents[1]
TARGET_TOOL_FILES = {
    "student-schedule-get.schema.yaml",
    "ticket-create.schema.yaml",
    "ticket-get.schema.yaml",
    "document-request-create.schema.yaml",
    "room-availability-search.schema.yaml",
    "room-booking-create.schema.yaml",
    "handover-create.schema.yaml",
}
TRUSTED_INPUT_FIELDS = {
    "actor_id",
    "actor_user_id",
    "requester_id",
    "requester_user_id",
    "student_id",
    "student_code",
    "role",
    "roles",
    "permission",
    "permissions",
    "tenant_id",
    "queue_key",
    "conversation_id",
    "organization_id",
    "is_admin",
    "approved",
    "approval_flag",
}


class UniqueKeyLoader(yaml.SafeLoader):
    """Safe YAML loader that rejects duplicate mapping keys."""


def _construct_unique_mapping(loader: UniqueKeyLoader, node: yaml.MappingNode, deep: bool = False) -> dict[str, Any]:
    mapping: dict[str, Any] = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if key in mapping:
            raise ValueError(f"duplicate YAML key: {key!r}")
        mapping[key] = loader.construct_object(value_node, deep=deep)
    return mapping


UniqueKeyLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
    _construct_unique_mapping,
)


def load_yaml(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return yaml.load(handle, Loader=UniqueKeyLoader)


def load_json(path: Path) -> Any:
    def reject_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f"duplicate JSON key: {key!r}")
            result[key] = value
        return result

    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle, object_pairs_hook=reject_duplicates)


def load_document(path: Path) -> Any:
    if path.suffix.lower() == ".json":
        return load_json(path)
    return load_yaml(path)


def resolve_pointer(document: Any, fragment: str) -> Any:
    if fragment in ("", "#"):
        return document
    pointer = fragment[1:] if fragment.startswith("#") else fragment
    if not pointer.startswith("/"):
        raise ValueError(f"unsupported non-JSON-pointer fragment: {fragment}")
    current = document
    for raw_part in pointer[1:].split("/"):
        part = raw_part.replace("~1", "/").replace("~0", "~")
        if isinstance(current, list):
            current = current[int(part)]
        else:
            current = current[part]
    return current


def iter_refs(value: Any) -> list[str]:
    refs: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            if key == "$ref" and isinstance(child, str):
                refs.append(child)
            else:
                refs.extend(iter_refs(child))
    elif isinstance(value, list):
        for child in value:
            refs.extend(iter_refs(child))
    return refs


def validate_refs(path: Path, document: Any, cache: dict[Path, Any]) -> int:
    count = 0
    for ref in iter_refs(document):
        if ref.startswith(("http://", "https://", "urn:")):
            continue
        file_part, separator, fragment_part = ref.partition("#")
        target_path = path if not file_part else (path.parent / file_part).resolve()
        if not target_path.is_relative_to(ROOT):
            raise ValueError(f"reference escapes repository: {path}: {ref}")
        if not target_path.is_file():
            raise FileNotFoundError(f"unresolved file reference: {path}: {ref}")
        target_document = cache.get(target_path)
        if target_document is None:
            target_document = load_document(target_path)
            cache[target_path] = target_document
        fragment = f"#{fragment_part}" if separator else ""
        resolve_pointer(target_document, fragment)
        count += 1
    return count


def validate_asyncapi(path: Path, document: dict[str, Any]) -> None:
    if document.get("asyncapi") != "3.0.0":
        raise ValueError("AsyncAPI version must be exactly 3.0.0")
    for key in ("info", "channels", "operations", "components"):
        if key not in document:
            raise ValueError(f"AsyncAPI missing top-level {key}")
    if not document["info"].get("version"):
        raise ValueError("AsyncAPI info.version is required")
    messages = document.get("components", {}).get("messages", {})
    schemas = document.get("components", {}).get("schemas", {})
    if len(messages) != 8:
        raise ValueError(f"expected 8 canonical messages, found {len(messages)}")
    expected_names = {
        "ticket.created.v1",
        "ticket.status_changed.v1",
        "handover.queued.v1",
        "handover.status_changed.v1",
        "action.execution_completed.v1",
        "knowledge.version_published.v1",
        "knowledge.index_requested.v1",
        "notification.requested.v1",
    }
    actual_names = {message.get("name") for message in messages.values()}
    if actual_names != expected_names:
        raise ValueError(f"AsyncAPI event catalog mismatch: {sorted(actual_names)}")
    for message_key, message in messages.items():
        for field in ("name", "contentType", "correlationId", "payload", "x-event-type", "x-event-version", "x-data-classification", "x-idempotency", "x-replay"):
            if field not in message:
                raise ValueError(f"message {message_key} missing {field}")
    for operation_id, operation in document["operations"].items():
        if operation.get("action") not in {"send", "receive"}:
            raise ValueError(f"operation {operation_id} has invalid action")
        if "channel" not in operation or not operation.get("messages"):
            raise ValueError(f"operation {operation_id} needs channel and messages")
    for schema_name, schema in schemas.items():
        Draft202012Validator.check_schema(schema)


def validate_tool_registry(cache: dict[Path, Any]) -> None:
    registry_path = ROOT / "contracts" / "tools" / "tool-registry.yaml"
    registry = cache.get(registry_path)
    if registry is None:
        registry = load_yaml(registry_path)
        cache[registry_path] = registry
    referenced_files: set[str] = set()
    for tool in registry.get("tools", []):
        for ref_key, fragment in (("input_schema_ref", "/$defs/input"), ("output_schema_ref", "/$defs/output")):
            ref = tool[ref_key]
            file_name, separator, ref_fragment = ref.partition("#")
            if not separator or ref_fragment != fragment:
                raise ValueError(f"registry ref is not exact for {tool['tool_id']}: {ref}")
            referenced_files.add(file_name)
            target = (registry_path.parent / file_name).resolve()
            schema = cache.get(target)
            if schema is None:
                schema = load_yaml(target)
                cache[target] = schema
            resolve_pointer(schema, f"#{ref_fragment}")
    if referenced_files != TARGET_TOOL_FILES:
        raise ValueError(f"registry tool schema set mismatch: {sorted(referenced_files)}")


def validate_tool_schemas(cache: dict[Path, Any]) -> None:
    tools_dir = ROOT / "contracts" / "tools"
    for file_name in sorted(TARGET_TOOL_FILES):
        path = tools_dir / file_name
        schema = cache.get(path)
        if schema is None:
            schema = load_yaml(path)
            cache[path] = schema
        Draft202012Validator.check_schema(schema)
        input_schema = resolve_pointer(schema, "#/$defs/input")
        output_schema = resolve_pointer(schema, "#/$defs/output")
        if input_schema.get("additionalProperties") is not False:
            raise ValueError(f"{file_name} input must set additionalProperties=false")
        forbidden = TRUSTED_INPUT_FIELDS.intersection(input_schema.get("properties", {}))
        if forbidden:
            raise ValueError(f"{file_name} accepts trusted model fields: {sorted(forbidden)}")
        if output_schema.get("additionalProperties") is not False:
            raise ValueError(f"{file_name} output must set additionalProperties=false")
        if set(output_schema.get("required", [])) != {"status", "result", "error"}:
            raise ValueError(f"{file_name} output envelope must require status/result/error")


def validate_gates() -> None:
    path = ROOT / "evals" / "gates" / "regression-gates.yaml"
    gates = load_yaml(path)
    expected = {
        "EVAL-METRIC-001": (">=", 0.70),
        "EVAL-METRIC-002": (">=", 0.90),
        "EVAL-METRIC-003": (">=", 0.95),
        "EVAL-METRIC-004": (">=", 0.95),
        "EVAL-METRIC-005": (">=", 0.90),
        "EVAL-METRIC-006": (">=", 0.98),
        "EVAL-METRIC-007": (">=", 0.90),
        "EVAL-METRIC-008": (">=", 0.90),
        "EVAL-METRIC-009": (">=", 0.98),
        "EVAL-METRIC-014": (">=", 0.95),
        "EVAL-METRIC-015-FIRST": (">=", 0.98),
        "EVAL-METRIC-015-AFTER-REPAIR": ("==", 1.00),
    }
    for metric_id, (operator, value) in expected.items():
        actual = gates["thresholds"][metric_id]
        if actual["operator"] != operator or actual["value"] != value:
            raise ValueError(f"gate drift for {metric_id}: {actual}")
    if set(gates["hard_zero_metrics"]) < {
        "EVAL-METRIC-010",
        "EVAL-METRIC-011",
        "EVAL-METRIC-012",
        "EVAL-METRIC-013",
    }:
        raise ValueError("one or more authoritative hard-zero metrics are missing")
    if gates["baseline_regression"]["aggregate_max_drop"] != 0.02:
        raise ValueError("aggregate baseline regression must be 0.02")
    if gates["baseline_regression"]["subgroup_max_drop"] != 0.03:
        raise ValueError("subgroup baseline regression must be 0.03")


def validate_jsonl(case_schema: dict[str, Any]) -> tuple[int, Counter[str], Counter[str]]:
    validator = Draft202012Validator(case_schema, format_checker=FormatChecker())
    case_ids: set[str] = set()
    suites: Counter[str] = Counter()
    severities: Counter[str] = Counter()
    total = 0
    for path in sorted((ROOT / "evals" / "datasets").glob("*.jsonl")):
        with path.open("r", encoding="utf-8") as handle:
            for line_number, raw_line in enumerate(handle, start=1):
                if not raw_line.strip():
                    continue
                try:
                    case = json.loads(raw_line, object_pairs_hook=_json_unique_pairs)
                except Exception as exc:
                    raise ValueError(f"{path}:{line_number}: invalid JSON: {exc}") from exc
                errors = sorted(validator.iter_errors(case), key=lambda error: list(error.absolute_path))
                if errors:
                    detail = "; ".join(
                        f"/{'/'.join(map(str, error.absolute_path))}: {error.message}" for error in errors
                    )
                    raise ValueError(f"{path}:{line_number}: schema errors: {detail}")
                case_id = case["case_id"]
                if case_id in case_ids:
                    raise ValueError(f"duplicate case_id: {case_id}")
                case_ids.add(case_id)
                suites[case["suite"]] += 1
                severities[case["severity"]] += 1
                total += 1
    return total, suites, severities


def _json_unique_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key!r}")
        result[key] = value
    return result


def main() -> int:
    yaml_paths = sorted(
        list((ROOT / "contracts" / "asyncapi").rglob("*.yaml"))
        + list((ROOT / "contracts" / "tools").glob("*.yaml"))
        + list((ROOT / "evals").rglob("*.yaml"))
        + [ROOT / "contracts" / "openapi" / "v1" / "openapi.yaml"]
    )
    cache: dict[Path, Any] = {}
    for path in yaml_paths:
        cache[path.resolve()] = load_yaml(path)

    json_schema_paths = sorted((ROOT / "contracts" / "json-schema").rglob("*.json"))
    for path in json_schema_paths:
        cache[path.resolve()] = load_json(path)

    schema_paths = sorted(
        list((ROOT / "evals" / "schemas").glob("*.schema.yaml"))
        + list((ROOT / "contracts" / "tools").glob("*.schema.yaml"))
        + json_schema_paths
    )
    for path in schema_paths:
        Draft202012Validator.check_schema(cache[path.resolve()])

    ref_count = 0
    for path, document in list(cache.items()):
        ref_count += validate_refs(path, document, cache)

    asyncapi_path = (ROOT / "contracts" / "asyncapi" / "v1" / "asyncapi.yaml").resolve()
    validate_asyncapi(asyncapi_path, cache[asyncapi_path])
    validate_tool_registry(cache)
    validate_tool_schemas(cache)
    validate_gates()

    case_schema = cache[(ROOT / "evals" / "schemas" / "eval-case.schema.yaml").resolve()]
    case_total, suites, severities = validate_jsonl(case_schema)

    red_catalog = cache[(ROOT / "evals" / "red-team" / "catalog.yaml").resolve()]
    red_ids = [scenario["id"] for scenario in red_catalog["scenarios"]]
    if len(red_ids) != 36 or len(set(red_ids)) != 36:
        raise ValueError("red-team catalog must contain 36 unique canonical scenarios")
    if red_ids != [f"EVAL-RED-{index:03d}" for index in range(1, 37)]:
        raise ValueError("red-team scenario IDs must be contiguous EVAL-RED-001..036")

    target_files = (
        list((ROOT / "contracts" / "asyncapi").rglob("*"))
        + [ROOT / "contracts" / "tools" / name for name in TARGET_TOOL_FILES]
        + list((ROOT / "evals").rglob("*"))
    )
    file_count = sum(path.is_file() for path in target_files)
    print("VALIDATION_OK")
    print(f"files={file_count}")
    print(f"yaml_files={len(yaml_paths)}")
    print(f"schema_files={len(schema_paths)}")
    print(f"resolved_refs={ref_count}")
    print(f"jsonl_cases={case_total}")
    print("suites=" + json.dumps(dict(sorted(suites.items())), ensure_ascii=False, sort_keys=True))
    print("severities=" + json.dumps(dict(sorted(severities.items())), ensure_ascii=False, sort_keys=True))
    print(f"red_team_scenarios={len(red_ids)}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"VALIDATION_FAILED: {exc}", file=sys.stderr)
        raise
