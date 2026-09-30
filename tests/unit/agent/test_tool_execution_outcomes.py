from __future__ import annotations

from pathlib import Path
import sys
from concurrent.futures import ThreadPoolExecutor
import threading
import pytest

ROOT = Path(__file__).resolve().parents[3]
API_SRC = ROOT / "services" / "api" / "src"
if str(API_SRC) not in sys.path:
    sys.path.insert(0, str(API_SRC))

from campus247.agent.state import ExecutionContext, ToolPhase
from campus247.agent.tools.executor import (
    BlindRetryBlockedError,
    ExecutionInProgressError,
    IdempotencyConflictError,
    ExecutionOutcomeStatus,
    IdempotentToolExecutionCoordinator,
    ToolExecutionResult,
)


class FakeExternalService:
    def __init__(self):
        self.call_count = 0
        self.should_timeout = False

    def execute(self, payload: dict) -> dict:
        self.call_count += 1
        if self.should_timeout:
            raise TimeoutError("External gateway timeout after dispatch")
        return {"booking_id": "b-123", "status": "CONFIRMED"}


@pytest.fixture
def coordinator():
    return IdempotentToolExecutionCoordinator()


def test_reserved_action_dispatches_at_most_once(coordinator):
    """AC-TASK-AGENT-EXEC-001-01: A reserved action dispatches at most once per idempotency identity."""
    service = FakeExternalService()
    idempotency_key = "idem-ticket-create-001"
    payload = {"room_id": "room-101", "hours": 2}

    # First dispatch
    res1 = coordinator.execute_idempotent(
        idempotency_key=idempotency_key,
        action_name="book_room",
        payload=payload,
        dispatch_fn=lambda: service.execute(payload),
    )
    assert res1.status == ExecutionOutcomeStatus.SUCCEEDED
    assert res1.tool_phase == ToolPhase.SUCCEEDED
    assert service.call_count == 1

    # Second dispatch with identical idempotency identity
    res2 = coordinator.execute_idempotent(
        idempotency_key=idempotency_key,
        action_name="book_room",
        payload=payload,
        dispatch_fn=lambda: service.execute(payload),
    )
    assert res2.status == ExecutionOutcomeStatus.SUCCEEDED
    # Crucial: Must NOT call the underlying external service again
    assert service.call_count == 1
    assert res1.data == res2.data


def test_timeout_after_dispatch_becomes_result_unknown_no_blind_retry(coordinator):
    """AC-TASK-AGENT-EXEC-001-02: Timeout after dispatch never becomes an inferred failure or blind retry."""
    service = FakeExternalService()
    service.should_timeout = True
    idempotency_key = "idem-timeout-002"
    payload = {"room_id": "room-102"}

    # Attempt execution which times out
    res = coordinator.execute_idempotent(
        idempotency_key=idempotency_key,
        action_name="book_room",
        payload=payload,
        dispatch_fn=lambda: service.execute(payload),
    )

    assert res.status == ExecutionOutcomeStatus.RESULT_UNKNOWN
    assert res.tool_phase == ToolPhase.UNCERTAIN
    assert "reconciliation" in res.permitted_next_action.lower()

    # Attempting immediate blind retry must be BLOCKED
    with pytest.raises(BlindRetryBlockedError):
        coordinator.execute_idempotent(
            idempotency_key=idempotency_key,
            action_name="book_room",
            payload=payload,
            dispatch_fn=lambda: service.execute(payload),
        )


def test_reconciliation_resolves_unknown_state(coordinator):
    """Unknown state is resolved deterministically before further action."""
    service = FakeExternalService()
    service.should_timeout = True
    idempotency_key = "idem-reconcile-003"
    payload = {"room_id": "room-103"}

    res = coordinator.execute_idempotent(
        idempotency_key=idempotency_key,
        action_name="book_room",
        payload=payload,
        dispatch_fn=lambda: service.execute(payload),
    )
    assert res.status == ExecutionOutcomeStatus.RESULT_UNKNOWN

    # Reconciliation verifies downstream state: say the booking actually succeeded remotely
    reconciled = coordinator.reconcile(
        idempotency_key=idempotency_key,
        resolved_status=ExecutionOutcomeStatus.SUCCEEDED,
        data={"booking_id": "b-remote-verified"},
    )
    assert reconciled.status == ExecutionOutcomeStatus.SUCCEEDED
    assert reconciled.tool_phase == ToolPhase.SUCCEEDED


