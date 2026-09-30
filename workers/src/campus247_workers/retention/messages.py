from dataclasses import dataclass, field
from datetime import datetime, timezone
import uuid
from campus247_workers.retention.tombstones import TombstoneRepository, Tombstone


@dataclass
class RetentionRecord:
    record_id: str
    tenant_id: str
    created_at: datetime
    expires_at: datetime
    legal_hold: bool = False
    record_type: str = "conversation"
    payload: str | None = None
    status: str = "active"


@dataclass
class RetentionBatchResult:
    batch_id: str
    processed_count: int
    purged_count: int
    skipped_held_count: int
    skipped_unexpired_count: int
    already_tombstoned_count: int
    policy_version: str
    checkpoint: str | None = None
    tombstones: list[Tombstone] = field(default_factory=list)


class RetentionProcessor:
    def __init__(self, tombstone_repo: TombstoneRepository, policy_version: str = "v1.0") -> None:
        self._tombstone_repo = tombstone_repo
        self.policy_version = policy_version

    def process_batch(
        self,
        records: list[RetentionRecord],
        current_time: datetime | None = None,
        checkpoint: str | None = None,
        limit: int | None = None,
    ) -> RetentionBatchResult:
        now = current_time or datetime.now(timezone.utc)
        batch_id = f"batch-{uuid.uuid4().hex[:8]}"

        # Resolve starting point from checkpoint
        start_idx = 0
        if checkpoint is not None:
            found = False
            for idx, r in enumerate(records):
                if r.record_id == checkpoint:
                    start_idx = idx + 1
                    found = True
                    break
            if not found:
                start_idx = 0

        target_records = records[start_idx:]
        if limit is not None:
            target_records = target_records[:limit]

        processed_count = 0
        purged_count = 0
        skipped_held_count = 0
        skipped_unexpired_count = 0
        already_tombstoned_count = 0
        created_tombstones: list[Tombstone] = []
        last_checkpoint: str | None = checkpoint

        for rec in target_records:
            last_checkpoint = rec.record_id
            processed_count += 1

            # 1. AC-01: Held records are NEVER selected for removal
            if rec.legal_hold:
                skipped_held_count += 1
                continue

            # 2. AC-01: Non-expired records are NEVER selected for removal
            if rec.expires_at > now:
                skipped_unexpired_count += 1
                continue

            # 3. AC-02: Check if already purged / tombstoned (idempotency guard)
            if self._tombstone_repo.is_tombstoned(rec.record_id):
                already_tombstoned_count += 1
                rec.status = "purged"
                rec.payload = None
                continue

            # 4. Execute purge
            rec.status = "purged"
            rec.payload = None

            # 5. Record non-sensitive tombstone evidence
            tombstone = self._tombstone_repo.save_tombstone(
                record_id=rec.record_id,
                record_type=rec.record_type,
                tenant_id=rec.tenant_id,
                policy_version=self.policy_version,
                purged_at=now,
            )
            created_tombstones.append(tombstone)
            purged_count += 1

        return RetentionBatchResult(
            batch_id=batch_id,
            processed_count=processed_count,
            purged_count=purged_count,
            skipped_held_count=skipped_held_count,
            skipped_unexpired_count=skipped_unexpired_count,
            already_tombstoned_count=already_tombstoned_count,
            policy_version=self.policy_version,
            checkpoint=last_checkpoint,
            tombstones=created_tombstones,
        )
