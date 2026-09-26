from __future__ import annotations

from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional


def calculate_retention_cutoff(retention_days: int, reference_time: Optional[datetime] = None) -> datetime:
    if retention_days < 1:
        raise ValueError("retention_days must be at least 1.")
    ref = reference_time or datetime.now(timezone.utc)
    return ref - timedelta(days=retention_days)


def _parse_datetime(val: Any) -> Optional[datetime]:
    if val is None:
        return None
    if isinstance(val, datetime):
        return val if val.tzinfo else val.replace(tzinfo=timezone.utc)
    if isinstance(val, str):
        cleaned = val.replace("Z", "+00:00")
        dt = datetime.fromisoformat(cleaned)
        return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
    return None


def sweep_tombstones(records: List[Dict[str, Any]], cutoff: datetime) -> Dict[str, Any]:
    purged_ids: List[str] = []
    kept_records: List[Dict[str, Any]] = []

    for record in records:
        raw_deleted = record.get("deleted_at")
        deleted_at = _parse_datetime(raw_deleted)
        if deleted_at is not None and deleted_at < cutoff:
            purged_ids.append(record["id"])
        else:
            kept_records.append(record)

    return {
        "purged_count": len(purged_ids),
        "purged_ids": purged_ids,
        "retained_count": len(kept_records),
    }


class TombstoneSweeper:
    """Delegator class preserving API contract."""

    def sweep(self, records: List[Dict[str, Any]], cutoff: datetime) -> Dict[str, Any]:
        return sweep_tombstones(records=records, cutoff=cutoff)
