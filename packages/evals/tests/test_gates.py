"""Unit tests for AI evaluation regression gate (TASK-EVAL-GATE-001)."""

from pathlib import Path
import pytest
from packages.evals.src.gates import evaluate_gates, GateDecision

GATE_CONFIG = Path(__file__).resolve().parents[1] / "gates" / "v1.yaml"


def test_gate_passes_healthy_metrics():
    metrics = {
        "EVAL-METRIC-001": 0.85,
        "EVAL-METRIC-002": 0.95,
        "EVAL-METRIC-003": 0.98,
        "EVAL-METRIC-004": 0.97,
        "EVAL-METRIC-010": 0,
        "EVAL-METRIC-011": 0,
        "EVAL-METRIC-012": 0,
        "EVAL-METRIC-013": 0,
    }
    decision = evaluate_gates(metrics, config_path=GATE_CONFIG)
    assert decision.passed is True
    assert len(decision.failures) == 0


def test_gate_fails_hard_zero_violation():
    metrics = {
        "EVAL-METRIC-001": 0.85,
        "EVAL-METRIC-002": 0.95,
        "EVAL-METRIC-010": 1,  # Unauthorized write detected!
    }
    decision = evaluate_gates(metrics, config_path=GATE_CONFIG)
    assert decision.passed is False
    assert any("hard_zero" in f.lower() or "EVAL-METRIC-010" in f for f in decision.failures)


def test_gate_fails_threshold_drop():
    metrics = {
        "EVAL-METRIC-001": 0.50,  # Below 0.70
        "EVAL-METRIC-002": 0.95,
        "EVAL-METRIC-010": 0,
    }
    decision = evaluate_gates(metrics, config_path=GATE_CONFIG)
    assert decision.passed is False
    assert any("EVAL-METRIC-001" in f for f in decision.failures)
