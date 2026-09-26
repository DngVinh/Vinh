from __future__ import annotations

from pathlib import Path
from typing import Any
import pytest
import yaml


def calculate_relative_luminance(r: int, g: int, b: int) -> float:
    """Calculate WCAG 2.2 relative luminance for sRGB channels."""
    normalized = [c / 255.0 for c in (r, g, b)]
    linearized = [
        c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
        for c in normalized
    ]
    return 0.2126 * linearized[0] + 0.7152 * linearized[1] + 0.0722 * linearized[2]


def calculate_contrast_ratio(rgb1: tuple[int, int, int], rgb2: tuple[int, int, int]) -> float:
    """Calculate WCAG 2.2 contrast ratio between two colors."""
    lum1 = calculate_relative_luminance(*rgb1)
    lum2 = calculate_relative_luminance(*rgb2)
    bright, dark = max(lum1, lum2), min(lum1, lum2)
    return (bright + 0.05) / (dark + 0.05)


@pytest.fixture
def a11y_manifest() -> dict[str, Any]:
    manifest_path = Path(__file__).parent / "accessibility-manifest.yaml"
    assert manifest_path.exists(), "Accessibility manifest must exist"
    return yaml.safe_load(manifest_path.read_text(encoding="utf-8"))


def test_a11y_manifest_structure_and_standards(a11y_manifest: dict[str, Any]) -> None:
    assert a11y_manifest["standard"] == "WCAG 2.2 AA"
    assert a11y_manifest["target_conformance"] == "Level AA"
    assert len(a11y_manifest["checkpoints"]) >= 5

    for checkpoint in a11y_manifest["checkpoints"]:
        rule = checkpoint.get("rule_id", "UNKNOWN")
        assert checkpoint["status"] == "PASS", f"Checkpoint {rule} did not pass"
        assert "rule_id" in checkpoint, f"Missing rule_id in checkpoint: {checkpoint}"
        assert "description" in checkpoint, f"Missing description in checkpoint {rule}"


def test_contrast_ratio_evaluator_passes_for_accessible_colors() -> None:
    black = (0, 0, 0)
    white = (255, 255, 255)
    ratio = calculate_contrast_ratio(black, white)
    assert ratio >= 4.5, f"Expected contrast ratio >= 4.5, got {ratio:.2f}"


def test_negative_low_contrast_fails_wcag_threshold() -> None:
    # Negative path: low contrast text fails WCAG minimum 4.5:1
    light_gray = (200, 200, 200)
    white = (255, 255, 255)
    ratio = calculate_contrast_ratio(light_gray, white)
    assert ratio < 4.5, f"Expected low contrast < 4.5 for negative test, got {ratio:.2f}"
