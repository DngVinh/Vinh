from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from pathlib import Path
import sys
import pytest

ROOT = Path(__file__).resolve().parents[3]
API_SRC = ROOT / "services" / "api" / "src"
SYNTH_SRC = ROOT / "packages" / "synthetic" / "src"
for p in [API_SRC, SYNTH_SRC]:
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from campus247.domain.actions.confirmation import (
    ConfirmationTokenService,
    ConfirmationValidationResult,
)
from campus247.application.actions.confirm import (
    ConfirmationReservationService,
    ConfirmationExecutionManager,
    ConfirmationError,
)


@pytest.fixture
def token_service():
    return ConfirmationTokenService(signing_key="unit-test-confirmation-secret-key-32b")


@pytest.fixture
def reservation_service():
    return ConfirmationReservationService()


def test_ac_01_changing_any_bound_field_invalidates_confirmation(token_service: ConfirmationTokenService) -> None:
    """AC-TASK-API-CONFFIX-001-01: Changing any bound field invalidates confirmation before side effects."""
    base_time = datetime(2026, 9, 27, 12, 0, 0, tzinfo=timezone.utc)
    expires_at = base_time + timedelta(minutes=15)
    payload = {"room_id": "r-101", "time_slot": "09:00 - 11:30"}
    payload_hash = token_service.compute_payload_hash(payload)

    token = token_service.mint_token(
        preview_id="prev-100",
        actor_id="user-stu-01",
        action_type="ROOM_BOOKING",
        payload_hash=payload_hash,
        preview_version=1,
        expires_at=expires_at,
    )

    # 1. Valid token passes with exact match
    res_valid = token_service.validate_token(
        token=token,
        expected_preview_id="prev-100",
        expected_actor_id="user-stu-01",
        expected_action_type="ROOM_BOOKING",
        expected_tool_version="1.0",
        expected_policy_version="1.0",
        expected_payload_hash=payload_hash,
        expected_version=1,
        at_time=base_time,
    )
    assert res_valid.is_valid is True

    # 2. Altered actor_id must fail
    res_actor = token_service.validate_token(
        token=token,
        expected_preview_id="prev-100",
        expected_actor_id="user-attacker-99",
        expected_action_type="ROOM_BOOKING",
        expected_tool_version="1.0",
        expected_policy_version="1.0",
        expected_payload_hash=payload_hash,
        expected_version=1,
        at_time=base_time,
    )
    assert res_actor.is_valid is False
    assert res_actor.error_code == "ACTOR_MISMATCH"

    # 3. Altered payload hash must fail
    tampered_hash = token_service.compute_payload_hash({"room_id": "r-999", "time_slot": "all-day"})
    res_payload = token_service.validate_token(
        token=token,
        expected_preview_id="prev-100",
        expected_actor_id="user-stu-01",
        expected_action_type="ROOM_BOOKING",
        expected_tool_version="1.0",
        expected_policy_version="1.0",
        expected_payload_hash=tampered_hash,
        expected_version=1,
        at_time=base_time,
    )
    assert res_payload.is_valid is False
    assert res_payload.error_code == "PAYLOAD_HASH_MISMATCH"

    # 4. Altered action_type must fail
    res_action = token_service.validate_token(
        token=token,
        expected_preview_id="prev-100",
        expected_actor_id="user-stu-01",
        expected_action_type="TICKET_CREATE",
        expected_tool_version="1.0",
        expected_policy_version="1.0",
        expected_payload_hash=payload_hash,
        expected_version=1,
        at_time=base_time,
    )
    assert res_action.is_valid is False
    assert res_action.error_code == "ACTION_TYPE_MISMATCH"

    # 5. Altered version must fail
    res_version = token_service.validate_token(
        token=token,
        expected_preview_id="prev-100",
        expected_actor_id="user-stu-01",
        expected_action_type="ROOM_BOOKING",
        expected_tool_version="1.0",
        expected_policy_version="1.0",
        expected_payload_hash=payload_hash,
        expected_version=2,
        at_time=base_time,
    )
    assert res_version.is_valid is False
    assert res_version.error_code == "VERSION_MISMATCH"

    # 6. Altered preview_id must fail
    res_pid = token_service.validate_token(
        token=token,
        expected_preview_id="prev-999",
        expected_actor_id="user-stu-01",
        expected_action_type="ROOM_BOOKING",
        expected_tool_version="1.0",
        expected_policy_version="1.0",
        expected_payload_hash=payload_hash,
        expected_version=1,
        at_time=base_time,
    )
    assert res_pid.is_valid is False
    assert res_pid.error_code == "PREVIEW_ID_MISMATCH"


def test_ac_02_exactly_one_concurrent_consumer_reserves_token(reservation_service: ConfirmationReservationService) -> None:
    """AC-TASK-API-CONFFIX-001-02: Exactly one concurrent consumer can reserve a confirmation token."""
    token = "concurrent-test-token-uuid-12345"
    preview_id = "prev-concurrent-1"
    actor_id = "user-123"

    results: list[bool] = []

    def attempt_reservation():
        return reservation_service.reserve(token=token, preview_id=preview_id, actor_id=actor_id)

    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(attempt_reservation) for _ in range(10)]
        results = [f.result() for f in futures]

    # Exactly 1 True, exactly 9 False
    assert results.count(True) == 1
    assert results.count(False) == 9
    assert reservation_service.is_reserved(token) is True


