from __future__ import annotations

import sys
from pathlib import Path
from datetime import datetime, timezone, timedelta
import pytest

ROOT = Path(__file__).resolve().parents[3]
WORKER_SRC = ROOT / "services" / "worker" / "src"
if str(WORKER_SRC) not in sys.path:
    sys.path.insert(0, str(WORKER_SRC))

from campus247_worker.retention.tombstones import (
    TombstoneSweeper,
    calculate_retention_cutoff,
)


def test_tombstone_sweeper_purges_expired_records():
    # AC-01: Only expired tombstoned records (> 90 days) are purged
    now = datetime(2026, 9, 22, 12, 0, 0, tzinfo=timezone.utc)
    cutoff = calculate_retention_cutoff(retention_days=90, reference_time=now)

    records = [
        {"id": "rec_001", "deleted_at": now - timedelta(days=95)},  # Expired -> Purge
        {"id": "rec_002", "deleted_at": now - timedelta(days=120)}, # Expired -> Purge
        {"id": "rec_003", "deleted_at": now - timedelta(days=30)},  # Active tombstone -> Keep
        {"id": "rec_004", "deleted_at": None},                       # Active record -> Keep
    ]

    sweeper = TombstoneSweeper()
    result = sweeper.sweep(records=records, cutoff=cutoff)

    assert result["purged_count"] == 2
    assert "rec_001" in result["purged_ids"]
    assert "rec_002" in result["purged_ids"]
    assert "rec_003" not in result["purged_ids"]
    assert "rec_004" not in result["purged_ids"]


def test_tombstone_sweeper_invalid_retention_days_rejection():
    # AC-02: failure path - retention days must be at least 1
    with pytest.raises(ValueError, match="retention_days must be at least 1"):
        calculate_retention_cutoff(retention_days=0)
