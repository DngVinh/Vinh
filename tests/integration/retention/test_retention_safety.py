import sys
from pathlib import Path

# Bootstrap workers/src into path
workers_src = str(Path(__file__).resolve().parents[3] / "workers" / "src")
if workers_src not in sys.path:
    sys.path.insert(0, workers_src)

import pytest
from datetime import datetime, timezone, timedelta
from campus247_workers.retention.tombstones import TombstoneRepository, Tombstone
from campus247_workers.retention.messages import (
    RetentionRecord,
    RetentionProcessor,
    RetentionBatchResult,
)

def test_held_and_unexpired_records_are_never_removed():
    repo = TombstoneRepository()
    processor = RetentionProcessor(tombstone_repo=repo, policy_version="v1.0")

    now = datetime(2026, 9, 27, 12, 0, 0, tzinfo=timezone.utc)
    expired_time = now - timedelta(days=1)
    future_time = now + timedelta(days=30)

    records = [
        # Expired and not held -> should be purged
        RetentionRecord(
            record_id="rec-01",
            tenant_id="tenant-1",
            created_at=expired_time - timedelta(days=30),
            expires_at=expired_time,
            legal_hold=False,
            payload="expired content",
        ),
        # Expired but under legal hold -> MUST NOT be purged
        RetentionRecord(
            record_id="rec-02",
            tenant_id="tenant-1",
            created_at=expired_time - timedelta(days=30),
            expires_at=expired_time,
            legal_hold=True,
            payload="held content",
        ),
        # Not expired and not held -> MUST NOT be purged
        RetentionRecord(
            record_id="rec-03",
            tenant_id="tenant-1",
            created_at=now - timedelta(days=5),
            expires_at=future_time,
            legal_hold=False,
            payload="active content",
        ),
    ]

    result = processor.process_batch(records=records, current_time=now)

    assert result.purged_count == 1
    assert result.skipped_held_count == 1
    assert result.skipped_unexpired_count == 1
    assert records[0].status == "purged"
    assert records[0].payload is None
    assert records[1].status == "active"
    assert records[1].payload == "held content"
    assert records[2].status == "active"

    # Verify tombstone evidence created only for purged record
    assert repo.is_tombstoned("rec-01") is True
    assert repo.is_tombstoned("rec-02") is False
    assert repo.is_tombstoned("rec-03") is False


def test_idempotent_batch_retry():
    repo = TombstoneRepository()
    processor = RetentionProcessor(tombstone_repo=repo, policy_version="v1.0")

    now = datetime(2026, 9, 27, 12, 0, 0, tzinfo=timezone.utc)
    expired_time = now - timedelta(days=1)

    records = [
        RetentionRecord(
            record_id="rec-01",
            tenant_id="tenant-1",
            created_at=expired_time - timedelta(days=10),
            expires_at=expired_time,
            legal_hold=False,
            payload="some content",
        )
    ]

    # First run
    res1 = processor.process_batch(records=records, current_time=now)
    assert res1.purged_count == 1
    assert len(res1.tombstones) == 1

    # Second run (retry of already purged/tombstoned batch)
    res2 = processor.process_batch(records=records, current_time=now)
    assert res2.purged_count == 0
    assert res2.already_tombstoned_count == 1
    # Tombstone count in repository did not duplicate
    all_tombstones = repo.list_tombstones("tenant-1")
    assert len(all_tombstones) == 1


def test_resume_from_checkpoint_partial_failure():
    repo = TombstoneRepository()
    processor = RetentionProcessor(tombstone_repo=repo, policy_version="v1.0")

    now = datetime(2026, 9, 27, 12, 0, 0, tzinfo=timezone.utc)
    expired_time = now - timedelta(days=1)

    records = [
        RetentionRecord(
            record_id=f"rec-{i:02d}",
            tenant_id="tenant-1",
            created_at=expired_time - timedelta(days=10),
            expires_at=expired_time,
            legal_hold=False,
            payload=f"content {i}",
        )
        for i in range(1, 6)
    ]

    # Batch 1 processed up to rec-02 (limit=2)
    res1 = processor.process_batch(records=records, current_time=now, limit=2)
    assert res1.purged_count == 2
    assert res1.checkpoint == "rec-02"

    # Batch 2 resumes from checkpoint "rec-02"
    res2 = processor.process_batch(records=records, current_time=now, checkpoint=res1.checkpoint, limit=3)
    assert res2.purged_count == 3
    assert res2.checkpoint == "rec-05"

    # Overall 5 records purged safely, no duplicates
    assert len(repo.list_tombstones("tenant-1")) == 5


def test_outcome_reconciliation_and_tombstone_evidence():
    repo = TombstoneRepository()
    processor = RetentionProcessor(tombstone_repo=repo, policy_version="v1.2")

    now = datetime(2026, 9, 27, 12, 0, 0, tzinfo=timezone.utc)
    expired_time = now - timedelta(days=1)

    records = [
        RetentionRecord(
            record_id="rec-audit-01",
            tenant_id="tenant-x",
            created_at=expired_time - timedelta(days=5),
            expires_at=expired_time,
            legal_hold=False,
            payload="secret-sensitive-text",
        )
    ]

    res = processor.process_batch(records=records, current_time=now)
    assert res.policy_version == "v1.2"
    assert res.processed_count == 1
    assert res.purged_count == 1

    tombstone = repo.get_tombstone("rec-audit-01")
    assert tombstone is not None
    assert tombstone.retention_policy_version == "v1.2"
    assert tombstone.tenant_id == "tenant-x"
    assert tombstone.record_id == "rec-audit-01"
    # Evidence must exclude payload/secrets
    assert not hasattr(tombstone, "payload")
    assert "secret-sensitive-text" not in str(tombstone.__dict__)
    assert tombstone.checksum != ""
