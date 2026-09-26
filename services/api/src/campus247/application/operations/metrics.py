from dataclasses import dataclass
from typing import Any, Dict, List, Literal


@dataclass(frozen=True)
class MetricAlarm:
    name: str = ""
    metric: str = ""
    threshold: float = 0.0
    comparison: Literal["greater_than", "greater_than_or_equal", "less_than", "less_than_or_equal"] = "greater_than"

    def is_breached(self, current_value: float) -> bool:
        if self.comparison == "greater_than":
            return current_value > self.threshold
        elif self.comparison == "greater_than_or_equal":
            return current_value >= self.threshold
        elif self.comparison == "less_than":
            return current_value < self.threshold
        elif self.comparison == "less_than_or_equal":
            return current_value <= self.threshold
        return False


def evaluate_alarm_condition(alarm: MetricAlarm, current_value: float) -> bool:
    return alarm.is_breached(current_value)


class MetricsCollector:
    def __init__(self) -> None:
        self._request_durations: List[float] = []
        self._status_codes: List[int] = []

    def record_request(self, status_code: int, duration_ms: float) -> None:
        if duration_ms < 0:
            raise ValueError("duration_ms must be non-negative.")
        self._status_codes.append(status_code)
        self._request_durations.append(duration_ms)

    def get_summary(self) -> Dict[str, Any]:
        total = len(self._status_codes)
        if total == 0:
            return {
                "total_requests": 0,
                "error_rate": 0.0,
                "availability": 1.0,
                "p95_latency_ms": 0.0,
            }

        errors = sum(1 for code in self._status_codes if code >= 500)
        error_rate = errors / total
        availability = 1.0 - error_rate

        sorted_durations = sorted(self._request_durations)
        idx_p95 = int(len(sorted_durations) * 0.95)
        p95_latency = sorted_durations[min(idx_p95, len(sorted_durations) - 1)]

        return {
            "total_requests": total,
            "error_rate": round(error_rate, 4),
            "availability": round(availability, 4),
            "p95_latency_ms": round(p95_latency, 2),
        }
