"""Offline semantic validation for the Campus 24/7 OpenAPI V1 contract.

Run from any working directory with: python contracts/tools/validate_openapi.py
The validator only reads repository files. It makes no network, provider or paid
package calls; PyYAML is the same open-source YAML parser already used by the
repository's other offline validators.
"""

from __future__ import annotations

import json
import re
import sys
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[2]
OPENAPI_PATH = ROOT / "contracts" / "openapi" / "v1" / "openapi.yaml"
REQUIREMENTS_PATH = ROOT / "docs" / "01-product" / "requirements.yaml"
SECURITY_CONTROLS_PATH = ROOT / "docs" / "06-security" / "12_SECURITY_CONTROLS.md"
TASK_ITEMS = ROOT / "tasks" / "items"
HTTP_METHODS = {"get", "put", "post", "delete", "options", "head", "patch", "trace"}
CONTRACT_ID_RE = re.compile(r"^API-[A-Z][A-Z0-9-]{1,61}$")
CONTROL_ID_RE = re.compile(r"^SEC-CTRL-[0-9]{3}$")
TASK_ID_RE = re.compile(r"^TASK-TEST-[A-Z0-9-]{1,61}$")


class UniqueKeyLoader(yaml.SafeLoader):
    """Safe YAML loader that fails on duplicate object keys."""


def _construct_unique_mapping(
    loader: UniqueKeyLoader, node: yaml.MappingNode, deep: bool = False
) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if key in result:
            raise ValueError(f"duplicate YAML key: {key!r}")
        result[key] = loader.construct_object(value_node, deep=deep)
    return result


UniqueKeyLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
    _construct_unique_mapping,
)


def load_document(path: Path) -> Any:
    try:
        if path.suffix.lower() == ".json":
            return json.loads(path.read_text(encoding="utf-8"))
        return yaml.load(path.read_text(encoding="utf-8"), Loader=UniqueKeyLoader)
    except Exception as exc:
        raise ValueError(f"cannot parse {path.relative_to(ROOT)}: {exc}") from exc


def resolve_pointer(document: Any, reference: str) -> Any:
    if reference in ("", "#"):
        return document
    pointer = reference[1:] if reference.startswith("#") else reference
    if not pointer.startswith("/"):
        raise ValueError(f"unsupported non-JSON-pointer fragment: {reference}")
    current = document
    for raw_part in pointer[1:].split("/"):
        part = raw_part.replace("~1", "/").replace("~0", "~")
        if isinstance(current, list):
            current = current[int(part)]
        elif isinstance(current, dict):
            current = current[part]
        else:
            raise ValueError(f"cannot resolve {reference} at {part!r}")
    return current


def iter_refs(value: Any) -> Iterator[str]:
    if isinstance(value, dict):
        for key, child in value.items():
            if key == "$ref" and isinstance(child, str):
                yield child
            yield from iter_refs(child)
    elif isinstance(value, list):
        for child in value:
            yield from iter_refs(child)


def validate_local_refs(entrypoint: Path, cache: dict[Path, Any]) -> int:
    """Resolve all repository-local refs reachable from the OpenAPI document."""
    pending = [entrypoint.resolve()]
    inspected: set[Path] = set()
    ref_count = 0
    while pending:
        path = pending.pop()
        if path in inspected:
            continue
        inspected.add(path)
        document = cache.get(path)
        if document is None:
            document = load_document(path)
            cache[path] = document
        for reference in iter_refs(document):
            if reference.startswith(("http://", "https://", "urn:")):
                continue
            file_part, separator, fragment = reference.partition("#")
            target = path if not file_part else (path.parent / file_part).resolve()
            try:
                target.relative_to(ROOT)
            except ValueError as exc:
                raise ValueError(
                    f"reference escapes repository: {path.relative_to(ROOT)} -> {reference}"
                ) from exc
            if not target.is_file():
                raise ValueError(
                    f"unresolved local reference: {path.relative_to(ROOT)} -> {reference}"
                )
            target_document = cache.get(target)
            if target_document is None:
                target_document = load_document(target)
                cache[target] = target_document
            resolve_pointer(target_document, f"#{fragment}" if separator else "")
            ref_count += 1
            pending.append(target)
    return ref_count


def problem_response(response: Any) -> bool:
    return isinstance(response, dict) and response.get("$ref") == "#/components/responses/Problem"


