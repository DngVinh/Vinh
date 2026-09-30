from __future__ import annotations

from datetime import datetime, timezone, timedelta
from concurrent.futures import ThreadPoolExecutor
from dataclasses import FrozenInstanceError, replace
from pathlib import Path
import sys
import pytest

ROOT = Path(__file__).resolve().parents[3]
API_SRC = ROOT / "services" / "api" / "src"
if str(API_SRC) not in sys.path:
    sys.path.insert(0, str(API_SRC))

from campus247.agent.state import AgentState, ConfirmationContext, NormalizedTurn, Terminal, ToolPhase
from campus247.agent.tools.write_flow import (
    ConfirmationBindingError,
    ConfirmationBindingState,
    WriteToolFlowBroker,
)
from campus247.domain.shared.values import generate_uuid7


@pytest.fixture
def broker():
    return WriteToolFlowBroker(expiry_minutes=10)


def test_resume_executes_exact_previewed_action_for_same_actor(broker):
    """AC-TASK-AGENT-CONFIRM-002-02: Resume executes only the exact previewed action for same authorized actor."""
    actor_id = generate_uuid7()
    tool_id = "book_room"
    arguments = {"room_id": "room-101", "hours": 2, "purpose": "Seminar"}

    # Broker builds authoritative preview and interrupt
    preview = broker.build_preview(actor_id=actor_id, tool_id=tool_id, arguments=arguments)
    interrupt = broker.create_confirmation_interrupt(preview)

    assert interrupt["phase"] == ToolPhase.AWAITING_CONFIRMATION
    assert interrupt["actor_id"] == actor_id

    # Resume with exact same actor and arguments
    result = broker.resume_with_confirmation(
        preview=preview,
        confirming_actor_id=actor_id,
        arguments=arguments,
    )
    assert result.phase == ToolPhase.CONFIRMED
    assert result.is_authorized is True
    assert result.error is None


def test_tampered_arguments_rejected(broker):
    """AC-TASK-AGENT-CONFIRM-002-01: Model or attacker mutating arguments is rejected."""
    actor_id = generate_uuid7()
    tool_id = "book_room"
    arguments = {"room_id": "room-101", "hours": 2}

    preview = broker.build_preview(actor_id=actor_id, tool_id=tool_id, arguments=arguments)

    # Attacker / drift changes room_id to room-999
    tampered_arguments = {"room_id": "room-999", "hours": 2}

    with pytest.raises(ConfirmationBindingError) as exc_info:
        broker.resume_with_confirmation(
            preview=preview,
            confirming_actor_id=actor_id,
            arguments=tampered_arguments,
        )
    assert "payload" in str(exc_info.value).lower() or "drift" in str(exc_info.value).lower()


def test_wrong_actor_rejected(broker):
    """AC-TASK-AGENT-CONFIRM-002-02: Different actor attempting confirmation is rejected."""
    actor_id = generate_uuid7()
    attacker_id = generate_uuid7()
    tool_id = "cancel_ticket"
    arguments = {"ticket_id": "tick-123"}

    preview = broker.build_preview(actor_id=actor_id, tool_id=tool_id, arguments=arguments)

    with pytest.raises(ConfirmationBindingError) as exc_info:
        broker.resume_with_confirmation(
            preview=preview,
            confirming_actor_id=attacker_id,
            arguments=arguments,
        )
    assert "actor" in str(exc_info.value).lower()


def test_expired_preview_rejected(broker):
    """AC-TASK-AGENT-CONFIRM-002-03: Expired confirmation cannot be resumed."""
    actor_id = generate_uuid7()
    tool_id = "request_document"
    arguments = {"doc_type": "TRANSCRIPT"}

    preview = broker.build_preview(actor_id=actor_id, tool_id=tool_id, arguments=arguments)

    future_time = datetime.now(timezone.utc) + timedelta(minutes=15)
    with pytest.raises(ConfirmationBindingError) as exc_info:
        broker.resume_with_confirmation(
            preview=preview,
            confirming_actor_id=actor_id,
            arguments=arguments,
            at_time=future_time,
        )
    assert "expired" in str(exc_info.value).lower()


