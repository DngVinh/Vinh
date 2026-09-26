from __future__ import annotations

import asyncio
from pathlib import Path
import sys
import uuid
import pytest
from unittest.mock import AsyncMock, patch

ROOT = Path(__file__).resolve().parents[3]
API_SRC = ROOT / "services" / "api" / "src"
if str(API_SRC) not in sys.path:
    sys.path.insert(0, str(API_SRC))

from campus247.infrastructure.llm.fake import DeterministicFakeProvider
from campus247.infrastructure.llm.multi_provider import MultiProviderFallbackGateway
from campus247.infrastructure.llm.openai_adapter import OpenAICompatibleAdapter
from campus247.ports.llm import (
    FinishReason,
    LlmEvent,
    LlmEventType,
    LlmRequest,
    LlmResponse,
    LlmResponseStatus,
    TokenUsage,
)


@pytest.fixture
def sample_request() -> LlmRequest:
    return LlmRequest(
        request_id=str(uuid.uuid4()),
        route_id="grounded_faq",
        model_profile="default",
        system_instructions="Bạn là trợ lý AI.",
        input_items=({"role": "user", "content": "Xin chào"},),
        max_output_tokens=500,
        deadline_ms=5000,
    )


def test_openai_adapter_configuration() -> None:
    adapter = OpenAICompatibleAdapter(
        provider_id="gemini",
        base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
        api_key="test-key",
        model_name="gemini-3.6-flash",
        is_free=True,
    )
    assert adapter.provider_id == "gemini"
    assert adapter.model_name == "gemini-3.6-flash"
    assert adapter.is_free is True
    assert adapter.is_configured is True


def test_openai_adapter_unconfigured() -> None:
    adapter = OpenAICompatibleAdapter(
        provider_id="deepseek",
        base_url="https://api.deepseek.com",
        api_key="",
        model_name="deepseek-chat",
        is_free=False,
    )
    assert adapter.is_configured is False


@pytest.mark.asyncio
async def test_multi_provider_prioritizes_free_first(sample_request: LlmRequest) -> None:
    mock_free = AsyncMock()
    mock_free.is_configured = True
    mock_free.generate.return_value = LlmResponse(
        status=LlmResponseStatus.COMPLETED,
        provider_id="gemini_free",
        model_id="gemini-3.6-flash",
        output_text="Phản hồi từ Gemini Free",
    )

    mock_paid = AsyncMock()
    mock_paid.is_configured = True
    mock_paid.generate.return_value = LlmResponse(
        status=LlmResponseStatus.COMPLETED,
        provider_id="deepseek_paid",
        model_id="deepseek-chat",
        output_text="Phản hồi từ DeepSeek Paid",
    )

    gateway = MultiProviderFallbackGateway(
        providers=[
            ("deepseek_paid", mock_paid, False),
            ("gemini_free", mock_free, True),
        ]
    )

    resp = await gateway.generate(sample_request)

    # Must call free tier first and return without touching paid tier
    mock_free.generate.assert_awaited_once()
    mock_paid.generate.assert_not_awaited()
    assert resp.provider_id == "gemini_free"
    assert resp.output_text == "Phản hồi từ Gemini Free"


@pytest.mark.asyncio
async def test_multi_provider_escalates_to_paid_when_free_fails(sample_request: LlmRequest) -> None:
    mock_free = AsyncMock()
    mock_free.is_configured = True
    mock_free.generate.side_effect = RuntimeError("429 Too Many Requests: Rate limit exceeded")

    mock_paid = AsyncMock()
    mock_paid.is_configured = True
    mock_paid.generate.return_value = LlmResponse(
        status=LlmResponseStatus.COMPLETED,
        provider_id="deepseek_paid",
        model_id="deepseek-chat",
        output_text="Phản hồi từ DeepSeek sau khi Gemini bị giới hạn",
    )

    gateway = MultiProviderFallbackGateway(
        providers=[
            ("gemini_free", mock_free, True),
            ("deepseek_paid", mock_paid, False),
        ]
    )

    resp = await gateway.generate(sample_request)

    # Free was tried first, failed, then paid succeeded
    mock_free.generate.assert_awaited_once()
    mock_paid.generate.assert_awaited_once()
    assert resp.provider_id == "deepseek_paid"
    assert "DeepSeek" in resp.output_text


@pytest.mark.asyncio
async def test_multi_provider_safety_fallback_to_offline_fake(sample_request: LlmRequest) -> None:
    mock_free = AsyncMock()
    mock_free.is_configured = True
    mock_free.generate.side_effect = RuntimeError("Network down")

    mock_paid = AsyncMock()
    mock_paid.is_configured = False  # Not configured (no key)

    fake_provider = DeterministicFakeProvider.default()

    gateway = MultiProviderFallbackGateway(
        providers=[
            ("gemini_free", mock_free, True),
            ("deepseek_paid", mock_paid, False),
        ],
        fallback_gateway=fake_provider,
    )

    resp = await gateway.generate(sample_request)
    assert resp.status == LlmResponseStatus.COMPLETED
    assert resp.provider_id == "fake"
