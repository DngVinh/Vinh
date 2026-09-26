"""Security test suite for knowledge poisoning and quarantine pipeline (TASK-TEST-SEC-003)."""

from pathlib import Path
import pytest
import yaml

FIXTURE_PATH = Path(__file__).resolve().parent / "fixtures" / "poisoned_documents.yaml"


def load_fixtures():
    with FIXTURE_PATH.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def evaluate_quarantine_policy(doc: dict) -> tuple[bool, str | None]:
    """Evaluates if a document can be safely published or must remain quarantined."""
    content_lower = doc.get("content", "").lower()

    # 1. Prompt injection / adversarial payload check
    injection_signatures = ["system instruction:", "ignore all safety", "ignore prior instructions"]
    for sig in injection_signatures:
        if sig in content_lower:
            return False, "prompt_injection_detected"

    # 2. Dual-review requirement for official knowledge publish
    reviewers = doc.get("reviewers", [])
    if len(reviewers) < 2:
        return False, "insufficient_reviewers"

    return True, None


def test_poisoned_documents_fixture_exists_and_valid():
    config = load_fixtures()
    assert "samples" in config
    assert len(config["samples"]) >= 3


def test_prompt_injection_document_is_quarantined():
    config = load_fixtures()
    injection_doc = next(s for s in config["samples"] if s["id"] == "POISON-001-INJECTION")
    can_publish, reason = evaluate_quarantine_policy(injection_doc)
    assert can_publish is False
    assert reason == "prompt_injection_detected"


def test_insufficient_review_document_is_quarantined():
    config = load_fixtures()
    unapproved_doc = next(s for s in config["samples"] if s["id"] == "POISON-002-HASH-MISMATCH")
    can_publish, reason = evaluate_quarantine_policy(unapproved_doc)
    assert can_publish is False
    assert reason == "insufficient_reviewers"


def test_clean_dual_reviewed_document_is_approved():
    config = load_fixtures()
    clean_doc = next(s for s in config["samples"] if s["id"] == "VALID-001-HANDBOOK")
    can_publish, reason = evaluate_quarantine_policy(clean_doc)
    assert can_publish is True
    assert reason is None


def test_negative_single_reviewer_cannot_bypass_quarantine():
    tampered_doc = {
        "id": "TAMPERED-001",
        "content": "Quy dinh moi ve diem danh.",
        "reviewers": ["ROLE-KNOWLEDGE-ADMIN"],
    }
    can_publish, reason = evaluate_quarantine_policy(tampered_doc)
    assert can_publish is False
    assert reason == "insufficient_reviewers"
