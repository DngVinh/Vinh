from __future__ import annotations

import re
import secrets
import time
from typing import Any, Dict, Optional


SENSITIVE_KEYS = {
    "authorization",
    "cookie",
    "set-cookie",
    "password",
    "token",
    "secret",
    "api_key",
    "apikey",
    "api-key",
    "access_token",
    "access-token",
    "refresh_token",
    "refresh-token",
    "email",
    "phone",
    "student_id",
}


def extract_trace_context(headers: Dict[str, str]) -> Dict[str, Any]:
    traceparent = headers.get("traceparent") or headers.get("Traceparent")
    if traceparent:
        pattern = r"^00-([0-9a-f]{32})-([0-9a-f]{16})-([0-9a-f]{2})$"
        match = re.match(pattern, traceparent.strip().lower())
        if match:
            trace_id, parent_span_id, flags = match.groups()
            return {
                "trace_id": trace_id,
                "parent_span_id": parent_span_id,
                "sampled": flags == "01",
            }

    # Fallback to fresh trace context
    return {
        "trace_id": secrets.token_hex(16),
        "parent_span_id": None,
        "sampled": True,
    }


def sanitize_trace_attributes(attributes: Dict[str, Any]) -> Dict[str, Any]:
    sanitized = {}
    for key, value in attributes.items():
        if key.lower() in SENSITIVE_KEYS:
            sanitized[key] = "[REDACTED]"
        else:
            sanitized[key] = value
    return sanitized


class Span:
    def __init__(
        self,
        name: str,
        trace_id: str,
        parent_span_id: Optional[str] = None,
        attributes: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.name = name
        self.trace_id = trace_id
        self.parent_span_id = parent_span_id
        self.span_id = secrets.token_hex(8)
        self.attributes = sanitize_trace_attributes(attributes or {})
        self.start_time = time.time()
        self.end_time: Optional[float] = None
        self.is_ended = False

    def end(self) -> None:
        self.end_time = time.time()
        self.is_ended = True

    def __enter__(self) -> Span:
        return self

    def __exit__(
        self,
        exc_type: Optional[type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[Any],
    ) -> None:
        if exc_val:
            self.attributes["error"] = True
            self.attributes["error.type"] = str(exc_type)
        self.end()


class TelemetryManager:
    def __init__(self, service_name: str = "campus247-api") -> None:
        self.service_name = service_name

    def start_span(
        self,
        name: str,
        trace_id: Optional[str] = None,
        parent_span_id: Optional[str] = None,
        attributes: Optional[Dict[str, Any]] = None,
    ) -> Span:
        tid = trace_id or secrets.token_hex(16)
        merged_attrs = {"service.name": self.service_name, **(attributes or {})}
        return Span(name=name, trace_id=tid, parent_span_id=parent_span_id, attributes=merged_attrs)
