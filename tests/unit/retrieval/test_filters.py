from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import sys
import pytest

ROOT = Path(__file__).resolve().parents[3]
API_SRC = ROOT / "services" / "api" / "src"
if str(API_SRC) not in sys.path:
    sys.path.insert(0, str(API_SRC))

from campus247.application.retrieval.filters import RetrievalFilter


def test_retrieval_filter_active_document_matches() -> None:
    now = datetime(2026, 9, 22, 12, 0, tzinfo=timezone.utc)
    rf = RetrievalFilter(reference_date=now, audience="STUDENT")

    meta = {
        "status": "PUBLISHED",
        "effective_from": "2026-09-01T00:00:00Z",
        "effective_until": "2027-08-31T23:59:59Z",
        "audiences": ["STUDENT", "STAFF"],
        "is_synthetic": True,
    }
    assert rf.matches(meta) is True


def test_retrieval_filter_expired_document_rejected() -> None:
    now = datetime(2026, 9, 22, 12, 0, tzinfo=timezone.utc)
    rf = RetrievalFilter(reference_date=now)

    meta = {
        "status": "PUBLISHED",
        "effective_from": "2025-09-01T00:00:00Z",
        "effective_until": "2026-08-31T23:59:59Z",  # Expired
        "audiences": ["STUDENT"],
    }
    assert rf.matches(meta) is False


def test_retrieval_filter_non_published_rejected() -> None:
    rf = RetrievalFilter()
    for bad_status in ["DRAFT", "SUPERSEDED", "WITHDRAWN", "ARCHIVED"]:
        assert rf.matches({"status": bad_status}) is False


def test_retrieval_filter_audience_mismatch_rejected() -> None:
    rf = RetrievalFilter(audience="STAFF")
    meta = {
        "status": "PUBLISHED",
        "audiences": ["STUDENT"],  # No STAFF
    }
    assert rf.matches(meta) is False
