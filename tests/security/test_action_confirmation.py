from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
import sys
import pytest

ROOT = Path(__file__).resolve().parents[2]
API_SRC = ROOT / "services" / "api" / "src"
if str(API_SRC) not in sys.path:
    sys.path.insert(0, str(API_SRC))

from campus247.application.action.idempotency import IdempotencyLedger, ReservationStatus
from campus247.domain.action.confirmation import ConfirmationTokenService
from campus247.domain.action.preview import create_action_preview
from campus247.domain.shared.values import generate_uuid7


def test_confirmation_tamper_signature_rejected():
    service = ConfirmationTokenService(signing_key="sec-test-signing-key-32-chars!!!")
    actor_id = generate_uuid7()
    preview = create_action_preview(actor_id, "docreq.create", {"doc_type": "TRANSCRIPT"})
    token = service.mint_token(preview)

    # Tamper with the token
    tampered = token[:-6] + "xxxxxx"
    res = service.validate_token(
        token=tampered,
        expected_preview_id=preview.id,
        expected_actor_id=actor_id,
        expected_payload_hash=preview.payload_hash,
    )
    assert res.is_valid is False
    assert res.error_code == "SIGNATURE_INVALID"


def test_confirmation_expired_token_rejected():
    service = ConfirmationTokenService(signing_key="sec-test-signing-key-32-chars!!!")
    actor_id = generate_uuid7()
    preview = create_action_preview(actor_id, "booking.create", {"room_id": "H1-101"}, ttl_seconds=5)
    token = service.mint_token(preview)

    # Validate in the future
    future_time = datetime.now(timezone.utc) + timedelta(seconds=15)
    res = service.validate_token(
        token=token,
        expected_preview_id=preview.id,
        expected_actor_id=actor_id,
        expected_payload_hash=preview.payload_hash,
        at_time=future_time,
    )
    assert res.is_valid is False
    assert res.error_code == "TOKEN_EXPIRED"


def test_confirmation_replay_with_idempotency_ledger():
    service = ConfirmationTokenService(signing_key="sec-test-signing-key-32-chars!!!")
    ledger = IdempotencyLedger()
    actor_id = generate_uuid7()
    preview = create_action_preview(actor_id, "ticket.create", {"title": "Issue"})
    token = service.mint_token(preview)
    idem_key = "test-replay-key-12345"

    # 1. First execution
    val_res = service.validate_token(
        token=token,
        expected_preview_id=preview.id,
        expected_actor_id=actor_id,
        expected_payload_hash=preview.payload_hash,
    )
    assert val_res.is_valid is True

    reserve_res1 = ledger.reserve(actor_id, "ticket.create", idem_key, preview.payload_hash)
    assert reserve_res1.status == ReservationStatus.ACQUIRED

    ledger.complete(actor_id, "ticket.create", idem_key, 201, '{"id": "T100"}')

    # 2. Replay attempt
    reserve_res2 = ledger.reserve(actor_id, "ticket.create", idem_key, preview.payload_hash)
    assert reserve_res2.status == ReservationStatus.REPLAY
    assert reserve_res2.record.http_status == 201
    assert reserve_res2.record.response_reference == '{"id": "T100"}'


def test_confirmation_key_reused_with_tampered_payload_rejected():
    ledger = IdempotencyLedger()
    actor_id = generate_uuid7()
    idem_key = "test-reused-key-12345"

    # Initial registration
    ledger.reserve(actor_id, "docreq.create", idem_key, "hash-original")
    ledger.complete(actor_id, "docreq.create", idem_key, 200, "ok")

    # Attacker tries to reuse key with modified payload
    reused = ledger.reserve(actor_id, "docreq.create", idem_key, "hash-modified")
    assert reused.status == ReservationStatus.CONFLICT_REUSED
    assert reused.error_code == "IDEMPOTENCY_KEY_REUSED"
