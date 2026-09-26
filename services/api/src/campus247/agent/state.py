from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class Route(StrEnum):
    GROUNDED_FAQ = "grounded_faq"
    PERSONAL_SCHEDULE = "personal_schedule"
    TICKET_CREATE = "ticket_create"
    DOCUMENT_REQUEST = "document_request"
    ROOM_BOOKING = "room_booking"
    HUMAN_HANDOVER = "human_handover"
    SENSITIVE_CASE = "sensitive_case"
    UNSUPPORTED = "unsupported"


class Terminal(StrEnum):
    ANSWERED = "answered"
    ABSTAINED = "abstained"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    HANDED_OVER = "handed_over"
    SAFE_FAILURE = "safe_failure"


class ToolPhase(StrEnum):
    NONE = "none"
    CANDIDATE = "candidate"
    VALIDATED = "validated"
    AUTHORIZED = "authorized"
    PREVIEWED = "previewed"
    AWAITING_CONFIRMATION = "awaiting_confirmation"
    CONFIRMED = "confirmed"
    EXECUTING = "executing"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    UNCERTAIN = "uncertain"


class SafetySeverity(StrEnum):
    NORMAL = "normal"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass(frozen=True)
class NormalizedTurn:
    session_id: str
    turn_id: str
    user_id: str
    query: str
    locale: str = "vi-VN"


@dataclass(frozen=True)
class SafetyDecision:
    severity: SafetySeverity = SafetySeverity.NORMAL
    is_crisis: bool = False
    reason: str | None = None


@dataclass(frozen=True)
class RetrievalState:
    candidate_ids: tuple[str, ...] = ()
    citation_bundle_ref: str | None = None


@dataclass(frozen=True)
class DraftResponse:
    text: str
    claim_count: int = 0
    is_grounded: bool = False


@dataclass(frozen=True)
class AgentState:
    """Canonical typed agent state contract for controlled LangGraph execution."""

    request: NormalizedTurn
    schema_version: str = "1.0"
    trusted_context_ref: str | None = None
    route: Route | None = None
    safety: SafetyDecision = field(default_factory=SafetyDecision)
    retrieval: RetrievalState | None = None
    draft: DraftResponse | None = None
    tool_candidate: Any | None = None
    tool_flow: Any | None = None
    tool_phase: ToolPhase = ToolPhase.NONE
    terminal: Terminal | None = None
    errors: tuple[str, ...] = ()
    step_count: int = 0

    def __post_init__(self) -> None:
        if self.schema_version != "1.0":
            raise ValueError(f"Invalid state schema version '{self.schema_version}'. Expected '1.0'")
