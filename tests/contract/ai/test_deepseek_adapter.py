from __future__ import annotations

from pathlib import Path
import sys
import uuid
import pytest

ROOT = Path(__file__).resolve().parents[3]
API_SRC = ROOT / "services" / "api" / "src"
if str(API_SRC) not in sys.path:
    sys.path.insert(0, str(API_SRC))

from campus247.infrastructure.llm.deepseek import DeepSeekAdapter
from campus247.ports.llm import FinishReason, LlmRequest, LlmResponseStatus


def test_deepseek_adapter_disabled_by_default() -> None:
    adapter = DeepSeekAdapter(api_key="mock_key", enabled=False)
    assert adapter.is_enabled is False

    req = LlmRequest(
        request_id=str(uuid.uuid4()),
        route_id="faq",
        model_profile="default",
        system_instructions="test",
        input_items=(),
        max_output_tokens=100,
        deadline_ms=2000,
    )

    with pytest.raises(RuntimeError, match="DeepSeek adapter is disabled"):
        import asyncio
        asyncio.run(adapter.generate(req))


def test_deepseek_adapter_normalization_logic() -> None:
    adapter = DeepSeekAdapter(api_key="mock_key", enabled=True)
    mock_payload = {
        "id": "resp_12345",
        "choices": [
            {
                "message": {
                    "role": "assistant",
                    "content": "Học phí là 12 triệu",
                    "reasoning_content": "Secret thought that must be discarded",
                },
                "finish_reason": "stop",
            }
        ],
        "usage": {
            "prompt_tokens": 50,
            "completion_tokens": 25,
            "total_tokens": 75,
            "prompt_tokens_details": {"cached_tokens": 10},
        },
    }

    resp = adapter.normalize_response(mock_payload, latency_ms=150)
    assert resp.status == LlmResponseStatus.COMPLETED
    assert resp.provider_id == "deepseek"
    assert resp.output_text == "Học phí là 12 triệu"
    assert resp.finish_reason == FinishReason.STOP
    assert resp.usage.input_tokens == 50
    assert resp.usage.cached_input_tokens == 10
    assert resp.usage.output_tokens == 25
    # Reasoning content MUST NOT be exposed in output
    assert "Secret thought" not in (resp.output_text or "")


def test_deepseek_adapter_capabilities() -> None:
    adapter = DeepSeekAdapter()
    caps = adapter.capabilities("deepseek", "deepseek-chat")
    assert caps.provider_id == "deepseek"
    assert caps.supports_structured_output is True
