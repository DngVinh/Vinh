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
from campus247_worker.outbox.relay import OutboxEventRecord, OutboxRelay


def test_outbox_relay_enqueue_and_claim():
    relay = OutboxRelay()
    agg_id = generate_uuid7()

    evt = relay.enqueue(
        event_type="ticket.created",
        aggregate_type="ticket",
        aggregate_id=agg_id,
        partition_key=agg_id,
        payload='{"ticket_id": "T1"}',
    )
    assert evt.id is not None
    assert evt.published_at is None

    # Worker 1 claims batch
    claimed = relay.claim_batch(batch_size=10, worker_id="worker-1")
    assert len(claimed) == 1
    assert claimed[0].id == evt.id


def test_concurrent_worker_skip_locked():
    relay = OutboxRelay()
    agg_id = generate_uuid7()
    relay.enqueue("ticket.created", "ticket", agg_id, agg_id, '{"t": 1}')

    # Worker 1 claims
    claimed_1 = relay.claim_batch(batch_size=10, worker_id="worker-1")
    assert len(claimed_1) == 1

    # Worker 2 attempts claim concurrently -> should get empty (skipped locked / claimed)
    claimed_2 = relay.claim_batch(batch_size=10, worker_id="worker-2")
    assert len(claimed_2) == 0


def test_mark_published():
    relay = OutboxRelay()
    agg_id = generate_uuid7()
    evt = relay.enqueue("ticket.created", "ticket", agg_id, agg_id, '{"t": 1}')
    claimed = relay.claim_batch(batch_size=1, worker_id="worker-1")

    relay.mark_published(claimed[0].id)

    # Claim again should return 0 since published
    claimed_after = relay.claim_batch(batch_size=10, worker_id="worker-1")
    assert len(claimed_after) == 0