def validate_operations(
    document: dict[str, Any],
    requirement_ids: set[str],
    control_ids: set[str],
    test_task_ids: set[str],
) -> int:
    if document.get("openapi") != "3.1.2":
        raise ValueError("OpenAPI version must be exactly 3.1.2")
    if not isinstance(document.get("paths"), dict):
        raise ValueError("OpenAPI paths must be an object")

    operation_ids: set[str] = set()
    contract_ids: set[str] = set()
    count = 0
    for path_name, path_item in document["paths"].items():
        if not isinstance(path_name, str) or not path_name.startswith("/"):
            raise ValueError(f"invalid path name: {path_name!r}")
        if not isinstance(path_item, dict):
            raise ValueError(f"path item must be an object: {path_name}")
        for method, operation in path_item.items():
            if method.lower() not in HTTP_METHODS:
                continue
            count += 1
            label = f"{method.upper()} {path_name}"
            if not isinstance(operation, dict):
                raise ValueError(f"{label}: operation must be an object")
            operation_id = operation.get("operationId")
            if not isinstance(operation_id, str) or not operation_id:
                raise ValueError(f"{label}: operationId is required")
            if operation_id in operation_ids:
                raise ValueError(f"duplicate operationId: {operation_id}")
            operation_ids.add(operation_id)

            contract_id = operation.get("x-contract-id")
            if not isinstance(contract_id, str) or not CONTRACT_ID_RE.fullmatch(contract_id):
                raise ValueError(f"{label}: invalid x-contract-id")
            if contract_id in contract_ids:
                raise ValueError(f"duplicate x-contract-id: {contract_id}")
            contract_ids.add(contract_id)

            requirement_refs = operation.get("x-requirement-ids")
            if not isinstance(requirement_refs, list) or not requirement_refs or not all(
                isinstance(value, str) for value in requirement_refs
            ):
                raise ValueError(f"{label}: x-requirement-ids must be a non-empty string list")
            unknown_requirements = sorted(set(requirement_refs) - requirement_ids)
            if unknown_requirements:
                raise ValueError(f"{label}: unknown requirement IDs: {unknown_requirements}")

            control_refs = operation.get("x-control-ids")
            if not isinstance(control_refs, list) or not control_refs or not all(
                isinstance(value, str) and CONTROL_ID_RE.fullmatch(value) for value in control_refs
            ):
                raise ValueError(f"{label}: x-control-ids must contain canonical SEC-CTRL IDs")
            unknown_controls = sorted(set(control_refs) - control_ids)
            if unknown_controls:
                raise ValueError(f"{label}: unknown control IDs: {unknown_controls}")

            test_refs = operation.get("x-test-ids")
            if not isinstance(test_refs, list) or not test_refs or not all(
                isinstance(value, str) and TASK_ID_RE.fullmatch(value) for value in test_refs
            ):
                raise ValueError(f"{label}: x-test-ids must contain canonical TASK-TEST IDs")
            unknown_tests = sorted(set(test_refs) - test_task_ids)
            if unknown_tests:
                raise ValueError(f"{label}: unknown test task IDs: {unknown_tests}")

            responses = operation.get("responses")
            if not isinstance(responses, dict) or not responses:
                raise ValueError(f"{label}: responses are required")
            has_success = any(str(code).startswith("2") for code in responses)
            has_problem_policy = any(
                (str(code).startswith(("4", "5")) or str(code).lower() == "default")
                and problem_response(response)
                for code, response in responses.items()
            )
            if not has_success:
                raise ValueError(f"{label}: at least one 2xx response is required")
            if not has_problem_policy:
                raise ValueError(f"{label}: an RFC 9457 Problem error response is required")
    return count


def main() -> int:
    cache: dict[Path, Any] = {}
    openapi = load_document(OPENAPI_PATH)
    requirements = load_document(REQUIREMENTS_PATH)
    requirement_ids = {
        item["id"]
        for item in requirements.get("requirements", [])
        if isinstance(item, dict) and isinstance(item.get("id"), str)
    }
    if not requirement_ids:
        raise ValueError("requirements catalog has no requirement IDs")
    control_ids = set(
        re.findall(
            r"^\|\s*`(SEC-CTRL-[0-9]{3})`\s*\|",
            SECURITY_CONTROLS_PATH.read_text(encoding="utf-8"),
            flags=re.MULTILINE,
        )
    )
    if not control_ids:
        raise ValueError("security control catalog has no canonical SEC-CTRL IDs")
    test_task_ids = {path.stem for path in TASK_ITEMS.glob("TASK-TEST-*.yaml")}
    if not test_task_ids:
        raise ValueError("test task catalog has no TASK-TEST IDs")

    operation_count = validate_operations(openapi, requirement_ids, control_ids, test_task_ids)
    cache[OPENAPI_PATH.resolve()] = openapi
    reference_count = validate_local_refs(OPENAPI_PATH, cache)
    print("VALIDATION_OK")
    print(f"operations={operation_count}")
    print(f"requirements={len(requirement_ids)}")
    print(f"security_controls={len(control_ids)}")
    print(f"test_tasks={len(test_task_ids)}")
    print(f"resolved_local_refs={reference_count}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"VALIDATION_FAILED: {exc}", file=sys.stderr)
        raise
