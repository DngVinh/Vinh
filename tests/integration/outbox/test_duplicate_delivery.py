from __future__ import annotations

from pathlib import Path
import sys
import pytest

ROOT = Path(__file__).resolve().parents[3]
WORKER_SRC = ROOT / "services" / "worker" / "src"
API_SRC = ROOT / "services" / "api" / "src"
for p in [WORKER_SRC, API_SRC]:
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from campus247.domain.shared.values import generate_uuid7
from campus247_worker.events.idempotency import EventDuplicateGuard


def test_first_delivery_is_processed():
    guard = EventDuplicateGuard()
    consumer = "ticket_indexer"
    event_id = generate_uuid7()

    should_process = guard.should_process(consumer_name=consumer, event_id=event_id)
    assert should_process is True

    guard.mark_processed(consumer_name=consumer, event_id=event_id, outcome="SUCCESS")

    # Second delivery of same event to same consumer should be ignored
    should_process_again = guard.should_process(consumer_name=consumer, event_id=event_id)
    assert should_process_again is False


def test_different_consumer_processes_same_event():
    guard = EventDuplicateGuard()
    event_id = generate_uuid7()

    guard.mark_processed(consumer_name="consumer_a", event_id=event_id, outcome="SUCCESS")

    # consumer_b has not processed it yet
    assert guard.should_process(consumer_name="consumer_b", event_id=event_id) is True
