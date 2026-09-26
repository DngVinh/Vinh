from __future__ import annotations

from pathlib import Path
import sys
import pytest

ROOT = Path(__file__).resolve().parents[3]
API_SRC = ROOT / "services" / "api" / "src"
if str(API_SRC) not in sys.path:
    sys.path.insert(0, str(API_SRC))

from campus247.agent.prompts import PromptEntry, PromptRegistry


@pytest.fixture
def registry() -> PromptRegistry:
    reg_path = ROOT / "packages" / "prompts" / "registry.yaml"
    return PromptRegistry.from_yaml(reg_path)


def test_load_prompt_and_render(registry: PromptRegistry) -> None:
    entry = registry.get("AI-PROMPT-INTENT-001@1.0.0")
    assert isinstance(entry, PromptEntry)
    assert entry.prompt_id == "AI-PROMPT-INTENT-001"
    assert entry.status == "approved"

    rendered = entry.render({"user_query": "Học phí kỳ này bao nhiêu?"})
    assert "Học phí kỳ này bao nhiêu?" in rendered
    assert "IntentDecision" in rendered


def test_render_missing_variable_fails(registry: PromptRegistry) -> None:
    entry = registry.get("AI-PROMPT-INTENT-001@1.0.0")
    with pytest.raises(ValueError, match="Missing required variable"):
        entry.render({})


def test_render_extra_variable_fails(registry: PromptRegistry) -> None:
    entry = registry.get("AI-PROMPT-INTENT-001@1.0.0")
    with pytest.raises(ValueError, match="Extra variable not permitted"):
        entry.render({"user_query": "Test", "unauthorized_extra": "hack"})


def test_missing_prompt_key_fails(registry: PromptRegistry) -> None:
    with pytest.raises(KeyError, match="Prompt not found"):
        registry.get("AI-PROMPT-NONEXISTENT@1.0.0")
