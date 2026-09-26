from __future__ import annotations

from pathlib import Path
import sys
import pytest

ROOT = Path(__file__).resolve().parents[3]
API_SRC = ROOT / "services" / "api" / "src"
if str(API_SRC) not in sys.path:
    sys.path.insert(0, str(API_SRC))

from campus247.application.retrieval.rerank import RerankOutputValidator


def test_rerank_validator_valid_ranking() -> None:
    allowlist = ["chunk_1", "chunk_2", "chunk_3"]
    validator = RerankOutputValidator(allowlisted_ids=allowlist, top_k=2)

    raw_output = ["chunk_2", "chunk_1", "chunk_3"]
    validated = validator.validate_and_filter(raw_output)
    assert validated == ["chunk_2", "chunk_1"]


def test_rerank_validator_drops_hallucinated_ids() -> None:
    allowlist = ["chunk_1", "chunk_2"]
    validator = RerankOutputValidator(allowlisted_ids=allowlist, top_k=5)

    # raw_output contains hallucinated "chunk_999"
    raw_output = ["chunk_999", "chunk_2", "chunk_1"]
    validated = validator.validate_and_filter(raw_output)
    assert "chunk_999" not in validated
    assert validated == ["chunk_2", "chunk_1"]


def test_rerank_validator_fallback_on_empty_or_all_invalid() -> None:
    allowlist = ["chunk_1", "chunk_2"]
    validator = RerankOutputValidator(allowlisted_ids=allowlist, top_k=2)

    # All invalid
    raw_output = ["fake_a", "fake_b"]
    validated = validator.validate_and_filter(raw_output)
    # Must fallback to original allowlist order
    assert validated == ["chunk_1", "chunk_2"]