def test_replay_protection_rejects_duplicate_resume(broker):
    """Replay of an already consumed confirmation is rejected."""
    actor_id = generate_uuid7()
    tool_id = "book_room"
    arguments = {"room_id": "room-101"}

    preview = broker.build_preview(actor_id=actor_id, tool_id=tool_id, arguments=arguments)

    # First resume succeeds
    res1 = broker.resume_with_confirmation(
        preview=preview,
        confirming_actor_id=actor_id,
        arguments=arguments,
    )
    assert res1.phase == ToolPhase.CONFIRMED

    # Second resume of same preview must be rejected
    with pytest.raises(ConfirmationBindingError) as exc_info:
        broker.resume_with_confirmation(
            preview=preview,
            confirming_actor_id=actor_id,
            arguments=arguments,
        )
    assert "already consumed" in str(exc_info.value).lower() or "replay" in str(exc_info.value).lower()


def test_invalid_confirmation_transitions_to_safe_failure():
    """AC-TASK-AGENT-CONFIRM-002-03: Invalid confirmation transitions to safe failure with no side-effects."""
    turn = NormalizedTurn(
        session_id="sess-1",
        turn_id="turn-1",
        user_id="user-1",
        query="Book room",
    )
    initial_state = AgentState(
        request=turn,
        tool_phase=ToolPhase.AWAITING_CONFIRMATION,
    )

    # Transition helper in state or broker
    binding_state = ConfirmationBindingState(
        preview_id="prev-1",
        actor_id="user-1",
        tool_id="book_room",
        arguments_hash="hash-abc",
        is_consumed=False,
    )

    failed_state = binding_state.to_failed_state(initial_state, reason="Payload hash mismatch")
    assert failed_state.tool_phase == ToolPhase.FAILED
    assert failed_state.terminal == Terminal.SAFE_FAILURE
    assert "Payload hash mismatch" in failed_state.errors[0]


def test_signed_token_rejects_mutated_preview_without_consuming_original(broker):
    actor_id = generate_uuid7()
    args = {"category": "ACADEMIC", "title": "Phúc khảo"}
    preview = broker.build_preview(actor_id=actor_id, tool_id="TOOL-TICKET-001", arguments=args)
    token = broker.create_confirmation_interrupt(preview)["confirmation_token"]
    mutated = replace(preview, actor_user_id=generate_uuid7())

    with pytest.raises(ConfirmationBindingError):
        broker.resume_with_confirmation(
            preview=mutated,
            confirming_actor_id=actor_id,
            arguments=args,
            confirmation_token=token,
        )

    assert broker.revalidate(preview, arguments=args) is True


def test_context_or_policy_drift_is_rejected_before_consume(broker):
    actor_id = generate_uuid7()
    conversation_id = generate_uuid7()
    args = {"category": "ACADEMIC", "title": "Phúc khảo"}
    preview = broker.build_preview(
        actor_id=actor_id,
        tool_id="TOOL-TICKET-001",
        arguments=args,
        conversation_id=conversation_id,
    )
    token = broker.create_confirmation_interrupt(preview)["confirmation_token"]

    with pytest.raises(ConfirmationBindingError):
        broker.resume_with_confirmation(
            preview, actor_id, args, confirmation_token=token, conversation_id=generate_uuid7()
        )
    with pytest.raises(ConfirmationBindingError):
        broker.resume_with_confirmation(
            preview, actor_id, args, confirmation_token=token, policy_version="policy-old"
        )

    assert broker.revalidate(preview, arguments=args) is True


def test_concurrent_confirmation_has_one_consumer(broker):
    actor_id = generate_uuid7()
    args = {"category": "ACADEMIC", "title": "Phúc khảo"}
    preview = broker.build_preview(actor_id=actor_id, tool_id="TOOL-TICKET-001", arguments=args)
    token = broker.create_confirmation_interrupt(preview)["confirmation_token"]

    def confirm() -> str:
        try:
            broker.resume_with_confirmation(preview, actor_id, args, confirmation_token=token)
            return "confirmed"
        except ConfirmationBindingError:
            return "rejected"

    with ThreadPoolExecutor(max_workers=2) as pool:
        outcomes = list(pool.map(lambda _: confirm(), range(2)))

    assert sorted(outcomes) == ["confirmed", "rejected"]


def test_confirmation_context_is_immutable_and_complete():
    context = ConfirmationContext(
        preview_id="preview",
        tool_id="TOOL-TICKET-001",
        canonical_arguments='{"category":"ACADEMIC"}',
        payload_hash="hash",
        actor_id="actor",
        authorization_scope="write:self",
        contract_version="1.0.0",
        policy_version="policy-v1",
        expires_at="2026-09-28T12:00:00+00:00",
        risk_level="HIGH",
    )

    assert context.authorization_scope == "write:self"
    with pytest.raises(FrozenInstanceError):
        context.payload_hash = "changed"
