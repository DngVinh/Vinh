from __future__ import annotations

import asyncio
from pathlib import Path
import sys
import uuid
import pytest

ROOT = Path(__file__).resolve().parents[3]
API_SRC = ROOT / "services" / "api" / "src"
if str(API_SRC) not in sys.path:
    sys.path.insert(0, str(API_SRC))

from campus247.application.ai.gateway import (
    BudgetExceededError,
    GatewayPolicyExecutor,
    GatewayTimeoutError,
    ProviderError,
)
from campus247.infrastructure.llm.fake import DeterministicFakeProvider
from campus247.ports.llm import LlmRequest, LlmResponseStatus


@pytest.fixture
def fake_gateway() -> DeterministicFakeProvider:
    fixture_path = ROOT / "packages" / "evals" / "fixtures" / "llm.yaml"
    return DeterministicFakeProvider.from_yaml(fixture_path)


@pytest.mark.asyncio
async def test_gateway_execute_success(fake_gateway: DeterministicFakeProvider) -> None:
    executor = GatewayPolicyExecutor(gateway=fake_gateway, max_monthly_budget_usd=100.0)
    req = LlmRequest(
        request_id=str(uuid.uuid4()),
        route_id="faq",
        model_profile="default",
        system_instructions="test",
        input_items=(),
        max_output_tokens=500,
        deadline_ms=5000,
    )
    resp = await executor.execute(req)
    assert resp.status == LlmResponseStatus.COMPLETED
    assert executor.total_tokens_used > 0


@pytest.mark.asyncio
async def test_gateway_budget_exceeded(fake_gateway: DeterministicFakeProvider) -> None:
    # Set budget to 0 USD
    executor = GatewayPolicyExecutor(gateway=fake_gateway, max_monthly_budget_usd=0.0)
    req = LlmRequest(
        request_id=str(uuid.uuid4()),
        route_id="faq",
        model_profile="default",
        system_instructions="test",
        input_items=(),
        max_output_tokens=500,
        deadline_ms=5000,
    )
    with pytest.raises(BudgetExceededError, match="Monthly LLM budget limit reached"):
        await executor.execute(req)


@pytest.mark.asyncio
async def test_gateway_timeout_enforced() -> None:
    class SlowFakeGateway(DeterministicFakeProvider):
        async def generate(self, request: LlmRequest):
            await asyncio.sleep(0.5)
            return await super().generate(request)

    fixture_path = ROOT / "packages" / "evals" / "fixtures" / "llm.yaml"
    slow_gateway = SlowFakeGateway.from_yaml(fixture_path)
    executor = GatewayPolicyExecutor(gateway=slow_gateway, max_monthly_budget_usd=100.0)

    req = LlmRequest(
        request_id=str(uuid.uuid4()),
        route_id="faq",
        model_profile="default",
        system_instructions="test",
        input_items=(),
        max_output_tokens=500,
        deadline_ms=50,  # 50ms deadline, will timeout
    )
    with pytest.raises(GatewayTimeoutError, match="Gateway deadline exceeded"):
        await executor.execute(req)
