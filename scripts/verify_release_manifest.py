import json
import hashlib
import sys
from pathlib import Path
from typing import Any
import jsonschema


def load_manifest_schema() -> dict[str, Any]:
    schema_path = Path(__file__).resolve().parents[1] / "release" / "release-manifest.schema.json"
    with open(schema_path, "r", encoding="utf-8") as f:
        return json.load(f)


def validate_manifest_schema(manifest: dict[str, Any]) -> list[str]:
    schema = load_manifest_schema()
    validator = jsonschema.Draft7Validator(schema)
    errors = []
    for err in validator.iter_errors(manifest):
        path_str = ".".join(str(p) for p in err.absolute_path) or "root"
        errors.append(f"Schema violation at {path_str}: {err.message}")
    return errors


def verify_manifest(
    manifest: dict[str, Any],
    base_dir: Path | str | None = None,
) -> tuple[bool, list[str]]:
    errors: list[str] = []

    # 1. Schema check
    schema_errors = validate_manifest_schema(manifest)
    if schema_errors:
        errors.extend(schema_errors)
        return False, errors

    # 2. Gate check (all gates must pass)
    gates = manifest.get("gates", [])
    for gate in gates:
        if gate.get("status") != "passed":
            errors.append(f"Gate {gate.get('gate_id')} has status '{gate.get('status')}', expected 'passed'")

    # 3. Evidence immutability check
    if base_dir is not None:
        base_path = Path(base_dir)
        evidence_items = manifest.get("evidence", [])
        for item in evidence_items:
            rel_path = item.get("path")
            expected_sha = item.get("sha256")
            target_file = base_path / rel_path

            if not target_file.is_file():
                errors.append(f"Evidence file missing on disk: {rel_path}")
                continue

            try:
                content = target_file.read_bytes()
                actual_sha = hashlib.sha256(content).hexdigest()
                if actual_sha.lower() != expected_sha.lower():
                    errors.append(
                        f"Checksum mismatch for evidence {rel_path}: expected {expected_sha}, got {actual_sha}"
                    )
            except Exception as ex:
                errors.append(f"Could not read evidence file {rel_path}: {ex}")

    is_valid = len(errors) == 0
    return is_valid, errors


def main(argv: list[str] | None = None) -> int:
    args = argv if argv is not None else sys.argv[1:]
    if not args:
        print("Usage: python scripts/verify_release_manifest.py <manifest_path> [base_dir]")
        return 1

    manifest_path = Path(args[0])
    base_dir = Path(args[1]) if len(args) > 1 else manifest_path.parent

    if not manifest_path.is_file():
        print(f"Error: Manifest file not found: {manifest_path}", file=sys.stderr)
        return 1

    try:
        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)
    except Exception as ex:
        print(f"Error: Failed to parse manifest JSON: {ex}", file=sys.stderr)
        return 1

    is_valid, errors = verify_manifest(manifest, base_dir=base_dir)
    if is_valid:
        print(f"Manifest verification successful: {manifest.get('release_id')}")
        return 0
    else:
        print("Manifest verification failed with errors:", file=sys.stderr)
        for err in errors:
            print(f" - {err}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
