from __future__ import annotations

import hashlib
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


FORBIDDEN_ATTRIBUTES = {
    "prompt",
    "raw_prompt",
    "completion",
    "raw_completion",
    "thought",
    "chain_of_thought",
    "cot",
    "secret",
    "api_key",
    "token",
    "password",
    "ssn",
    "national_id",
}

ALLOWLISTED_KEYS = {
    "trace_id",
    "span_id",
    "parent_span_id",
    "session_id",
    "turn_id",
    "principal_hash",
    "event_type",
    "route",
    "decision",
    "evidence_ids",
    "tool_phase",
    "error_code",
    "latency_ms",
    "timestamp",
}

MAX_ATTRIBUTE_LEN = 1000


def validate_trace_payload(payload: Dict[str, Any]) -> None:
    for key, value in payload.items():
        if key in FORBIDDEN_ATTRIBUTES or key not in ALLOWLISTED_KEYS:
            raise ValueError(f"Forbidden or non-allowlisted trace attribute: {key}")
        if isinstance(value, str) and len(value) > MAX_ATTRIBUTE_LEN:
            raise ValueError(f"Attribute '{key}' exceeds maximum length {MAX_ATTRIBUTE_LEN}")


def hash_principal(raw_user_id: str) -> str:
    salt = "campus247_obs_salt"
    h = hashlib.sha256(f"{salt}:{raw_user_id}".encode("utf-8")).hexdigest()
    return f"prn_{h[:16]}"


@dataclass
class TraceEvent:
    trace_id: str
    span_id: str
    session_id: str
    turn_id: str
    principal_hash: str
    event_type: str
    timestamp: str
    parent_span_id: Optional[str] = None
    route: Optional[str] = None
    decision: Optional[str] = None
    evidence_ids: List[str] = field(default_factory=list)
    tool_phase: Optional[str] = None
    error_code: Optional[str] = None
    latency_ms: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        return {k: v for k, v in asdict(self).items() if v is not None}


class AgentTracer:
    """Records privacy-safe, correlated agent decision traces."""

    def __init__(self) -> None:
        self._events: List[TraceEvent] = []

    def record(
        self,
        trace_id: str,
        span_id: str,
        session_id: str,
        turn_id: str,
        raw_user_id: str,
        event_type: str,
        parent_span_id: Optional[str] = None,
        route: Optional[str] = None,
        decision: Optional[str] = None,
        evidence_ids: Optional[List[str]] = None,
        tool_phase: Optional[str] = None,
        error_code: Optional[str] = None,
        latency_ms: Optional[float] = None,
    ) -> TraceEvent:
        principal_hash = hash_principal(raw_user_id)
        now_ts = datetime.now(timezone.utc).isoformat()

        payload = {
            "trace_id": trace_id,
            "span_id": span_id,
            "parent_span_id": parent_span_id,
            "session_id": session_id,
            "turn_id": turn_id,
            "principal_hash": principal_hash,
            "event_type": event_type,
            "route": route,
            "decision": decision,
            "evidence_ids": evidence_ids or [],
            "tool_phase": tool_phase,
            "error_code": error_code,
            "latency_ms": latency_ms,
            "timestamp": now_ts,
        }
        filtered = {k: v for k, v in payload.items() if v is not None}
        validate_trace_payload(filtered)

        event = TraceEvent(
            trace_id=trace_id,
            span_id=span_id,
            parent_span_id=parent_span_id,
            session_id=session_id,
            turn_id=turn_id,
            principal_hash=principal_hash,
            event_type=event_type,
            route=route,
            decision=decision,
            evidence_ids=evidence_ids or [],
            tool_phase=tool_phase,
            error_code=error_code,
            latency_ms=latency_ms,
            timestamp=now_ts,
        )
        self._events.append(event)
        return event

    def get_trace(self, trace_id: str) -> List[TraceEvent]:
        return [e for e in self._events if e.trace_id == trace_id]

    def reconstruct_decisions(self, trace_id: str) -> List[Dict[str, Any]]:
        trace_events = self.get_trace(trace_id)
        return [e.to_dict() for e in trace_events]