def test_terminal_outcome_contains_safe_correlation_and_next_action(coordinator):
    """AC-TASK-AGENT-EXEC-001-03: Every terminal outcome contains safe correlation evidence and permitted next action."""
    service = FakeExternalService()
    idempotency_key = "idem-audit-004"
    payload = {"room_id": "room-104"}

    res = coordinator.execute_idempotent(
        idempotency_key=idempotency_key,
        action_name="book_room",
        payload=payload,
        dispatch_fn=lambda: service.execute(payload),
    )

    assert res.correlation_id is not None
    assert res.permitted_next_action is not None
    assert "token" not in res.permitted_next_action.lower()
    assert "secret" not in res.permitted_next_action.lower()


def test_same_key_with_changed_payload_is_rejected_without_dispatch(coordinator):
    service = FakeExternalService()
    key = "idem-conflict-005"

    first = coordinator.execute_idempotent(
        idempotency_key=key,
        action_name="book_room",
        payload={"room_id": "room-105"},
        dispatch_fn=lambda: service.execute({"room_id": "room-105"}),
    )

    with pytest.raises(IdempotencyConflictError):
        coordinator.execute_idempotent(
            idempotency_key=key,
            action_name="book_room",
            payload={"room_id": "room-999"},
            dispatch_fn=lambda: service.execute({"room_id": "room-999"}),
        )

    assert first.status == ExecutionOutcomeStatus.SUCCEEDED
    assert service.call_count == 1


def test_reservation_blocks_concurrent_dispatch(coordinator):
    entered = threading.Event()
    release = threading.Event()
    service = FakeExternalService()

    def slow_dispatch() -> dict:
        service.call_count += 1
        entered.set()
        release.wait(timeout=2)
        return {"status": "CONFIRMED"}

    def execute() -> object:
        return coordinator.execute_idempotent(
            idempotency_key="idem-concurrent-006",
            action_name="book_room",
            payload={"room_id": "room-106"},
            dispatch_fn=slow_dispatch,
        )

    with ThreadPoolExecutor(max_workers=2) as pool:
        first_future = pool.submit(execute)
        assert entered.wait(timeout=2)
        second_future = pool.submit(execute)
        with pytest.raises(ExecutionInProgressError):
            second_future.result(timeout=2)
        release.set()
        first = first_future.result(timeout=2)

    assert first.status == ExecutionOutcomeStatus.SUCCEEDED
    assert service.call_count == 1


def test_local_failure_is_failed_no_effect_and_redacted(coordinator):
    raw_secret = "secret-value-must-not-escape"

    def fail() -> None:
        raise RuntimeError(raw_secret)

    result = coordinator.execute_idempotent(
        idempotency_key="idem-failure-007",
        action_name="ticket_create",
        payload={"subject": "Help"},
        dispatch_fn=fail,
    )

    assert result.status == ExecutionOutcomeStatus.FAILED_NO_EFFECT
    assert raw_secret not in str(result.error)
    cached = coordinator.execute_idempotent(
        idempotency_key="idem-failure-007",
        action_name="ticket_create",
        payload={"subject": "Help"},
        dispatch_fn=fail,
    )
    assert cached.status == ExecutionOutcomeStatus.FAILED_NO_EFFECT


def test_terminal_result_can_be_projected_to_immutable_state_context(coordinator):
    result = coordinator.execute_idempotent(
        idempotency_key="idem-context-008",
        action_name="ticket_create",
        payload={"subject": "Help"},
        dispatch_fn=lambda: {"ticket_id": "safe-ref"},
    )

    context = result.to_state_context(payload_hash="hash-for-test")
    assert isinstance(context, ExecutionContext)
    assert context.correlation_id == result.correlation_id
    assert context.outcome == ExecutionOutcomeStatus.SUCCEEDED.value
