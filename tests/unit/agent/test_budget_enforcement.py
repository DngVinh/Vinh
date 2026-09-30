from __future__ import annotations

from pathlib import Path
import sys
import pytest

ROOT = Path(__file__).resolve().parents[3]
API_SRC = ROOT / "services" / "api" / "src"
if str(API_SRC) not in sys.path:
    sys.path.insert(0, str(API_SRC))

from campus247.agent.budget import (
    BudgetExhaustedError,
    BudgetTracker,
    RunBudget,
)
from campus247.agent.state import AgentState, NormalizedTurn, Terminal


def test_no_dispatch_when_estimate_exceeds_budget():
    """AC-TASK-AGENT-BUDGET-001-01: No dispatch starts when its conservative estimate exceeds remaining budget."""
    budget = RunBudget(max_total_tokens=1000, max_provider_calls=2)
    tracker = BudgetTracker(budget=budget)

    # First call consumes 800 tokens
    tracker.check_dispatch(estimated_tokens=500, is_provider=True)
    tracker.record_provider_call(prompt_tokens=400, completion_tokens=400)
    assert tracker.consumed_tokens == 800

    # Next call estimated at 300 tokens -> 800 + 300 = 1100 > 1000: MUST be rejected before dispatch
    with pytest.raises(BudgetExhaustedError) as exc_info:
        tracker.check_dispatch(estimated_tokens=300, is_provider=True)
    assert "token" in str(exc_info.value).lower()


def test_retries_and_fallbacks_consume_parent_budget_cannot_reset():
    """AC-TASK-AGENT-BUDGET-001-02: Retries and fallbacks consume same parent budget and cannot reset counters."""
    budget = RunBudget(max_retries=2, max_provider_calls=3)
    tracker = BudgetTracker(budget=budget)

    # Initial call
    tracker.check_dispatch(estimated_tokens=100, is_provider=True)
    tracker.record_provider_call(prompt_tokens=50, completion_tokens=50)

    # First retry
    tracker.record_retry()
    assert tracker.retries == 1

    # Second retry
    tracker.record_retry()
    assert tracker.retries == 2

    # Third retry exceeds max_retries=2
    with pytest.raises(BudgetExhaustedError) as exc_info:
        tracker.record_retry()
    assert "retry" in str(exc_info.value).lower()

    # Provider calls count was not reset
    assert tracker.provider_calls == 1


def test_budget_exhaustion_yields_truthful_safe_failure_state():
    """AC-TASK-AGENT-BUDGET-001-03: Budget exhaustion yields truthful safe outcome with no fabricated completion."""
    budget = RunBudget(max_provider_calls=1)
    tracker = BudgetTracker(budget=budget)

    turn = NormalizedTurn(
        session_id="sess-budget",
        turn_id="turn-budget",
        user_id="user-1",
        query="Explain quantum computing in detail",
    )
    initial_state = AgentState(request=turn)

    # Exhaust provider call budget
    tracker.check_dispatch(estimated_tokens=100, is_provider=True)
    tracker.record_provider_call(prompt_tokens=50, completion_tokens=50)

    # Attempt another call
    with pytest.raises(BudgetExhaustedError):
        tracker.check_dispatch(estimated_tokens=100, is_provider=True)

    failed_state = tracker.to_safe_failure_state(initial_state, reason="Provider calls limit reached")
    assert failed_state.terminal == Terminal.SAFE_FAILURE
    assert failed_state.draft is None  # Never fabricate completion
    assert any("budget" in err.lower() for err in failed_state.errors)
