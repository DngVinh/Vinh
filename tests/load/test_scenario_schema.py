"""Unit test for local load-testing harness scenario schema (TASK-TEST-LOAD-001)."""

from pathlib import Path
import pytest
from tests.load.scenarios import load_test_plan

CONFIG_PATH = Path(__file__).resolve().parent / "config.yaml"


def test_load_config_validates_peak_users_and_slo():
    plan = load_test_plan(CONFIG_PATH)
    assert plan.peak_concurrent_users == 200
    assert plan.ramp_up_seconds == 10
    assert plan.steady_state_seconds == 30
    assert plan.slo.p95_latency_ms <= 2500
    assert plan.slo.p99_latency_ms <= 5000
    assert len(plan.scenarios) == 3


def test_scenario_weights_sum_to_100():
    plan = load_test_plan(CONFIG_PATH)
    total_weight = sum(s.weight_percent for s in plan.scenarios)
    assert total_weight == 100


def test_negative_invalid_slo_bounds(tmp_path):
    bad_config = tmp_path / "bad_config.yaml"
    bad_config.write_text("""
plan_id: "BAD"
workload:
  peak_concurrent_users: 200
  ramp_up_seconds: 10
  steady_state_seconds: 30
  target_slo:
    p95_latency_ms: 6000
    p99_latency_ms: 5000
scenarios:
  - id: "S1"
    weight_percent: 100
    method: "GET"
    path: "/"
""", encoding="utf-8")

    with pytest.raises(ValueError, match="Invalid SLO latency bounds"):
        load_test_plan(bad_config)
