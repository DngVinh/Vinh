from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import threading

from campus247.domain.shared.values import generate_uuid7


@dataclass
class OutboxEventRecord:
    id: str
    event_type: str
    event_version: int
    aggregate_type: str
    aggregate_id: str
    partition_key: str
    payload: str
    occurred_at: datetime
    published_at: datetime | None = None
    publish_attempts: int = 0
    last_error_code: str | None = None
    claimed_by: str | None = None
    claimed_until: datetime | None = None


class OutboxRelay:
    def __init__(self) -> None:
        self._events: dict[str, OutboxEventRecord] = {}
        self._lock = threading.Lock()

    def enqueue(
        self,
        event_type: str,
        aggregate_type: str,
        aggregate_id: str,
        partition_key: str,
        payload: str,
        event_version: int = 1,
    ) -> OutboxEventRecord:
        record = OutboxEventRecord(
            id=generate_uuid7(),
            event_type=event_type,
            event_version=event_version,
            aggregate_type=aggregate_type,
            aggregate_id=aggregate_id,
            partition_key=partition_key,
            payload=payload,
            occurred_at=datetime.now(timezone.utc),
        )
        with self._lock:
            self._events[record.id] = record
        return record

    def claim_batch(
        self,
        batch_size: int,
        worker_id: str,
        lease_seconds: int = 30,
    ) -> list[OutboxEventRecord]:
        now = datetime.now(timezone.utc)
        claimed: list[OutboxEventRecord] = []
        with self._lock:
            for event in self._events.values():
                if event.published_at is not None:
                    continue
                if event.claimed_until is not None and event.claimed_until > now:
                    continue  # Currently claimed by another worker

                event.claimed_by = worker_id
                event.claimed_until = now + timedelta(seconds=lease_seconds)
                claimed.append(event)
                if len(claimed) >= batch_size:
                    break
        return claimed

    def mark_published(self, event_id: str) -> None:
        with self._lock:
            if event_id in self._events:
                self._events[event_id].published_at = datetime.now(timezone.utc)
                self._events[event_id].claimed_by = None
                self._events[event_id].claimed_until = None

    def record_failure(self, event_id: str, error_code: str) -> None:
        with self._lock:
            if event_id in self._events:
                self._events[event_id].publish_attempts += 1
                self._events[event_id].last_error_code = error_code
                self._events[event_id].claimed_by = None
                self._events[event_id].claimed_until = None
