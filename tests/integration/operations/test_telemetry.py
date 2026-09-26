import pytest
from campus247.bootstrap.telemetry import (
    TelemetryManager,
    extract_trace_context,
    sanitize_trace_attributes,
)


def test_telemetry_trace_context_extraction():
    # AC-01: Valid W3C traceparent extraction
    traceparent = "00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01"
    headers = {"traceparent": traceparent}
    ctx = extract_trace_context(headers)

    assert ctx is not None
    assert ctx["trace_id"] == "4bf92f3577b34da6a3ce929d0e0e4736"
    assert ctx["parent_span_id"] == "00f067aa0ba902b7"
    assert ctx["sampled"] is True


def test_telemetry_malformed_traceparent_fallback():
    # AC-02: Malformed traceparent should fallback gracefully to generated trace ID
    headers = {"traceparent": "invalid-traceparent"}
    ctx = extract_trace_context(headers)

    assert ctx is not None
    assert len(ctx["trace_id"]) == 32
    assert ctx["parent_span_id"] is None


def test_telemetry_attribute_sanitization():
    # AC-01: Sensitive attributes must be redacted
    attrs = {
        "http.method": "POST",
        "http.target": "/api/v1/auth/login",
        "authorization": "Bearer secret-token-123",
        "cookie": "session=abc-secret",
        "password": "my-secret-password",
    }
    sanitized = sanitize_trace_attributes(attrs)

    assert sanitized["http.method"] == "POST"
    assert sanitized["authorization"] == "[REDACTED]"
    assert sanitized["cookie"] == "[REDACTED]"
    assert sanitized["password"] == "[REDACTED]"


def test_telemetry_manager_span_lifecycle():
    manager = TelemetryManager(service_name="campus247-api")
    with manager.start_span("test-operation", attributes={"custom.attr": "value"}) as span:
        assert span.trace_id is not None
        assert span.span_id is not None
        assert span.name == "test-operation"
        assert span.attributes["custom.attr"] == "value"

    assert span.is_ended is True
