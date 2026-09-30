from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import uuid


@dataclass(frozen=True)
class Tombstone:
    tombstone_id: str
    record_id: str
    record_type: str
    tenant_id: str
    retention_policy_version: str
    purged_at: datetime
    checksum: str


class TombstoneRepository:
    def __init__(self) -> None:
        self._tombstones: dict[str, Tombstone] = {}

    def is_tombstoned(self, record_id: str) -> bool:
        return record_id in self._tombstones

    def save_tombstone(
        self,
        record_id: str,
        record_type: str,
        tenant_id: str,
        policy_version: str,
        purged_at: datetime | None = None,
    ) -> Tombstone:
        if record_id in self._tombstones:
            return self._tombstones[record_id]

        ts = purged_at or datetime.now(timezone.utc)
        # Generate non-reversible cryptographic checksum for audit reconciliation
        checksum = hashlib.sha256(f"{tenant_id}:{record_type}:{record_id}:{policy_version}".encode()).hexdigest()

        tombstone = Tombstone(
            tombstone_id=f"tomb-{uuid.uuid4().hex[:12]}",
            record_id=record_id,
            record_type=record_type,
            tenant_id=tenant_id,
            retention_policy_version=policy_version,
            purged_at=ts,
            checksum=checksum,
        )
        self._tombstones[record_id] = tombstone
        return tombstone

    def get_tombstone(self, record_id: str) -> Tombstone | None:
        return self._tombstones.get(record_id)

    def list_tombstones(self, tenant_id: str | None = None) -> list[Tombstone]:
        if tenant_id is None:
            return list(self._tombstones.values())
        return [t for t in self._tombstones.values() if t.tenant_id == tenant_id]
