from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import json
from typing import Any

from campus247.domain.shared.values import generate_uuid7

SENSITIVE_KEY_PATTERNS = {"password", "secret", "token", "access_token", "authorization", "api_key"}


@dataclass(frozen=True)
class AuditEventRecord:
    id: str
    occurred_at: datetime
    actor_type: str
    actor_id: str | None
    action_code: str
    resource_type: str
    resource_id: str | None
    outcome: str
    reason_code: str | None = None
    correlation_id: str | None = None
    request_id: str | None = None
    metadata_safe: dict[str, Any] | None = None


def sanitize_metadata(metadata: dict[str, Any] | None) -> dict[str, Any] | None:
    if not metadata:
        return None
    sanitized: dict[str, Any] = {}
    for k, v in metadata.items():
        if any(p in k.lower() for p in SENSITIVE_KEY_PATTERNS):
            continue
        sanitized[k] = v
    return sanitized


class AuditWriter:
    def __init__(self) -> None:
        self._log: list[AuditEventRecord] = []

    def record_event(
        self,
        actor_type: str,
        actor_id: str | None,
        action_code: str,
        resource_type: str,
        resource_id: str | None,
        outcome: str,
        reason_code: str | None = None,
        correlation_id: str | None = None,
        request_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> AuditEventRecord:
        record = AuditEventRecord(
            id=generate_uuid7(),
            occurred_at=datetime.now(timezone.utc),
            actor_type=actor_type,
            actor_id=actor_id,
            action_code=action_code,
            resource_type=resource_type,
            resource_id=resource_id,
            outcome=outcome,
            reason_code=reason_code,
            correlation_id=correlation_id,
            request_id=request_id,
            metadata_safe=sanitize_metadata(metadata),
        )
        self._log.append(record)
        return record

    def get_history(self) -> list[AuditEventRecord]:
        return list(self._log)
