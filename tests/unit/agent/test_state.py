from __future__ import annotations

from pathlib import Path
import sys
import pytest

ROOT = Path(__file__).resolve().parents[3]
API_SRC = ROOT / "services" / "api" / "src"
if str(API_SRC) not in sys.path:
    sys.path.insert(0, str(API_SRC))

from campus247.agent.state import (
    AgentState,
    NormalizedTurn,
    Route,
    SafetyDecision,
    SafetySeverity,
    Terminal,
    ToolPhase,
)


def test_agent_state_creation_and_defaults() -> None:
    turn = NormalizedTurn(
        session_id="sess_123",
        turn_id="turn_001",
        user_id="user_student_1",
        query="Học phí kỳ này bao nhiêu?",
    )
    state = AgentState(request=turn)

    assert state.schema_version == "1.0"
    assert state.request.query == "Học phí kỳ này bao nhiêu?"
    assert state.route is None
    assert state.safety.severity == SafetySeverity.NORMAL
    assert state.tool_phase == ToolPhase.NONE
    assert state.terminal is None
    assert len(state.errors) == 0


def test_agent_state_version_validation() -> None:
    turn = NormalizedTurn(
        session_id="sess_123",
        turn_id="turn_001",
        user_id="user_student_1",
        query="Test",
    )
    with pytest.raises(ValueError, match="Invalid state schema version"):
        AgentState(request=turn, schema_version="2.0")


def test_agent_state_route_and_terminal_enums() -> None:
    assert Route.GROUNDED_FAQ == "grounded_faq"
    assert Route.SENSITIVE_CASE == "sensitive_case"
    assert Terminal.ANSWERED == "answered"
    assert Terminal.HANDED_OVER == "handed_over"
    assert ToolPhase.AWAITING_CONFIRMATION == "awaiting_confirmation"
