from __future__ import annotations

from pathlib import Path
import sys
import tempfile
import pytest

ROOT = Path(__file__).resolve().parents[3]
API_SRC = ROOT / "services" / "api" / "src"
if str(API_SRC) not in sys.path:
    sys.path.insert(0, str(API_SRC))

from campus247.application.action.idempotency import (
    IdempotencyLedger,
    ReservationStatus,
)
from campus247.domain.shared.values import generate_uuid7


def durable_test_path() -> Path:
    return Path(tempfile.gettempdir()) / f"campus247-idempotency-test-{generate_uuid7()}.sqlite3"


def test_first_call_acquires_reservation():
    ledger = IdempotencyLedger()
    actor_id = generate_uuid7()
    key = "idem-key-test-12345"

    res = ledger.reserve(
        actor_user_id=actor_id,
        operation_id="ticket.create",
        idempotency_key=key,
        request_fingerprint="sha256:fingerprint1",
    )
    assert res.status == ReservationStatus.ACQUIRED


def test_concurrent_call_in_progress():
    ledger = IdempotencyLedger()
    actor_id = generate_uuid7()
    key = "idem-key-test-12345"

    res1 = ledger.reserve(actor_id, "ticket.create", key, "sha256:fingerprint1")
    assert res1.status == ReservationStatus.ACQUIRED

    res2 = ledger.reserve(actor_id, "ticket.create", key, "sha256:fingerprint1")
    assert res2.status == ReservationStatus.CONFLICT_IN_PROGRESS
    assert res2.error_code == "IDEMPOTENCY_IN_PROGRESS"


def test_replay_after_completion():
    ledger = IdempotencyLedger()
    actor_id = generate_uuid7()
    key = "idem-key-test-12345"

    ledger.reserve(actor_id, "ticket.create", key, "sha256:fingerprint1")
    ledger.complete(actor_id, "ticket.create", key, http_status=201, response_payload='{"ticket_id": "T1"}')

    replay = ledger.reserve(actor_id, "ticket.create", key, "sha256:fingerprint1")
    assert replay.status == ReservationStatus.REPLAY
    assert replay.record is not None
    assert replay.record.http_status == 201
    assert replay.record.response_reference == '{"ticket_id": "T1"}'


def test_reused_key_different_fingerprint_conflict():
    ledger = IdempotencyLedger()
    actor_id = generate_uuid7()
    key = "idem-key-test-12345"

    ledger.reserve(actor_id, "ticket.create", key, "sha256:fingerprint1")
    ledger.complete(actor_id, "ticket.create", key, http_status=201, response_payload='{"ticket_id": "T1"}')

    conflict = ledger.reserve(actor_id, "ticket.create", key, "sha256:DIFFERENT_fingerprint")
    assert conflict.status == ReservationStatus.CONFLICT_REUSED
    assert conflict.error_code == "IDEMPOTENCY_KEY_REUSED"


def test_completed_reservation_replays_after_new_ledger_instance():
    database_path = durable_test_path()
    actor_id = generate_uuid7()
    key = "idem-key-restart-12345"

    ledger = IdempotencyLedger(database_path=database_path)
    ledger.reserve(actor_id, "ticket.create", key, "sha256:fingerprint1")
    ledger.complete(actor_id, "ticket.create", key, 201, "ticket-reference")
    replay = IdempotencyLedger(database_path=database_path).reserve(
        actor_id, "ticket.create", key, "sha256:fingerprint1"
    )

    assert replay.status == ReservationStatus.REPLAY
    assert replay.record is not None
    assert replay.record.response_reference == "ticket-reference"
