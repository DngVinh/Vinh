"""AI evaluation regression gate and threshold checker (TASK-EVAL-GATE-001)."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
import yaml

DEFAULT_GATE_CONFIG = Path(__file__).resolve().parents[1] / "gates" / "v1.yaml"


@dataclass
class GateDecision:
    passed: bool
    failures: list[str] = field(default_factory=list)
    metrics: dict[str, float | int] = field(default_factory=dict)


def evaluate_gates(
    metrics: dict[str, float | int],
    config_path: Path | str | None = None,
) -> GateDecision:
    path = Path(config_path or DEFAULT_GATE_CONFIG)
    with path.open("r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    failures: list[str] = []
    hard_zeros = config.get("hard_zero_metrics", {})
    for metric_id, description in hard_zeros.items():
        if metric_id in metrics:
            val = metrics[metric_id]
            if val != 0:
                failures.append(f"Hard-zero violation for {metric_id} ({description}): expected 0, got {val}")

    thresholds = config.get("thresholds", {})
    for metric_id, rule in thresholds.items():
        if metric_id in metrics:
            val = float(metrics[metric_id])
            op = rule.get("operator", ">=")
            target = float(rule.get("value", 0.0))
            name = rule.get("name", metric_id)

            if op == ">=" and val < target:
                failures.append(f"Threshold failed for {metric_id} ({name}): {val:.3f} < {target:.3f}")
            elif op == "==" and val != target:
                failures.append(f"Threshold failed for {metric_id} ({name}): {val:.3f} != {target:.3f}")
            elif op == "<=" and val > target:
                failures.append(f"Threshold failed for {metric_id} ({name}): {val:.3f} > {target:.3f}")

    return GateDecision(passed=(len(failures) == 0), failures=failures, metrics=metrics)
