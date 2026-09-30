from __future__ import annotations

from dataclasses import dataclass, field, replace
import time
from typing import Any

from campus247.agent.state import AgentState, Terminal


class BudgetExhaustedError(Exception):
    pass


@dataclass(frozen=True)
class RunBudget:
    max_total_tokens: int = 4000
    max_provider_calls: int = 5
    max_tool_calls: int = 3
    max_retries: int = 2
    max_latency_seconds: float = 30.0


class BudgetTracker:
    """Tracks token, latency, provider-call, tool-call, and retry budgets across an agent run."""

    def __init__(self, budget: RunBudget | None = None) -> None:
        self.budget = budget or RunBudget()
        self.consumed_tokens: int = 0
        self.provider_calls: int = 0
        self.tool_calls: int = 0
        self.retries: int = 0
        self.start_time: float = time.monotonic()

    def check_dispatch(
        self,
        estimated_tokens: int = 0,
        is_tool: bool = False,
        is_provider: bool = False,
    ) -> None:
        elapsed = time.monotonic() - self.start_time
        if elapsed > self.budget.max_latency_seconds:
            raise BudgetExhaustedError(f"Latency budget exhausted ({elapsed:.1f}s > {self.budget.max_latency_seconds}s)")

        if is_provider and (self.provider_calls + 1 > self.budget.max_provider_calls):
            raise BudgetExhaustedError(
                f"Provider calls budget exhausted ({self.provider_calls + 1} > {self.budget.max_provider_calls})"
            )

        if is_tool and (self.tool_calls + 1 > self.budget.max_tool_calls):
            raise BudgetExhaustedError(
                f"Tool calls budget exhausted ({self.tool_calls + 1} > {self.budget.max_tool_calls})"
            )

        # AC-TASK-AGENT-BUDGET-001-01: No dispatch starts when estimate exceeds remaining hard budget
        if self.consumed_tokens + estimated_tokens > self.budget.max_total_tokens:
            raise BudgetExhaustedError(
                f"Token budget exceeded by estimated dispatch "
                f"({self.consumed_tokens + estimated_tokens} > {self.budget.max_total_tokens})"
            )

    def record_provider_call(self, prompt_tokens: int, completion_tokens: int) -> None:
        self.consumed_tokens += prompt_tokens + completion_tokens
        self.provider_calls += 1

    def record_tool_call(self) -> None:
        self.tool_calls += 1

    def record_retry(self) -> None:
        # AC-TASK-AGENT-BUDGET-001-02: Retries consume parent budget and cannot reset counters
        if self.retries + 1 > self.budget.max_retries:
            raise BudgetExhaustedError(f"Retry budget exhausted ({self.retries + 1} > {self.budget.max_retries})")
        self.retries += 1

    def to_safe_failure_state(self, state: AgentState, reason: str) -> AgentState:
        # AC-TASK-AGENT-BUDGET-001-03: Budget exhaustion yields truthful safe outcome with no fabricated completion
        return replace(
            state,
            terminal=Terminal.SAFE_FAILURE,
            draft=None,
            errors=state.errors + (f"Budget exhausted: {reason}",),
        )
