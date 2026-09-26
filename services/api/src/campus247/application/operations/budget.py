from typing import Any, Dict


class BudgetExceededError(Exception):
    pass


class BudgetLedger:
    def __init__(self, daily_budget_usd: float = 20.0, warning_threshold_ratio: float = 0.8):
        self.daily_budget_usd = daily_budget_usd
        self.warning_threshold_ratio = warning_threshold_ratio
        self.current_spend_usd = 0.0
        self.total_prompt_tokens = 0
        self.total_completion_tokens = 0

    def record_token_usage(self, prompt_tokens: int, completion_tokens: int, cost_usd: float) -> Dict[str, Any]:
        if cost_usd < 0:
            raise ValueError("cost_usd must be non-negative.")
        if prompt_tokens < 0 or completion_tokens < 0:
            raise ValueError("Token counts must be non-negative.")

        potential_spend = self.current_spend_usd + cost_usd
        if potential_spend > self.daily_budget_usd:
            raise BudgetExceededError(
                f"Daily budget quota exceeded: requested ${cost_usd:.2f} + current ${self.current_spend_usd:.2f} "
                f"> budget ${self.daily_budget_usd:.2f}."
            )

        self.current_spend_usd = round(potential_spend, 4)
        self.total_prompt_tokens += prompt_tokens
        self.total_completion_tokens += completion_tokens

        warning_threshold = self.daily_budget_usd * self.warning_threshold_ratio
        warning_triggered = self.current_spend_usd >= warning_threshold

        return {
            "current_spend_usd": self.current_spend_usd,
            "budget_usd": self.daily_budget_usd,
            "warning_triggered": warning_triggered,
            "exceeded": False,
            "total_tokens": self.total_prompt_tokens + self.total_completion_tokens,
        }
