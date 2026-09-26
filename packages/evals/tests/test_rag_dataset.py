"""Unit tests for synthetic RAG eval dataset (TASK-EVAL-RAG-001)."""

from pathlib import Path
import pytest
import yaml
from packages.evals.src.validate import validate_case, SchemaValidationError

DATASET_PATH = Path(__file__).resolve().parents[1] / "datasets" / "rag-dev.yaml"


def test_rag_dataset_exists_and_valid():
    assert DATASET_PATH.is_file(), f"Missing dataset file at {DATASET_PATH}"
    with DATASET_PATH.open("r", encoding="utf-8") as f:
        cases = yaml.safe_load(f)
    assert isinstance(cases, list)
    assert len(cases) >= 2, "Must contain at least 2 RAG evaluation cases"
    for case in cases:
        assert validate_case(case) is True
        assert case["suite"] in ("grounded_qa", "citation", "abstention")
        assert case["case_id"].startswith("EVAL-RAG-")


def test_rag_dataset_negative_case():
    with DATASET_PATH.open("r", encoding="utf-8") as f:
        cases = yaml.safe_load(f)
    corrupted = dict(cases[0])
    corrupted["expected"] = None
    with pytest.raises(SchemaValidationError):
        validate_case(corrupted)
