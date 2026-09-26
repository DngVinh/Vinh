from __future__ import annotations

from pathlib import Path
import sys
import uuid
import pytest

ROOT = Path(__file__).resolve().parents[3]
API_SRC = ROOT / "services" / "api" / "src"
if str(API_SRC) not in sys.path:
    sys.path.insert(0, str(API_SRC))

from campus247.infrastructure.llm.fake import DeterministicFakeProvider
from campus247.ports.llm import (
    FinishReason,
    LlmEventType,
    LlmRequest,
    LlmResponseStatus,
)


@pytest.fixture
def fake_provider() -> DeterministicFakeProvider:
    fixture_path = ROOT / "packages" / "evals" / "fixtures" / "llm.yaml"
    return DeterministicFakeProvider.from_yaml(fixture_path)


@pytest.mark.asyncio
async def test_fake_provider_generate_known_route(fake_provider: DeterministicFakeProvider) -> None:
    req = LlmRequest(
        request_id=str(uuid.uuid4()),
        route_id="faq",
        model_profile="default",
        system_instructions="system instructions",
        input_items=({"role": "user", "content": "Học phí?"},),
        max_output_tokens=500,
        deadline_ms=5000,
    )
    resp = await fake_provider.generate(req)
    assert resp.status == LlmResponseStatus.COMPLETED
    assert resp.output_text is not None
    assert "Học phí" in resp.output_text
    assert resp.finish_reason == FinishReason.STOP
    assert resp.usage.total_tokens > 0

    # Verify request recorded
    assert len(fake_provider.recorded_requests) == 1
    assert fake_provider.recorded_requests[0].request_id == req.request_id


@pytest.mark.asyncio
async def test_fake_provider_generate_tool_call(fake_provider: DeterministicFakeProvider) -> None:
    req = LlmRequest(
        request_id=str(uuid.uuid4()),
        route_id="tool_call",
        model_profile="default",
        system_instructions="system instructions",
        input_items=(),
        max_output_tokens=500,
        deadline_ms=5000,
    )
    resp = await fake_provider.generate(req)
    assert resp.status == LlmResponseStatus.COMPLETED
    assert resp.finish_reason == FinishReason.TOOL_CALL
    assert len(resp.tool_candidates) == 1
    assert resp.tool_candidates[0].name == "search_knowledge"


@pytest.mark.asyncio
async def test_fake_provider_streaming(fake_provider: DeterministicFakeProvider) -> None:
    req = LlmRequest(
        request_id=str(uuid.uuid4()),
        route_id="stream_test",
        model_profile="default",
        system_instructions="system instructions",
        input_items=(),
        max_output_tokens=500,
        deadline_ms=5000,
    )
    events = [event async for event in fake_provider.stream(req)]
    assert len(events) >= 4
    assert events[0].event_type == LlmEventType.RESPONSE_STARTED
    text_deltas = [e.delta for e in events if e.event_type == LlmEventType.TEXT_DELTA]
    assert len(text_deltas) == 3
    assert text_deltas[0] == "Chào bạn! "
    assert events[-1].event_type == LlmEventType.RESPONSE_COMPLETED


@pytest.mark.asyncio
async def test_fake_provider_missing_fixture_fails(fake_provider: DeterministicFakeProvider) -> None:
    req = LlmRequest(
        request_id=str(uuid.uuid4()),
        route_id="non_existent_route",
        model_profile="default",
        system_instructions="system instructions",
        input_items=(),
        max_output_tokens=500,
        deadline_ms=5000,
    )
    with pytest.raises(KeyError, match="No fake LLM fixture registered for route"):
        await fake_provider.generate(req)


def test_fake_provider_capabilities(fake_provider: DeterministicFakeProvider) -> None:
    caps = fake_provider.capabilities("fake", "fake-default")
    assert caps.provider_id == "fake"
    assert caps.supports_streaming is True
    assert caps.supports_structured_output is True
