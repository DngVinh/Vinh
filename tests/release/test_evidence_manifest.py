from __future__ import annotations

from pathlib import Path
from typing import Any
import hashlib
import json
import pytest
import yaml


def is_gate_passed(gate: dict[str, Any]) -> bool:
    """Check if a quality gate has passed cleanly."""
    return gate.get("status") == "PASSED" and gate.get("exit_code") == 0


@pytest.fixture
def release_manifest() -> dict[str, Any]:
    manifest_path = Path(__file__).resolve().parents[2] / "release" / "evidence-manifest.yaml"
    assert manifest_path.exists(), f"Release evidence manifest must exist at {manifest_path}"
    return yaml.safe_load(manifest_path.read_text(encoding="utf-8"))


def test_release_manifest_structure_and_gates(release_manifest: dict[str, Any]) -> None:
    assert release_manifest.get("release_version") == "1.0.0-rc1", "Release version mismatch"
    assert release_manifest.get("overall_status") == "PASSED", "Overall status must be PASSED"
    assert "quality_gates" in release_manifest, "quality_gates field missing"
    gates = release_manifest.get("quality_gates", [])
    assert len(gates) >= 6, f"Expected at least 6 quality gates, got {len(gates)}"

    for gate in gates:
        gate_name = gate.get("name", "UNKNOWN")
        assert is_gate_passed(gate), f"Quality gate {gate_name} did not pass: {gate}"


def test_release_manifest_integrity_checksum(release_manifest: dict[str, Any]) -> None:
    expected_hash = release_manifest.get("checksum_sha256")
    assert expected_hash is not None, "Manifest must include checksum_sha256"

    # Verify sha256 checksum calculation
    payload = {k: v for k, v in release_manifest.items() if k != "checksum_sha256"}
    computed = hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()
    assert computed == expected_hash, "Checksum sha256 must match manifest payload"


def test_negative_failing_quality_gate_blocks_release() -> None:
    tampered_manifest = {
        "release_version": "1.0.0-rc1",
        "quality_gates": [
            {"name": "unit_tests", "status": "PASSED", "exit_code": 0},
            {"name": "security_audit", "status": "FAILED", "exit_code": 1},
        ],
    }

    def evaluate_release(manifest: dict[str, Any]) -> bool:
        return all(is_gate_passed(gate) for gate in manifest.get("quality_gates", []))

    assert not evaluate_release(tampered_manifest), "Failing gate must block release evaluation"
