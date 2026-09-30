from __future__ import annotations

from typing import Any, AsyncIterator
from campus247.infrastructure.llm.egress_policy import EgressPolicy


class EgressProviderError(Exception):
    """Provider failures without provider payloads, credentials, or stack details."""

    safe_reason = "External model provider failed without a safe result"

    def __init__(self) -> None:
        super().__init__(self.safe_reason)


class EgressGuardedLlmGateway:
    """Wraps an LLM provider adapter with deterministic egress policy enforcement."""

    def __init__(self, provider: Any, policy: EgressPolicy | None = None) -> None:
        self._provider = provider
        self._policy = policy or EgressPolicy()

    async def generate(self, payload: dict[str, Any]) -> dict[str, Any]:
        clean_payload = self._policy.validate_and_minimize(payload)
        try:
            return await self._provider.generate(clean_payload)
        except Exception:
            # Provider exceptions can echo request content; expose only a safe category.
            raise EgressProviderError() from None

    async def stream(self, payload: dict[str, Any]) -> AsyncIterator[dict[str, Any]]:
        clean_payload = self._policy.validate_and_minimize(payload)
        try:
            stream_method = getattr(self._provider, "stream", None)
            if callable(stream_method):
                async for chunk in stream_method(clean_payload):
                    yield chunk
            else:
                result = await self._provider.generate(clean_payload)
                yield result
        except Exception:
            raise EgressProviderError() from None
