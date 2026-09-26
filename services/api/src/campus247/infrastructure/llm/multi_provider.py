from __future__ import annotations

from collections.abc import AsyncIterator
import logging
from typing import Any

from campus247.ports.llm import (
    LlmEvent,
    LlmGateway,
    LlmRequest,
    LlmResponse,
    LlmResponseStatus,
    ModelCapabilities,
)

logger = logging.getLogger(__name__)


class MultiProviderFallbackGateway(LlmGateway):
    """Orchestrates multi-provider LLM execution with strict hierarchy:

    Priority 1: Free Tier APIs (Google Gemini via OpenAI endpoint).
    Priority 2: Paid Tier APIs (DeepSeek API, activated only when free tier fails or exhausts quota).
    Priority 3: Offline deterministic fake provider (safety fallback for synthetic demo/tests).
    """

    def __init__(
        self,
        providers: list[tuple[str, LlmGateway, bool]],
        fallback_gateway: LlmGateway | None = None,
    ) -> None:
        """Args:

        providers: list of (provider_name, gateway_instance, is_free_tier)
        fallback_gateway: optional safety provider when all live providers fail
        """
        # Sort so that is_free_tier == True comes first
        self._providers = sorted(providers, key=lambda p: (not p[2]))
        self._fallback_gateway = fallback_gateway

    @property
    def providers(self) -> list[tuple[str, LlmGateway, bool]]:
        return self._providers

    async def generate(self, request: LlmRequest) -> LlmResponse:
        errors: list[str] = []

        for name, provider, is_free in self._providers:
            # Check if adapter has is_configured check
            if hasattr(provider, "is_configured") and not provider.is_configured:
                continue

            try:
                tier_label = "FREE" if is_free else "PAID"
                logger.info(f"[LLM Gateway] Attempting {tier_label} provider '{name}' for request {request.request_id}...")
                resp = await provider.generate(request)
                if resp.status == LlmResponseStatus.COMPLETED:
                    return resp
                errors.append(f"{name}: response status {resp.status}")
            except Exception as e:
                err_msg = f"{name} ({'free' if is_free else 'paid'}): {type(e).__name__} - {e}"
                logger.warning(f"[LLM Gateway Fallback] Provider failed: {err_msg}. Escalating to next provider...")
                errors.append(err_msg)

        # All primary/live providers failed: fallback to offline fake if available
        if self._fallback_gateway is not None:
            logger.info("[LLM Gateway] All live providers failed or unconfigured; using deterministic fallback provider.")
            return await self._fallback_gateway.generate(request)

        raise RuntimeError(f"All LLM providers failed: {'; '.join(errors)}")

    async def stream(self, request: LlmRequest) -> AsyncIterator[LlmEvent]:
        errors: list[str] = []

        for name, provider, is_free in self._providers:
            if hasattr(provider, "is_configured") and not provider.is_configured:
                continue

            try:
                tier_label = "FREE" if is_free else "PAID"
                logger.info(f"[LLM Gateway] Streaming with {tier_label} provider '{name}'...")
                async for event in provider.stream(request):
                    yield event
                return
            except Exception as e:
                err_msg = f"{name}: {type(e).__name__} - {e}"
                logger.warning(f"[LLM Gateway Fallback] Stream failed with {err_msg}. Escalating to next provider...")
                errors.append(err_msg)

        if self._fallback_gateway is not None:
            logger.info("[LLM Gateway] Using fallback stream provider.")
            async for event in self._fallback_gateway.stream(request):
                yield event
            return

        raise RuntimeError(f"All LLM stream providers failed: {'; '.join(errors)}")

    def capabilities(self, provider_id: str, model_id: str) -> ModelCapabilities:
        for name, provider, _ in self._providers:
            if name == provider_id or getattr(provider, "provider_id", None) == provider_id:
                return provider.capabilities(provider_id, model_id)
        if self._fallback_gateway is not None:
            return self._fallback_gateway.capabilities(provider_id, model_id)
        return ModelCapabilities(
            provider_id="multi_provider",
            model_id=model_id,
            supports_structured_output=True,
            supports_function_tools=True,
            supports_streaming=True,
            supports_images=False,
            supports_stateless_requests=True,
        )
