from __future__ import annotations

from pathlib import Path
import sys
import uuid
import pytest

ROOT = Path(__file__).resolve().parents[3]
API_SRC = ROOT / "services" / "api" / "src"
if str(API_SRC) not in sys.path:
    sys.path.insert(0, str(API_SRC))

from campus247.ports.llm import (
    FinishReason,
    LlmEvent,
    LlmEventType,
    LlmGateway,
    LlmRequest,
    LlmResponse,
    LlmResponseStatus,
    ModelCapabilities,
    PrivacyClass,
    TokenUsage,
    ToolCandidate,
)


def test_llm_request_creation_and_defaults() -> None:
    req_id = str(uuid.uuid4())
    req = LlmRequest(
        request_id=req_id,
        route_id="faq",
        model_profile="default",
        system_instructions="You are HUCE assistant.",
        input_items=({"role": "user", "content": "Hello"},),
        max_output_tokens=500,
        deadline_ms=5000,
    )
    assert req.request_id == req_id
    assert req.route_id == "faq"
    assert req.privacy_class == PrivacyClass.PUBLIC
    assert req.temperature == 0.0
    assert len(req.input_items) == 1


def test_llm_request_validation_negative() -> None:
    with pytest.raises(ValueError, match="max_output_tokens must be positive"):
        LlmRequest(
            request_id=str(uuid.uuid4()),
            route_id="faq",
            model_profile="default",
            system_instructions="test",
            input_items=(),
            max_output_tokens=0,
            deadline_ms=1000,
        )

    with pytest.raises(ValueError, match="deadline_ms must be positive"):
        LlmRequest(
            request_id=str(uuid.uuid4()),
            route_id="faq",
            model_profile="default",
            system_instructions="test",
            input_items=(),
            max_output_tokens=100,
            deadline_ms=-1,
        )


def test_llm_response_and_token_usage() -> None:
    usage = TokenUsage(input_tokens=100, cached_input_tokens=20, output_tokens=50)
    candidate = ToolCandidate(call_id="call_1", name="search_faq", arguments={"query": "hoc phi"})
    resp = LlmResponse(
        status=LlmResponseStatus.COMPLETED,
        provider_id="fake",
        model_id="fake-model",
        output_text="Hoc phi la 10tr",
        tool_candidates=(candidate,),
        finish_reason=FinishReason.STOP,
        usage=usage,
        latency_ms=120,
    )
    assert resp.status == LlmResponseStatus.COMPLETED
    assert resp.output_text == "Hoc phi la 10tr"
    assert len(resp.tool_candidates) == 1
    assert resp.tool_candidates[0].name == "search_faq"
    assert resp.usage.total_tokens == 150


def test_llm_event_stream_types() -> None:
    event = LlmEvent(
        event_type=LlmEventType.TEXT_DELTA,
        delta="Xin chao",
    )
    assert event.event_type == LlmEventType.TEXT_DELTA
    assert event.delta == "Xin chao"


def test_model_capabilities() -> None:
    cap = ModelCapabilities(
        provider_id="fake",
        model_id="fake-model",
        supports_structured_output=True,
        supports_function_tools=True,
        supports_streaming=True,
        context_tokens=16384,
        max_output_tokens=2048,
    )
    assert cap.supports_streaming is True
    assert cap.context_tokens == 16384
