"""Security test suite for secret, PII and canary egress detection (TASK-TEST-SEC-001)."""

from pathlib import Path
import re
import pytest
import yaml

FIXTURE_PATH = Path(__file__).resolve().parent / "fixtures" / "canaries.yaml"


def load_canaries():
    with FIXTURE_PATH.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def scrub_sensitive_text(text: str, canaries_config: dict) -> str:
    scrubbed = text
    masks = canaries_config.get("sanitization_masks", {})
    for item in canaries_config.get("canary_tokens", []):
        token = item["token"]
        cat = item["category"]
        mask = masks.get(cat, "[REDACTED]")
        scrubbed = scrubbed.replace(token, mask)
    return scrubbed


def scan_for_canaries(payload: str, canaries_config: dict) -> list[str]:
    found = []
    for item in canaries_config.get("canary_tokens", []):
        if item["token"] in payload:
            found.append(item["id"])
    return found


def test_canaries_fixture_exists_and_valid():
    config = load_canaries()
    assert "canary_tokens" in config
    assert len(config["canary_tokens"]) >= 3


def test_audit_scrubber_removes_all_canaries():
    config = load_canaries()
    raw_log = "User logged in with SuperSecretPassword123! using national id 001202009999 and key C247_CANARY_PROV_SEC_9921"

    scrubbed = scrub_sensitive_text(raw_log, config)
    leaks = scan_for_canaries(scrubbed, config)
    assert len(leaks) == 0, f"Found unmasked canaries in scrubbed text: {leaks}"
    assert "[REDACTED_SECRET]" in scrubbed
    assert "[REDACTED_PII]" in scrubbed
    assert "[REDACTED_CREDENTIAL]" in scrubbed


def test_negative_canary_leak_detected():
    config = load_canaries()
    leaked_payload = "Unauthorized export of C247_CANARY_PROV_SEC_9921 occurred."

    detected = scan_for_canaries(leaked_payload, config)
    assert "CANARY-SECRET-01" in detected
