"""Load scenario definitions and plan validator for local load-testing (TASK-TEST-LOAD-001)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any
import yaml


@dataclass(frozen=True)
class TargetSlo:
    p95_latency_ms: int
    p99_latency_ms: int


@dataclass(frozen=True)
class ScenarioStep:
    id: str
    weight_percent: int
    method: str
    path: str


@dataclass(frozen=True)
class LoadTestPlan:
    plan_id: str
    peak_concurrent_users: int
    ramp_up_seconds: int
    steady_state_seconds: int
    slo: TargetSlo
    scenarios: tuple[ScenarioStep, ...]


def load_test_plan(config_path: Path | str) -> LoadTestPlan:
    path = Path(config_path)
    with path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    workload = data.get("workload", {})
    slo_data = workload.get("target_slo", {})

    peak = workload.get("peak_concurrent_users", 0)
    if peak <= 0:
        raise ValueError("peak_concurrent_users must be positive")

    p95 = slo_data.get("p95_latency_ms", 0)
    p99 = slo_data.get("p99_latency_ms", 0)
    if p95 <= 0 or p99 <= 0 or p95 > p99:
        raise ValueError("Invalid SLO latency bounds: p95 must be <= p99")

    steps: list[ScenarioStep] = []
    total_weight = 0
    for s in data.get("scenarios", []):
        weight = s.get("weight_percent", 0)
        total_weight += weight
        steps.append(
            ScenarioStep(
                id=s.get("id", ""),
                weight_percent=weight,
                method=s.get("method", "GET"),
                path=s.get("path", "/"),
            )
        )

    if total_weight != 100:
        raise ValueError(f"Scenario weights must sum to 100%, got {total_weight}%")

    return LoadTestPlan(
        plan_id=data.get("plan_id", ""),
        peak_concurrent_users=peak,
        ramp_up_seconds=workload.get("ramp_up_seconds", 0),
        steady_state_seconds=workload.get("steady_state_seconds", 0),
        slo=TargetSlo(p95_latency_ms=p95, p99_latency_ms=p99),
        scenarios=tuple(steps),
    )
