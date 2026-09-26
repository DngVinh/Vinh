"""Unit tests for synthetic safety and benign-control eval dataset (TASK-EVAL-SAFE-001)."""

from pathlib import Path
import pytest
import yaml
from packages.evals.src.validate import validate_case, SchemaValidationError

DATASET_PATH = Path(__file__).resolve().parents[1] / "datasets" / "safety-dev.yaml"


def test_safety_dataset_exists_and_valid():
    assert DATASET_PATH.is_file(), f"Missing dataset file at {DATASET_PATH}"
    with DATASET_PATH.open("r", encoding="utf-8") as f:
        cases = yaml.safe_load(f)
    assert isinstance(cases, list)
    assert len(cases) >= 2, "Must contain at least 2 safety evaluation cases"
    for case in cases:
        assert validate_case(case) is True
        assert case["suite"] in ("handover", "tool_safety", "privacy")
        assert case["case_id"].startswith("EVAL-SAFE-")


def test_safety_dataset_s1_dual_review():
    with DATASET_PATH.open("r", encoding="utf-8") as f:
        cases = yaml.safe_load(f)
    s1_cases = [c for c in cases if c.get("severity") == "S1"]
    assert len(s1_cases) >= 1, "Must contain at least 1 S1 critical safety case"
    for c in s1_cases:
        assert len(c["review"]["reviewers"]) >= 2, "S1 case requires at least 2 reviewers"


def test_safety_dataset_negative_case():
    with DATASET_PATH.open("r", encoding="utf-8") as f:
        cases = yaml.safe_load(f)
    corrupted = dict(cases[0])
    corrupted["severity"] = "INVALID"
    with pytest.raises(SchemaValidationError):
        validate_case(corrupted)
