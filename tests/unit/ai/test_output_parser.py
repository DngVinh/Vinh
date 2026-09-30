from __future__ import annotations

from pathlib import Path
import sys
import pytest

ROOT = Path(__file__).resolve().parents[3]
API_SRC = ROOT / "services" / "api" / "src"
if str(API_SRC) not in sys.path:
    sys.path.insert(0, str(API_SRC))

from campus247.agent.output_parser import OutputParseError, StrictOutputParser

SAMPLE_SCHEMA = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "type": "object",
    "additionalProperties": False,
    "required": ["route", "confidence"],
    "properties": {
        "route": {"type": "string", "enum": ["faq", "handover", "ticket"]},
        "confidence": {"type": "number", "minimum": 0.0, "maximum": 1.0},
    },
}


def test_parse_valid_json() -> None:
    parser = StrictOutputParser(schema=SAMPLE_SCHEMA)
    raw = '{"route": "faq", "confidence": 0.95}'
    result = parser.parse(raw)
    assert result == {"route": "faq", "confidence": 0.95}


def test_parse_markdown_fence_fails() -> None:
    parser = StrictOutputParser(schema=SAMPLE_SCHEMA)
    raw = """```json
{"route": "handover", "confidence": 0.8}
```"""
    with pytest.raises(OutputParseError, match="Malformed JSON"):
        parser.parse(raw)


@pytest.mark.parametrize(
    "raw",
    [
        '{"route": "faq", "route": "ticket", "confidence": 0.5}',
        '{"route": "faq", "confidence": 0.5, "nested": {"key": 1, "key": 2}}',
    ],
)
def test_parse_duplicate_keys_at_any_depth_fails(raw: str) -> None:
    with pytest.raises(OutputParseError, match="Duplicate JSON object key"):
        StrictOutputParser().parse(raw)


@pytest.mark.parametrize("number", ["NaN", "Infinity", "-Infinity", "1e400"])
def test_parse_non_finite_numbers_fail(number: str) -> None:
    with pytest.raises(OutputParseError, match="Non-finite JSON number"):
        StrictOutputParser(schema=SAMPLE_SCHEMA).parse(
            f'{{"route": "faq", "confidence": {number}}}'
        )


def test_parse_malformed_json_fails() -> None:
    parser = StrictOutputParser(schema=SAMPLE_SCHEMA)
    raw = '{"route": "faq", confidence: }'
    with pytest.raises(OutputParseError, match="Malformed JSON"):
        parser.parse(raw)


def test_parse_schema_violation_fails() -> None:
    parser = StrictOutputParser(schema=SAMPLE_SCHEMA)
    raw = '{"route": "unknown_route", "confidence": 0.5}'
    with pytest.raises(OutputParseError, match="Schema validation failed"):
        parser.parse(raw)


def test_parse_additional_properties_fails() -> None:
    parser = StrictOutputParser(schema=SAMPLE_SCHEMA)
    raw = '{"route": "faq", "confidence": 0.9, "extra": "unwanted"}'
    with pytest.raises(OutputParseError, match="Schema validation failed"):
        parser.parse(raw)
