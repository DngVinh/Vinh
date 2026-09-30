"""TASK-TEST-WEB-002: Verify the redesigned journeys in real browser evidence.

This test validates that the ui-redesign-manifest.yaml covers every required
redesigned P0 journey, viewport, keyboard check, zoom check, and non-color
indicator check.  It does NOT fabricate browser evidence — checks that require
a real browser are expected to be labelled ``not_verified``.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
import yaml


MANIFEST_PATH = Path(__file__).parent / "ui-redesign-manifest.yaml"

# ── Required coverage from TASK-TEST-WEB-002.yaml dependencies ──

REQUIRED_TASK_REFS: set[str] = {
    "TASK-WEB-HOME-002",
    "TASK-WEB-CITE-002",
    "TASK-WEB-SCHED-003",
    "TASK-WEB-TICK-003",
    "TASK-WEB-DOCREQ-002",
    "TASK-WEB-ROOM-003",
    "TASK-WEB-SAFE-001",
    "TASK-WEB-STAFF-002",
    "TASK-WEB-KNOW-002",
    "TASK-WEB-OPS-002",
    "TASK-WEB-PRIV-002",
}

REQUIRED_VIEWPORT_IDS: set[str] = {"VP-MOBILE", "VP-TABLET", "VP-DESKTOP"}

REQUIRED_CHECK_IDS: set[str] = {
    "CHK-KEYBOARD",
    "CHK-ZOOM-200",
    "CHK-NONCOLOR",
    "CHK-SEMANTICS",
    "CHK-STATUS",
}

ALLOWED_OUTCOMES: set[str] = {"pass", "fail", "not_verified"}


@pytest.fixture
def manifest() -> dict[str, Any]:
    assert MANIFEST_PATH.exists(), (
        f"UI redesign manifest must exist at {MANIFEST_PATH}"
    )
    data = yaml.safe_load(MANIFEST_PATH.read_text(encoding="utf-8"))
    assert isinstance(data, dict), "Manifest root must be a YAML mapping"
    return data


# ─────────────────────────── Structure tests ───────────────────────────


def test_manifest_declares_conformance_target(manifest: dict[str, Any]) -> None:
    """WCAG 2.2 AA conformance target must be stated."""
    assert manifest["conformance_target"] == "WCAG 2.2 AA"


def test_manifest_declares_required_viewports(manifest: dict[str, Any]) -> None:
    """Three viewports (360, 768, 1280 CSS px) must be declared."""
    vp_ids = {vp["id"] for vp in manifest["required_viewports"]}
    assert REQUIRED_VIEWPORT_IDS.issubset(vp_ids), (
        f"Missing viewports: {REQUIRED_VIEWPORT_IDS - vp_ids}"
    )
    widths = {vp["width_css_px"] for vp in manifest["required_viewports"]}
    assert {360, 768, 1280}.issubset(widths), f"Missing viewport widths: {widths}"


def test_manifest_declares_required_checks(manifest: dict[str, Any]) -> None:
    """Keyboard, zoom, non-color, semantics and status checks must be declared."""
    check_ids = {c["id"] for c in manifest["required_checks"]}
    assert REQUIRED_CHECK_IDS.issubset(check_ids), (
        f"Missing checks: {REQUIRED_CHECK_IDS - check_ids}"
    )


# ─────────────────────────── Coverage tests ────────────────────────────


def test_every_dependency_task_has_journey(manifest: dict[str, Any]) -> None:
    """Every task listed in TASK-TEST-WEB-002 dependencies must have a journey."""
    covered_tasks = {j["task_ref"] for j in manifest["journeys"]}
    missing = REQUIRED_TASK_REFS - covered_tasks
    assert not missing, f"Missing journey coverage for tasks: {missing}"


def test_every_journey_has_all_viewports(manifest: dict[str, Any]) -> None:
    """Each journey must declare an outcome for every required viewport."""
    for journey in manifest["journeys"]:
        jid = journey["id"]
        vp_ids = {v["viewport"] for v in journey["viewports"]}
        missing = REQUIRED_VIEWPORT_IDS - vp_ids
        assert not missing, (
            f"Journey {jid} missing viewport entries: {missing}"
        )


def test_every_journey_has_all_checks(manifest: dict[str, Any]) -> None:
    """Each journey must declare an outcome for every required a11y check."""
    for journey in manifest["journeys"]:
        jid = journey["id"]
        check_ids = {c["check"] for c in journey["checks"]}
        missing = REQUIRED_CHECK_IDS - check_ids
        assert not missing, (
            f"Journey {jid} missing a11y checks: {missing}"
        )


def test_all_outcomes_are_valid(manifest: dict[str, Any]) -> None:
    """Every outcome must be one of pass, fail, or not_verified."""
    for journey in manifest["journeys"]:
        jid = journey["id"]
        for vp in journey["viewports"]:
            assert vp["outcome"] in ALLOWED_OUTCOMES, (
                f"{jid} viewport {vp['viewport']}: invalid outcome '{vp['outcome']}'"
            )
        for ck in journey["checks"]:
            assert ck["outcome"] in ALLOWED_OUTCOMES, (
                f"{jid} check {ck['check']}: invalid outcome '{ck['outcome']}'"
            )


def test_no_fabricated_failures(manifest: dict[str, Any]) -> None:
    """No journey check may be marked 'fail' — actual failures are release blockers.

    If a check genuinely fails it must be fixed, not recorded as passing.
    Unavailable evidence must be 'not_verified', never 'fail' as placeholder.
    """
    for journey in manifest["journeys"]:
        jid = journey["id"]
        for ck in journey["checks"]:
            assert ck["outcome"] != "fail", (
                f"{jid} check {ck['check']} is marked 'fail' — "
                "fix the issue or mark 'not_verified' if evidence is unavailable"
            )


def test_summary_counts_are_consistent(manifest: dict[str, Any]) -> None:
    """Summary statistics must match actual journey data."""
    summary = manifest["summary"]
    journeys = manifest["journeys"]

    assert summary["total_journeys"] == len(journeys)

    actual_vp_total = sum(len(j["viewports"]) for j in journeys)
    assert summary["total_viewport_checks"] == actual_vp_total

    actual_check_total = sum(len(j["checks"]) for j in journeys)
    assert summary["total_a11y_checks"] == actual_check_total

    actual_vp_pass = sum(
        1 for j in journeys for v in j["viewports"] if v["outcome"] == "pass"
    )
    actual_vp_nv = sum(
        1 for j in journeys for v in j["viewports"] if v["outcome"] == "not_verified"
    )
    assert summary["viewport_pass"] == actual_vp_pass
    assert summary["viewport_not_verified"] == actual_vp_nv

    actual_ck_pass = sum(
        1 for j in journeys for c in j["checks"] if c["outcome"] == "pass"
    )
    actual_ck_nv = sum(
        1 for j in journeys for c in j["checks"] if c["outcome"] == "not_verified"
    )
    actual_ck_fail = sum(
        1 for j in journeys for c in j["checks"] if c["outcome"] == "fail"
    )
    assert summary["a11y_pass"] == actual_ck_pass
    assert summary["a11y_not_verified"] == actual_ck_nv
    assert summary["a11y_fail"] == actual_ck_fail


def test_honest_disclosure_present(manifest: dict[str, Any]) -> None:
    """Manifest must include an honest disclosure about unavailable evidence."""
    disclosure = manifest["summary"].get("honest_disclosure", "")
    assert "not_verified" in disclosure.lower() or "not verified" in disclosure.lower(), (
        "Summary must honestly disclose which checks could not be verified"
    )
    assert "browser" in disclosure.lower(), (
        "Disclosure must mention that a real browser is required"
    )
