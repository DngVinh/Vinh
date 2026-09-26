from __future__ import annotations

from pathlib import Path
import pytest
import yaml

from scripts.demo.seed import DemoSeedPacker, SeedValidationError


def test_demo_manifest_exists_and_valid() -> None:
    manifest_path = Path("scripts/demo/manifest.yaml")
    assert manifest_path.exists(), "Manifest file must exist"
    data = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    assert data["manifest_version"] == "1.0"
    assert data["environment"] == "synthetic-pilot"
    assert "scenarios" in data
    assert len(data["scenarios"]) >= 4
    assert data["synthetic_compliance"]["all_records_synthetic"] is True


def test_packer_generates_valid_synthetic_seed_pack() -> None:
    packer = DemoSeedPacker()
    pack = packer.generate_pack(seed=42)
    assert pack["manifest"]["environment"] == "synthetic-pilot"
    assert len(pack["identities"]) > 0
    assert len(pack["services"]) > 0
    assert len(pack["knowledge_items"]) > 0

    # Verify 100% synthetic markers
    for identity in pack["identities"]:
        assert identity["is_synthetic"] is True
        assert identity["email"].endswith("@synthetic.huce.edu.vn")

    for service in pack["services"]:
        assert service["is_synthetic"] is True


def test_packer_negative_rejects_non_synthetic_record() -> None:
    packer = DemoSeedPacker()
    invalid_record = {
        "id": "USR-REAL-001",
        "email": "real_student@huce.edu.vn",
        "is_synthetic": False,
    }
    with pytest.raises(SeedValidationError, match="Non-synthetic or real PII detected"):
        packer.validate_record(invalid_record)
