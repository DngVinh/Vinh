from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
import yaml


@dataclass(frozen=True)
class PromptEntry:
    prompt_id: str
    version: str
    status: str
    purpose: str
    owner: str
    model_profiles: tuple[str, ...]
    required_variables: tuple[str, ...]
    template: str

    def render(self, variables: dict[str, Any]) -> str:
        # Check required variables
        for req_var in self.required_variables:
            if req_var not in variables:
                raise ValueError(f"Missing required variable '{req_var}' for prompt {self.prompt_id}@{self.version}")

        # Check for extra variables (variable contract enforcement)
        for provided_var in variables:
            if provided_var not in self.required_variables:
                raise ValueError(
                    f"Extra variable not permitted '{provided_var}' for prompt {self.prompt_id}@{self.version}"
                )

        try:
            return self.template.format(**variables)
        except Exception as e:
            raise ValueError(f"Failed to render prompt {self.prompt_id}@{self.version}: {e}") from e


class PromptRegistry:
    """Registry managing version-controlled, immutable prompts."""

    def __init__(self, entries: dict[str, PromptEntry]) -> None:
        self._entries = entries

    @classmethod
    def from_yaml(cls, yaml_path: Path | str) -> PromptRegistry:
        path = Path(yaml_path)
        with path.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        entries: dict[str, PromptEntry] = {}
        raw_prompts = data.get("prompts", {}) if isinstance(data, dict) else {}
        for key, p in raw_prompts.items():
            entry = PromptEntry(
                prompt_id=p.get("prompt_id", ""),
                version=p.get("version", "1.0.0"),
                status=p.get("status", "draft"),
                purpose=p.get("purpose", ""),
                owner=p.get("owner", ""),
                model_profiles=tuple(p.get("model_profiles", ["default"])),
                required_variables=tuple(p.get("required_variables", [])),
                template=p.get("template", ""),
            )
            entries[key] = entry
        return cls(entries=entries)

    def get(self, ref: str) -> PromptEntry:
        if ref not in self._entries:
            raise KeyError(f"Prompt not found in registry: '{ref}'")
        return self._entries[ref]
