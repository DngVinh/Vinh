import pytest
from campus247.application.operations.metrics import (
    MetricsCollector,
    MetricAlarm,
    evaluate_alarm_condition,
)


def test_metrics_collector_and_slo_evaluation():
    collector = MetricsCollector()

    # Record 100 successful requests with low latency
    for _ in range(99):
        collector.record_request(status_code=200, duration_ms=150.0)
    # Record 1 500 error
    collector.record_request(status_code=500, duration_ms=300.0)

    summary = collector.get_summary()
    assert summary["total_requests"] == 100
    assert summary["error_rate"] == 0.01  # 1% error
    assert summary["availability"] == 0.99  # 99%
    assert summary["p95_latency_ms"] <= 300.0


def test_metrics_alarm_evaluation_breach():
    alarm = MetricAlarm(
        name="HighApiErrorRate",
        metric="error_rate",
        threshold=0.05,  # 5% threshold
        comparison="greater_than",
    )

    # 10% error rate breaches threshold
    is_breached = evaluate_alarm_condition(alarm, current_value=0.10)
    assert is_breached is True

    # 2% error rate does not breach threshold
    is_breached = evaluate_alarm_condition(alarm, current_value=0.02)
    assert is_breached is False


def test_metrics_collector_negative_duration_rejection():
    collector = MetricsCollector()
    with pytest.raises(ValueError, match="duration_ms must be non-negative"):
        collector.record_request(status_code=200, duration_ms=-10.0)
