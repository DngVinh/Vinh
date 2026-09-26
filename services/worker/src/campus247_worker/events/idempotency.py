from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import threading


@dataclass(frozen=True)
class InboxReceipt:
    consumer_name: str
    event_id: str
    received_at: datetime
    processed_at: datetime | None
    outcome: str


class EventDuplicateGuard:
    def __init__(self) -> None:
        self._receipts: dict[tuple[str, str], InboxReceipt] = {}
        self._lock = threading.Lock()

    def should_process(self, consumer_name: str, event_id: str) -> bool:
        with self._lock:
            receipt = self._receipts.get((consumer_name, event_id))
            if receipt is None:
                return True
            return receipt.processed_at is None and receipt.outcome == "FAILED_RETRYABLE"

    def mark_processed(
        self,
        consumer_name: str,
        event_id: str,
        outcome: str = "SUCCESS",
    ) -> None:
        now = datetime.now(timezone.utc)
        record = InboxReceipt(
            consumer_name=consumer_name,
            event_id=event_id,
            received_at=now,
            processed_at=now,
            outcome=outcome,
        )
        with self._lock:
            self._receipts[(consumer_name, event_id)] = record
