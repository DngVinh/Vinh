import sys
from pathlib import Path
import json
import hashlib
import pytest

repo_root = str(Path(__file__).resolve().parents[2])
if repo_root not in sys.path:
    sys.path.insert(0, repo_root)

from scripts.verify_release_manifest import verify_manifest, validate_manifest_schema


@pytest.fixture
def valid_manifest_data(tmp_path):
    # Create sample evidence file
    evidence_file = tmp_path / "evidence_gate_results.json"
    evidence_content = b'{"status": "passed", "tests": 120}'
    evidence_file.write_bytes(evidence_content)
    evidence_sha = hashlib.sha256(evidence_content).hexdigest()

    manifest = {
        "schema_version": "1.0",
        "release_id": "rel-2026-09-27-01",
        "source_revision": "a1b2c3d4e5f60718293a4b5c6d7e8f9a0b1c2d3e",
        "artifact_digest": "sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        "environment": "production",
        "migration_version": "20260927_01_booking_overlap_guard",
        "rollback_plan": {
            "strategy": "reverse_migration",
            "steps": ["alembic downgrade -1", "deploy previous image digest"]
        },
        "approvals": [
            {
                "role": "Security Owner",
                "approved_by": "sec-lead@huce.edu.vn",
                "approved_at": "2026-09-27T12:00:00Z",
                "signature": "sig-sec-987654"
            },
            {
                "role": "Product Owner",
                "approved_by": "po@huce.edu.vn",
                "approved_at": "2026-09-27T12:05:00Z",
                "signature": "sig-po-123456"
            }
        ],
        "gates": [
            {
                "gate_id": "CAMPUS247-EVAL-GATES-V1",
                "status": "passed",
                "evaluated_at": "2026-09-27T11:55:00Z"
            }
        ],
        "evidence": [
            {
                "path": str(evidence_file.name),
                "sha256": evidence_sha,
                "description": "Evaluation gate test results"
            }
        ]
    }
    return manifest, tmp_path


def test_valid_manifest_passes_verification(valid_manifest_data):
    manifest, base_dir = valid_manifest_data
    is_valid, errors = verify_manifest(manifest, base_dir=base_dir)
    assert is_valid is True, f"Expected valid manifest, got errors: {errors}"
    assert len(errors) == 0


def test_missing_source_or_artifact_digest_blocks_promotion(valid_manifest_data):
    manifest, base_dir = valid_manifest_data
    del manifest["source_revision"]
    is_valid, errors = verify_manifest(manifest, base_dir=base_dir)
    assert is_valid is False
    assert any("source_revision" in err for err in errors)


def test_changed_or_tampered_evidence_invalidates_manifest(valid_manifest_data):
    manifest, base_dir = valid_manifest_data
    # Tamper with the evidence file content
    evidence_path = base_dir / manifest["evidence"][0]["path"]
    evidence_path.write_bytes(b'{"status": "tampered"}')

    is_valid, errors = verify_manifest(manifest, base_dir=base_dir)
    assert is_valid is False
    assert any("checksum mismatch" in err.lower() or "digest" in err.lower() for err in errors)


def test_missing_evidence_file_invalidates_manifest(valid_manifest_data):
    manifest, base_dir = valid_manifest_data
    evidence_path = base_dir / manifest["evidence"][0]["path"]
    evidence_path.unlink()

    is_valid, errors = verify_manifest(manifest, base_dir=base_dir)
    assert is_valid is False
    assert any("evidence file missing" in err.lower() or "not found" in err.lower() for err in errors)


def test_unapproved_or_failed_gate_invalidates_manifest(valid_manifest_data):
    manifest, base_dir = valid_manifest_data
    manifest["gates"][0]["status"] = "failed"

    is_valid, errors = verify_manifest(manifest, base_dir=base_dir)
    assert is_valid is False
    assert any("gate" in err.lower() and "failed" in err.lower() for err in errors)


def test_verifier_performs_no_side_effects_or_mutations(valid_manifest_data, tmp_path):
    manifest, base_dir = valid_manifest_data
    # Capture filesystem snapshot before
    before_files = set(base_dir.rglob("*"))
    is_valid, _ = verify_manifest(manifest, base_dir=base_dir)
    after_files = set(base_dir.rglob("*"))
    assert before_files == after_files, "Verifier must be purely read-only"
