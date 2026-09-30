from __future__ import annotations

import pytest
from campus247.observability.agent_trace import (
    AgentTracer,
    TraceEvent,
    validate_trace_payload,
)


def test_trace_schema_rejects_non_allowlisted_and_oversized():
    # 1. Reject forbidden attributes (hidden thoughts / raw prompts / secrets)
    with pytest.raises(ValueError, match="Forbidden or non-allowlisted trace attribute: prompt"):
        validate_trace_payload({"trace_id": "tr-1", "prompt": "User raw query"})

    with pytest.raises(ValueError, match="Forbidden or non-allowlisted trace attribute: thought"):
        validate_trace_payload({"trace_id": "tr-1", "thought": "Internal chain of thought"})

    with pytest.raises(ValueError, match="Forbidden or non-allowlisted trace attribute: api_key"):
        validate_trace_payload({"trace_id": "tr-1", "api_key": "secret_key_123"})

    # 2. Reject non-allowlisted random key
    with pytest.raises(ValueError, match="Forbidden or non-allowlisted trace attribute: unknown_attr"):
        validate_trace_payload({"trace_id": "tr-1", "unknown_attr": "value"})

    # 3. Reject over-sized string attribute
    oversized = "A" * 1005
    with pytest.raises(ValueError, match="exceeds maximum length"):
        validate_trace_payload({"trace_id": "tr-1", "decision": oversized})


def test_correlation_spans_without_exposing_identity_directly():
    tracer = AgentTracer()
    raw_user_id = "student_nguyen_van_a_998877"

    evt1 = tracer.record(
        trace_id="trace-abc-123",
        span_id="span-1",
        session_id="session-001",
        turn_id="turn-001",
        raw_user_id=raw_user_id,
        event_type="route_decision",
        decision="grounded_faq",
        route="grounded_faq",
    )

    evt2 = tracer.record(
        trace_id="trace-abc-123",
        span_id="span-2",
        parent_span_id="span-1",
        session_id="session-001",
        turn_id="turn-001",
        raw_user_id=raw_user_id,
        event_type="evidence_evaluated",
        evidence_ids=["DOC-123", "DOC-456"],
        decision="passed_gate",
    )

    # Both events share trace_id and principal_hash
    assert evt1.trace_id == evt2.trace_id == "trace-abc-123"
    assert evt1.principal_hash == evt2.principal_hash
    # Raw user identity must NOT appear in stored attributes or dumps
    event_str = str(evt1.to_dict()) + str(evt2.to_dict())
    assert raw_user_id not in event_str
    assert "nguyen_van_a" not in event_str


def test_reconstruct_run_at_decision_level_without_hidden_reasoning():
    tracer = AgentTracer()
    trace_id = "trace-recon-999"

    tracer.record(
        trace_id=trace_id,
        span_id="s1",
        session_id="sess-1",
        turn_id="turn-1",
        raw_user_id="user-42",
        event_type="safety_evaluated",
        decision="normal",
    )
    tracer.record(
        trace_id=trace_id,
        span_id="s2",
        session_id="sess-1",
        turn_id="turn-1",
        raw_user_id="user-42",
        event_type="route_decision",
        decision="room_booking",
        route="room_booking",
    )
    tracer.record(
        trace_id=trace_id,
        span_id="s3",
        session_id="sess-1",
        turn_id="turn-1",
        raw_user_id="user-42",
        event_type="terminal_transition",
        decision="awaiting_confirmation",
        tool_phase="awaiting_confirmation",
    )

    decisions = tracer.reconstruct_decisions(trace_id)
    assert len(decisions) == 3
    assert [d["event_type"] for d in decisions] == [
        "safety_evaluated",
        "route_decision",
        "terminal_transition",
    ]
    # No hidden thoughts or raw prompts stored
    for d in decisions:
        assert "thought" not in d
        assert "prompt" not in d
        assert "chain_of_thought" not in d
