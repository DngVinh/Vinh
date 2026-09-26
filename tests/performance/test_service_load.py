import os
import time
import yaml
import pytest
from campus247.bootstrap.telemetry import TelemetryManager


def load_profile():
    profile_path = os.path.join(os.path.dirname(__file__), "profiles", "service.yaml")
    with open(profile_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def test_telemetry_overhead_under_load():
    profile = load_profile()
    assert profile["profile_name"] == "telemetry_overhead_load"
    iterations = profile.get("benchmark_iterations", 500)
    max_overhead_ms = profile.get("max_overhead_ms_per_op", 2.0)

    # Baseline: no tracing
    t0 = time.perf_counter()
    for _ in range(iterations):
        _ = sum(i * 2 for i in range(50))
    t1 = time.perf_counter()
    baseline_total_ms = (t1 - t0) * 1000

    # Traced: with telemetry span
    telemetry = TelemetryManager("campus247-test")
    t2 = time.perf_counter()
    for _ in range(iterations):
        with telemetry.start_span("load_op", attributes={"iter": 1}):
            _ = sum(i * 2 for i in range(50))
    t3 = time.perf_counter()
    traced_total_ms = (t3 - t2) * 1000

    overhead_per_op_ms = (traced_total_ms - baseline_total_ms) / iterations
    assert overhead_per_op_ms < max_overhead_ms


def test_service_load_profile_validation():
    profile = load_profile()
    assert "benchmark_iterations" in profile
    assert "max_overhead_ms_per_op" in profile
    assert profile["max_overhead_ms_per_op"] > 0
