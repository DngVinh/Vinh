"""Schema validation engine for evaluation cases and results (TASK-EVAL-SCHEMA-001)."""

from __future__ import annotations

import functools
from pathlib import Path
from typing import Any

import yaml
from jsonschema import Draft202012Validator, FormatChecker


ROOT = Path(__file__).resolve().parents[3]
CASE_SCHEMA_PATH = ROOT / "evals" / "schemas" / "eval-case.schema.yaml"
RESULT_SCHEMA_PATH = ROOT / "evals" / "schemas" / "eval-result.schema.yaml"


class SchemaValidationError(Exception):
    """Raised when an eval artifact violates its schema."""


@functools.lru_cache(maxsize=4)
def get_case_validator() -> Draft202012Validator:
    with CASE_SCHEMA_PATH.open("r", encoding="utf-8") as f:
        schema = yaml.safe_load(f)
    return Draft202012Validator(schema, format_checker=FormatChecker())


@functools.lru_cache(maxsize=4)
def get_result_validator() -> Draft202012Validator:
    with RESULT_SCHEMA_PATH.open("r", encoding="utf-8") as f:
        schema = yaml.safe_load(f)
    return Draft202012Validator(schema, format_checker=FormatChecker())


def validate_case(data: dict[str, Any]) -> bool:
    """Validate an eval case against eval-case.schema.yaml."""
    validator = get_case_validator()
    errors = sorted(validator.iter_errors(data), key=lambda e: list(e.absolute_path))
    if errors:
        msg = "; ".join(f"/{'/'.join(map(str, e.absolute_path))}: {e.message}" for e in errors)
        raise SchemaValidationError(f"Invalid eval case: {msg}")
    return True


def validate_result(data: dict[str, Any]) -> bool:
    """Validate an eval result against eval-result.schema.yaml."""
    validator = get_result_validator()
    errors = sorted(validator.iter_errors(data), key=lambda e: list(e.absolute_path))
    if errors:
        msg = "; ".join(f"/{'/'.join(map(str, e.absolute_path))}: {e.message}" for e in errors)
        raise SchemaValidationError(f"Invalid eval result: {msg}")
    return True
