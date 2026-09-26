from __future__ import annotations

import json
import re
from typing import Any
from jsonschema import Draft202012Validator, ValidationError


class OutputParseError(Exception):
    """Raised when LLM output cannot be strictly parsed or fails schema validation."""
    pass


class StrictOutputParser:
    """Strict JSON parser and schema validator for machine-consumed LLM outputs."""

    def __init__(self, schema: dict[str, Any] | None = None) -> None:
        self._schema = schema
        self._validator = Draft202012Validator(schema) if schema else None

    def _extract_json_text(self, raw_text: str) -> str:
        text = raw_text.strip()
        # Handle markdown fence ```json ... ``` or ``` ... ```
        if text.startswith("```"):
            fence_pattern = re.compile(r"^```(?:json)?\s*\n?(.*?)\n?```$", re.DOTALL | re.IGNORECASE)
            match = fence_pattern.search(text)
            if match:
                text = match.group(1).strip()
        return text

    def parse(self, raw_text: str) -> dict[str, Any]:
        if not raw_text or not raw_text.strip():
            raise OutputParseError("LLM response output is empty")

        cleaned = self._extract_json_text(raw_text)

        try:
            parsed = json.loads(cleaned)
        except (json.JSONDecodeError, ValueError) as err:
            raise OutputParseError(f"Malformed JSON in LLM response: {err}") from err

        if not isinstance(parsed, dict):
            raise OutputParseError(f"Expected JSON object at root, got {type(parsed).__name__}")

        if self._validator:
            errors = sorted(self._validator.iter_errors(parsed), key=lambda e: e.path)
            if errors:
                first_err: ValidationError = errors[0]
                field_path = ".".join(str(p) for p in first_err.path) or "root"
                raise OutputParseError(
                    f"Schema validation failed at '{field_path}': {first_err.message}"
                )

        return parsed
