from __future__ import annotations

import json
import math
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

    def parse(self, raw_text: str) -> dict[str, Any]:
        if not raw_text or not raw_text.strip():
            raise OutputParseError("LLM response output is empty")

        def unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
            result: dict[str, Any] = {}
            for key, value in pairs:
                if key in result:
                    raise ValueError("Duplicate JSON object key")
                result[key] = value
            return result

        def reject_constant(_: str) -> None:
            raise ValueError("Non-finite JSON number")

        def finite_float(value: str) -> float:
            number = float(value)
            if not math.isfinite(number):
                raise ValueError("Non-finite JSON number")
            return number

        try:
            parsed = json.loads(
                raw_text,
                object_pairs_hook=unique_object,
                parse_constant=reject_constant,
                parse_float=finite_float,
            )
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
