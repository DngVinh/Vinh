from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any
import httpx

from campus247.ports.llm import (
    FinishReason,
    LlmEvent,
    LlmEventType,
    LlmGateway,
    LlmRequest,
    LlmResponse,
    LlmResponseStatus,
    ModelCapabilities,
    TokenUsage,
    ToolCandidate,
)


class DeepSeekAdapter(LlmGateway):
    """DeepSeek API adapter behind canonical gateway; disabled by default in synthetic demo."""

    def __init__(
        self,
        base_url: str = "https://api.deepseek.com",
        api_key: str | None = None,
        enabled: bool = False,
    ) -> None:
        self._base_url = base_url
        self._api_key = api_key
        self._enabled = enabled

    @property
    def is_enabled(self) -> bool:
        return self._enabled

    def normalize_response(self, raw_data: dict[str, Any], latency_ms: int = 0) -> LlmResponse:
        choices = raw_data.get("choices", [])
        output_text = None
        finish_reason = FinishReason.STOP
        tool_candidates: list[ToolCandidate] = []

        if choices:
            choice = choices[0]
            msg = choice.get("message", {})
            output_text = msg.get("content")
            # Note: msg.get("reasoning_content") is explicitly discarded (AI-SYS-006 / AI-GW-006)

            finish_str = choice.get("finish_reason", "stop")
            if finish_str == "tool_calls":
                finish_reason = FinishReason.TOOL_CALL
                for tc in msg.get("tool_calls", []):
                    tool_candidates.append(
                        ToolCandidate(
                            call_id=tc.get("id", ""),
                            name=tc.get("function", {}).get("name", ""),
                            arguments=tc.get("function", {}).get("arguments", {}),
                        )
                    )
            elif finish_str == "length":
                finish_reason = FinishReason.LENGTH
            elif finish_str == "content_filter":
                finish_reason = FinishReason.CONTENT_FILTER
            else:
                finish_reason = FinishReason.STOP

        usage_raw = raw_data.get("usage", {})
        cached_tokens = usage_raw.get("prompt_tokens_details", {}).get("cached_tokens", 0)
        usage = TokenUsage(
            input_tokens=usage_raw.get("prompt_tokens", 0),
            cached_input_tokens=cached_tokens,
            output_tokens=usage_raw.get("completion_tokens", 0),
            reasoning_tokens=0,
        )

        return LlmResponse(
            status=LlmResponseStatus.COMPLETED,
            provider_id="deepseek",
            model_id="deepseek-chat",
            provider_request_id=raw_data.get("id"),
            output_text=output_text,
            structured_output=None,
            tool_candidates=tuple(tool_candidates),
            finish_reason=finish_reason,
            usage=usage,
            latency_ms=latency_ms,
            attempt=1,
        )

    async def generate(self, request: LlmRequest) -> LlmResponse:
        if not self._enabled:
            raise RuntimeError(
                "DeepSeek adapter is disabled in synthetic demo environment; live network calls are prohibited."
            )
        raise NotImplementedError("Live provider invocation is disabled in demo mode")

    async def stream(self, request: LlmRequest) -> AsyncIterator[LlmEvent]:
        if not self._enabled:
            raise RuntimeError(
                "DeepSeek adapter is disabled in synthetic demo environment; live network calls are prohibited."
            )
        raise NotImplementedError("Live streaming is disabled in demo mode")
        yield  # type: ignore

    def capabilities(self, provider_id: str, model_id: str) -> ModelCapabilities:
        return ModelCapabilities(
            provider_id="deepseek",
            model_id=model_id,
            supports_structured_output=True,
            supports_function_tools=True,
            supports_streaming=True,
            supports_images=False,
            supports_stateless_requests=True,
            context_tokens=65536,
            max_output_tokens=8192,
        )