def test_ac_03_expired_replayed_malformed_confirmations_produce_no_write(
    token_service: ConfirmationTokenService,
    reservation_service: ConfirmationReservationService,
) -> None:
    """AC-TASK-API-CONFFIX-001-03: Expired, replayed, malformed, or wrong-subject confirmations produce no write."""
    base_time = datetime(2026, 9, 27, 12, 0, 0, tzinfo=timezone.utc)
    expired_time = base_time - timedelta(minutes=5)
    payload = {"action": "delete_all"}
    payload_hash = token_service.compute_payload_hash(payload)

    side_effect_count = 0

    def mock_side_effect():
        nonlocal side_effect_count
        side_effect_count += 1
        return "SUCCESS"

    manager = ConfirmationExecutionManager(
        token_service=token_service,
        reservation_service=reservation_service,
    )

    # 1. Expired token produces no write
    expired_token = token_service.mint_token(
        preview_id="prev-exp",
        actor_id="user-1",
        action_type="DANGEROUS_ACTION",
        payload_hash=payload_hash,
        preview_version=1,
        expires_at=expired_time,
    )
    with pytest.raises(ConfirmationError, match="TOKEN_EXPIRED"):
        manager.execute(
            token=expired_token,
            preview_id="prev-exp",
            actor_id="user-1",
            action_type="DANGEROUS_ACTION",
            payload_hash=payload_hash,
            version=1,
            action_fn=mock_side_effect,
            at_time=base_time,
        )
    assert side_effect_count == 0

    # 2. Malformed token produces no write
    with pytest.raises(ConfirmationError, match="FORMAT_INVALID"):
        manager.execute(
            token="not-a-valid-token-format",
            preview_id="prev-exp",
            actor_id="user-1",
            action_type="DANGEROUS_ACTION",
            payload_hash=payload_hash,
            version=1,
            action_fn=mock_side_effect,
            at_time=base_time,
        )
    assert side_effect_count == 0

    # 3. Wrong-subject produces no write
    valid_token = token_service.mint_token(
        preview_id="prev-ok",
        actor_id="victim-user",
        action_type="DANGEROUS_ACTION",
        payload_hash=payload_hash,
        preview_version=1,
        expires_at=base_time + timedelta(minutes=15),
    )
    with pytest.raises(ConfirmationError, match="ACTOR_MISMATCH"):
        manager.execute(
            token=valid_token,
            preview_id="prev-ok",
            actor_id="attacker-user",
            action_type="DANGEROUS_ACTION",
            payload_hash=payload_hash,
            version=1,
            action_fn=mock_side_effect,
            at_time=base_time,
        )
    assert side_effect_count == 0

    # 4. First execution succeeds
    res = manager.execute(
        token=valid_token,
        preview_id="prev-ok",
        actor_id="victim-user",
        action_type="DANGEROUS_ACTION",
        payload_hash=payload_hash,
        version=1,
        action_fn=mock_side_effect,
        at_time=base_time,
    )
    assert res == "SUCCESS"
    assert side_effect_count == 1

    # 5. Replay produces no second write
    with pytest.raises(ConfirmationError, match="ALREADY_RESERVED"):
        manager.execute(
            token=valid_token,
            preview_id="prev-ok",
            actor_id="victim-user",
            action_type="DANGEROUS_ACTION",
            payload_hash=payload_hash,
            version=1,
            action_fn=mock_side_effect,
            at_time=base_time,
        )
    assert side_effect_count == 1


def test_action_failure_audit_does_not_capture_exception_text(
    token_service: ConfirmationTokenService,
    reservation_service: ConfirmationReservationService,
) -> None:
    """Action failures keep sensitive exception text out of audit metadata."""
    class RecordingAuditWriter:
        def __init__(self) -> None:
            self.transitions: list[dict[str, object]] = []

        def append_transition(self, **kwargs: object) -> None:
            self.transitions.append(kwargs)

    base_time = datetime(2026, 9, 27, 12, 0, 0, tzinfo=timezone.utc)
    payload_hash = token_service.compute_payload_hash({"operation": "write"})
    token = token_service.mint_token(
        preview_id="prev-failure",
        actor_id="user-1",
        action_type="CONTROLLED_WRITE",
        payload_hash=payload_hash,
        preview_version=1,
        expires_at=base_time + timedelta(minutes=15),
    )
    audit_writer = RecordingAuditWriter()
    manager = ConfirmationExecutionManager(token_service, reservation_service, audit_writer)
    secret_exception_text = "provider-secret-and-private-detail"

    def failing_action() -> None:
        raise RuntimeError(secret_exception_text)

    with pytest.raises(RuntimeError, match=secret_exception_text):
        manager.execute(
            token=token,
            preview_id="prev-failure",
            actor_id="user-1",
            action_type="CONTROLLED_WRITE",
            payload_hash=payload_hash,
            version=1,
            action_fn=failing_action,
            at_time=base_time,
        )

    assert secret_exception_text not in str(audit_writer.transitions)
    assert audit_writer.transitions[-1]["metadata"] == {"error_code": "ACTION_FAILED"}

