from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
import sys
import pytest

ROOT = Path(__file__).resolve().parents[3]
API_SRC = ROOT / "services" / "api" / "src"
if str(API_SRC) not in sys.path:
    sys.path.insert(0, str(API_SRC))

from campus247.agent.state import ToolPhase
from campus247.agent.tools.write_flow import ConfirmationBindingError, WriteToolFlowBroker
from campus247.domain.shared.values import generate_uuid7


def test_build_preview_and_interrupt() -> None:
    broker = WriteToolFlowBroker()
    actor_id = generate_uuid7()

    args = {"category": "ACADEMIC", "title": "Phúc khảo điểm thi"}
    preview = broker.build_preview(actor_id=actor_id, tool_id="TOOL-TICKET-001", arguments=args)

    assert preview.action_type == "TOOL-TICKET-001"
    assert preview.actor_user_id == actor_id

    interrupt = broker.create_confirmation_interrupt(preview)
    assert interrupt["phase"] == ToolPhase.AWAITING_CONFIRMATION
    assert interrupt["preview_id"] == preview.id
    assert interrupt["expires_at"] is not None


def test_revalidate_confirmation_success() -> None:
    broker = WriteToolFlowBroker()
    actor_id = generate_uuid7()
    args = {"category": "ACADEMIC", "title": "Phúc khảo điểm thi"}
    preview = broker.build_preview(actor_id=actor_id, tool_id="TOOL-TICKET-001", arguments=args)

    now = datetime.now(timezone.utc)
    is_valid = broker.revalidate(preview, arguments=args, at_time=now)
    assert is_valid is True


def test_revalidate_confirmation_tampered_payload_fails() -> None:
    broker = WriteToolFlowBroker()
    actor_id = generate_uuid7()
    args = {"category": "ACADEMIC", "title": "Phúc khảo"}
    preview = broker.build_preview(actor_id=actor_id, tool_id="TOOL-TICKET-001", arguments=args)

    tampered = {"category": "ACADEMIC", "title": "Hacker title"}
    now = datetime.now(timezone.utc)
    is_valid = broker.revalidate(preview, arguments=tampered, at_time=now)
    assert is_valid is False


def test_revalidate_confirmation_expired_fails() -> None:
    broker = WriteToolFlowBroker()
    actor_id = generate_uuid7()
    args = {"category": "ACADEMIC", "title": "Phúc khảo"}
    preview = broker.build_preview(actor_id=actor_id, tool_id="TOOL-TICKET-001", arguments=args)

    expired_time = datetime.now(timezone.utc) + timedelta(hours=1)
    is_valid = broker.revalidate(preview, arguments=args, at_time=expired_time)
    assert is_valid is False


def test_interrupt_binds_signed_confirmation_claims_without_raw_arguments() -> None:
    broker = WriteToolFlowBroker()
    actor_id = generate_uuid7()
    conversation_id = generate_uuid7()
    args = {"category": "ACADEMIC", "title": "Phúc khảo điểm thi"}
    preview = broker.build_preview(
        actor_id=actor_id,
        tool_id="TOOL-TICKET-001",
        arguments=args,
        conversation_id=conversation_id,
    )

    interrupt = broker.create_confirmation_interrupt(preview)

    assert interrupt["tool_id"] == "TOOL-TICKET-001"
    assert interrupt["contract_version"] == "1.0.0"
    assert interrupt["conversation_id"] == conversation_id
    assert interrupt["payload_hash"] == preview.payload_hash
    assert interrupt["idempotency_key_ref"].startswith("idem-")
    assert interrupt["confirmation_token"]
    assert args["title"] not in interrupt["confirmation_token"]
    assert interrupt["summary"]

    result = broker.resume_with_confirmation(
        preview=preview,
        confirming_actor_id=actor_id,
        arguments=args,
        confirmation_token=interrupt["confirmation_token"],
    )
    assert result.phase == ToolPhase.CONFIRMED


def test_tampered_confirmation_token_is_rejected_without_consuming_preview() -> None:
    broker = WriteToolFlowBroker()
    actor_id = generate_uuid7()
    args = {"category": "ACADEMIC", "title": "Phúc khảo"}
    preview = broker.build_preview(actor_id=actor_id, tool_id="TOOL-TICKET-001", arguments=args)
    interrupt = broker.create_confirmation_interrupt(preview)
    token = interrupt["confirmation_token"]
    tampered_token = f"{token[:-1]}{'0' if token[-1] != '0' else '1'}"

    with pytest.raises(ConfirmationBindingError) as exc_info:
        broker.resume_with_confirmation(
            preview=preview,
            confirming_actor_id=actor_id,
            arguments=args,
            confirmation_token=tampered_token,
        )

    assert "invalid" in str(exc_info.value).lower()
    assert broker.revalidate(preview, arguments=args) is True


def test_execute_write_tool_node_requires_confirmation() -> None:
    from campus247.agent.nodes.definitions import execute_write_tool_node
    from campus247.agent.state import AgentState, NormalizedTurn, ToolPhase, Terminal
    
    state = AgentState(
        request=NormalizedTurn(session_id="s", turn_id="t", user_id="u", query="q"),
        tool_phase=ToolPhase.AWAITING_CONFIRMATION
    )
    
    next_state = execute_write_tool_node(state)
    assert next_state.tool_phase == ToolPhase.FAILED
    assert next_state.terminal == Terminal.SAFE_FAILURE
    assert "UNAUTHORIZED_WRITE_ATTEMPT" in next_state.errors

def test_execute_write_tool_node_room_booking_availability() -> None:
    from campus247.agent.nodes.definitions import execute_write_tool_node
    from campus247.agent.state import AgentState, NormalizedTurn, ToolPhase, ToolFlowState
    
    from campus247.agent.state import ToolCandidate
    flow = ToolFlowState()
    candidate = ToolCandidate(tool_id="TOOL-ROOM-002", arguments={"room_id": "r-101-conflict"})
    state = AgentState(
        request=NormalizedTurn(session_id="s", turn_id="t", user_id="u", query="q"),
        tool_phase=ToolPhase.CONFIRMED,
        tool_flow=flow,
        tool_candidate=candidate
    )
    
    next_state = execute_write_tool_node(state)
    assert next_state.tool_phase == ToolPhase.FAILED
    assert "ROOM_UNAVAILABLE" in next_state.errors
    
    flow_success = ToolFlowState()
    candidate_success = ToolCandidate(tool_id="TOOL-ROOM-002", arguments={"room_id": "r-101-valid"})
    state_success = AgentState(
        request=NormalizedTurn(session_id="s", turn_id="t", user_id="u", query="q"),
        tool_phase=ToolPhase.CONFIRMED,
        tool_flow=flow_success,
        tool_candidate=candidate_success
    )
    next_state_success = execute_write_tool_node(state_success)
    assert next_state_success.tool_phase == ToolPhase.SUCCEEDED
    assert "booking_id" in next_state_success.tool_flow.result_data
    assert "receipt" in next_state_success.tool_flow.result_data
