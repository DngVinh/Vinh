from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any


def _parse_dt(val: Any) -> datetime | None:
    if val is None:
        return None
    if isinstance(val, datetime):
        return val if val.tzinfo else val.replace(tzinfo=timezone.utc)
    if isinstance(val, str):
        # Handle ISO strings ending in Z or offset
        cleaned = val.replace("Z", "+00:00")
        dt = datetime.fromisoformat(cleaned)
        return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
    return None


@dataclass(frozen=True)
class RetrievalFilter:
    """Metadata and effective-date filter for knowledge retrieval candidate gating."""

    status: str = "PUBLISHED"
    reference_date: datetime | None = None
    audience: str | None = None
    faculty_scope: str | None = None
    is_synthetic: bool | None = None

    def matches(self, meta: dict[str, Any]) -> bool:
        # Status gate: must be exactly PUBLISHED
        doc_status = meta.get("status")
        if doc_status != self.status:
            return False

        # Synthetic match if specified
        if self.is_synthetic is not None:
            if meta.get("is_synthetic", True) != self.is_synthetic:
                return False

        # Effective date gate
        ref = self.reference_date or datetime.now(timezone.utc)
        if ref.tzinfo is None:
            ref = ref.replace(tzinfo=timezone.utc)

        eff_from = _parse_dt(meta.get("effective_from"))
        if eff_from and eff_from > ref:
            return False

        eff_until = _parse_dt(meta.get("effective_until"))
        if eff_until and eff_until < ref:
            return False

        # Audience gate
        if self.audience:
            audiences = meta.get("audiences")
            if audiences is not None:
                if not any(a in ("ALL", self.audience) for a in audiences):
                    return False

        # Faculty scope gate
        if self.faculty_scope and self.faculty_scope != "ALL":
            scope = meta.get("faculty_scope")
            if scope and scope not in ("ALL", self.faculty_scope):
                return False

        return True
