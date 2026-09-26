import pytest
from campus247.application.operations.budget import (
    BudgetLedger,
    BudgetExceededError,
)


def test_budget_ledger_usage_tracking_and_warning():
    # AC-01: Track usage and trigger warning at 80% threshold
    ledger = BudgetLedger(daily_budget_usd=10.0, warning_threshold_ratio=0.8)

    status1 = ledger.record_token_usage(prompt_tokens=1000, completion_tokens=500, cost_usd=5.0)
    assert status1["current_spend_usd"] == 5.0
    assert status1["warning_triggered"] is False
    assert status1["exceeded"] is False

    # Spend reaches $8.50 -> > 80% warning
    status2 = ledger.record_token_usage(prompt_tokens=1000, completion_tokens=500, cost_usd=3.5)
    assert status2["current_spend_usd"] == 8.5
    assert status2["warning_triggered"] is True
    assert status2["exceeded"] is False


def test_budget_ledger_circuit_breaker_on_breach():
    # AC-02: Failure path - Reaching budget limit raises BudgetExceededError
    ledger = BudgetLedger(daily_budget_usd=10.0)
    ledger.record_token_usage(prompt_tokens=1000, completion_tokens=500, cost_usd=9.0)

    # Next call exceeds $10.0
    with pytest.raises(BudgetExceededError, match="Daily budget quota exceeded"):
        ledger.record_token_usage(prompt_tokens=1000, completion_tokens=500, cost_usd=2.0)


def test_budget_ledger_negative_cost_rejection():
    ledger = BudgetLedger(daily_budget_usd=10.0)
    with pytest.raises(ValueError, match="cost_usd must be non-negative"):
        ledger.record_token_usage(prompt_tokens=100, completion_tokens=100, cost_usd=-1.0)
