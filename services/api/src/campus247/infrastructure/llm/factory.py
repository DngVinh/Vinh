from __future__ import annotations

import os
from pathlib import Path

from campus247.bootstrap.settings import Settings, get_settings
from campus247.infrastructure.llm.fake import DeterministicFakeProvider
from campus247.infrastructure.llm.multi_provider import MultiProviderFallbackGateway
from campus247.infrastructure.llm.openai_adapter import OpenAICompatibleAdapter
from campus247.ports.llm import LlmGateway


def create_llm_gateway(
    demo_mode: bool | None = None,
    fixture_path: Path | str | None = None,
    settings: Settings | None = None,
) -> LlmGateway:
    """Creates a resilient MultiProviderFallbackGateway.

    Hierarchy:
    1. Free tier: Google Gemini (via OpenAI-compatible endpoint with LAB_MODEL).
    2. Paid tier: DeepSeek API (using DEEPSEEK_API_KEY with DEEPSEEK_MODEL, called only if free fails).
    3. Safety fallback: DeterministicFakeProvider for offline tests / fixture evaluation.
    """
    app_settings = settings or get_settings()

    if demo_mode is None:
        demo_mode = app_settings.DEMO_MODE

    # Offline fixture provider
    if fixture_path is not None:
        fallback_fake = DeterministicFakeProvider.from_yaml(fixture_path)
    else:
        fallback_fake = DeterministicFakeProvider.default()

    # 1. Primary Free Provider: Gemini via OpenAI-compatible endpoint
    gemini_key = app_settings.OPENAI_API_KEY or app_settings.GEMINI_API_KEY
    gemini_adapter = OpenAICompatibleAdapter(
        provider_id="gemini",
        base_url=app_settings.OPENAI_BASE_URL,
        api_key=gemini_key,
        model_name=app_settings.LAB_MODEL,
        is_free=True,
    )

    # 2. Secondary Paid Provider: DeepSeek
    deepseek_adapter = OpenAICompatibleAdapter(
        provider_id="deepseek",
        base_url=app_settings.DEEPSEEK_BASE_URL,
        api_key=app_settings.DEEPSEEK_API_KEY,
        model_name=app_settings.DEEPSEEK_MODEL,
        is_free=False,
    )

    providers: list[tuple[str, LlmGateway, bool]] = [
        ("gemini_free", gemini_adapter, True),
        ("deepseek_paid", deepseek_adapter, False),
    ]

    return MultiProviderFallbackGateway(
        providers=providers,
        fallback_gateway=fallback_fake if demo_mode else None,
    )
