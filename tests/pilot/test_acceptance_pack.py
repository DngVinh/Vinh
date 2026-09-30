from __future__ import annotations

from pathlib import Path
from typing import Any
import pytest
import yaml

from scripts.demo.seed import DemoSeedPacker
from campus247.application.operations.feature_flags import FeatureFlagService, FeatureFlag
from campus247.domain.action.confirmation import ConfirmationTokenService


@pytest.fixture
def pilot_manifest() -> dict[str, Any]:
    manifest_path = Path(__file__).parent / "manifest.yaml"
    assert manifest_path.exists(), "Pilot manifest must exist at tests/pilot/manifest.yaml"
    return yaml.safe_load(manifest_path.read_text(encoding="utf-8"))


def test_pilot_manifest_valid(pilot_manifest: dict[str, Any]) -> None:
    assert pilot_manifest["suite"] == "synthetic_pilot_acceptance_pack"
    assert len(pilot_manifest["journeys"]) >= 4


def test_pilot_journey_pack_execution() -> None:
    packer = DemoSeedPacker()
    pack = packer.generate_pack(seed=2026)

    # 1. Journey PILOT-JRN-01: FAQ inquiry
    assert len(pack["knowledge_items"]) >= 2
    faq_doc = pack["knowledge_items"][0]
    assert faq_doc["is_synthetic"] is True

    # 2. Journey PILOT-JRN-02: Service / Booking
    assert len(pack["services"]) >= 2
    service_doc = pack["services"][0]
    assert service_doc["is_synthetic"] is True

    # 3. Journey PILOT-JRN-03: Document request ownership & synthetic identities
    assert len(pack["identities"]) >= 1
    student = pack["identities"][0]
    assert student["role"] == "student"
    assert student["is_synthetic"] is True

    # 4. Feature flags under pilot conditions
    flags = FeatureFlagService()
    assert flags.is_enabled(FeatureFlag.DOCUMENT_SEARCH) is True
    assert flags.is_enabled(FeatureFlag.TICKET_CREATION) is True


def test_pilot_negative_unauthorized_token_rejection(pilot_manifest: dict[str, Any]) -> None:
    # Verify negative scenario declared in manifest
    negatives = [j for j in pilot_manifest["journeys"] if j.get("type") == "negative"]
    assert len(negatives) >= 1

    # Verify real ConfirmationTokenService rejects tampered token without side effect
    token_service = ConfirmationTokenService(signing_key="pilot-test-signing-key")
    result = token_service.validate_token(
        token="tampered.payload.or.token",
        expected_preview_id="prev-123",
        expected_action_type="BOOK_ROOM",
        expected_actor_id="user-456",
        expected_payload_hash="sha256-hash",
    )
    assert result.is_valid is False
    assert result.error_code in {"FORMAT_INVALID", "SIGNATURE_INVALID"}
