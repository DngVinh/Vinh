from __future__ import annotations

import asyncio
from typing import Any
from campus247.ports.llm import LlmGateway, LlmRequest, LlmResponse, LlmResponseStatus


class GatewayError(Exception):
    """Base error for LLM gateway policy failures."""
    pass


class GatewayTimeoutError(GatewayError):
    """Raised when an LLM request exceeds its configured deadline."""
    pass


class BudgetExceededError(GatewayError):
    """Raised when the cumulative cost or token budget limit is reached."""
    pass


class ProviderError(GatewayError):
    """Raised when the underlying LLM provider returns a failure or error."""
    pass


class GatewayPolicyExecutor:
    """Enforces timeout, cost budget, and error handling over an LlmGateway."""

    def __init__(
        self,
        gateway: LlmGateway,
        max_monthly_budget_usd: float = 100.0,
        estimated_cost_per_1k_tokens_usd: float = 0.002,
    ) -> None:
        self._gateway = gateway
        self._max_budget = max_monthly_budget_usd
        self._cost_per_token = estimated_cost_per_1k_tokens_usd / 1000.0
        self._cumulative_tokens = 0
        self._cumulative_cost_usd = 0.0

    @property
    def total_tokens_used(self) -> int:
        return self._cumulative_tokens

    @property
    def total_cost_usd(self) -> float:
        return self._cumulative_cost_usd

    def _check_budget(self) -> None:
        if self._cumulative_cost_usd >= self._max_budget:
            raise BudgetExceededError(
                f"Monthly LLM budget limit reached: ${self._cumulative_cost_usd:.4f} >= ${self._max_budget:.4f}"
            )

    async def execute(self, request: LlmRequest) -> LlmResponse:
        self._check_budget()

        timeout_sec = request.deadline_ms / 1000.0

        try:
            resp = await asyncio.wait_for(self._gateway.generate(request), timeout=timeout_sec)
        except asyncio.TimeoutError as err:
            raise GatewayTimeoutError(
                f"Gateway deadline exceeded after {request.deadline_ms}ms for route '{request.route_id}'"
            ) from err
        except Exception as err:
            if isinstance(err, GatewayError):
                raise
            raise ProviderError(f"Provider invocation failed: {err}") from err

        if resp.status == LlmResponseStatus.FAILED:
            raise ProviderError(f"Provider reported failure for route '{request.route_id}'")

        # Track usage
        tokens = resp.usage.total_tokens
        self._cumulative_tokens += tokens
        self._cumulative_cost_usd += tokens * self._cost_per_token

        return resp
