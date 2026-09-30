from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


DEFAULT_ABSTENTION_MESSAGE = (
    "Campus 24/7 không thể cung cấp câu trả lời này do vi phạm chính sách an toàn hoặc thiếu minh chứng kiểm chứng."
)


@dataclass
class StreamEvent:
    seq: int
    delta: str
    metadata: Dict[str, Any] = field(default_factory=dict)


class StreamEventSequencer:
    """Deterministically rejects duplicate, reordered, or superseded stream events."""

    def __init__(self, start_seq: int = 0) -> None:
        self.last_seq = start_seq

    def accept(self, event: StreamEvent) -> bool:
        if event.seq <= self.last_seq:
            return False
        self.last_seq = event.seq
        return True


@dataclass
class StreamValidationResult:
    success: bool
    terminal_status: str
    safe_text: str
    reason: Optional[str] = None


class StreamGuardrail:
    """Buffers provisional streaming tokens, enforces sequence integrity,

    and validates content before committing final visible semantics.
    """

    def __init__(
        self,
        forbidden_substrings: Optional[List[str]] = None,
        fallback_message: str = DEFAULT_ABSTENTION_MESSAGE,
    ) -> None:
        self.sequencer = StreamEventSequencer()
        self.provisional_chunks: List[str] = []
        self.forbidden_substrings = forbidden_substrings or [
            "__internal_prompt__",
            "DROP TABLE",
            "bearer eyJ",
        ]
        self.fallback_message = fallback_message
        self.is_committed = False
        self.final_status: Optional[str] = None
        self._committed_text: Optional[str] = None

    def push_provisional(self, seq: int, delta: str, metadata: Optional[Dict[str, Any]] = None) -> bool:
        evt = StreamEvent(seq=seq, delta=delta, metadata=metadata or {})
        if not self.sequencer.accept(evt):
            return False
        self.provisional_chunks.append(delta)
        return True

    @property
    def provisional_text(self) -> str:
        return "".join(self.provisional_chunks)

    def validate_and_commit(self) -> StreamValidationResult:
        full_text = self.provisional_text
        for forbidden in self.forbidden_substrings:
            if forbidden in full_text:
                self.is_committed = False
                self.final_status = "abstained"
                self._committed_text = None
                return StreamValidationResult(
                    success=False,
                    terminal_status="abstained",
                    safe_text=self.fallback_message,
                    reason=f"Forbidden pattern detected: {forbidden}",
                )

        self.is_committed = True
        self.final_status = "completed"
        self._committed_text = full_text
        return StreamValidationResult(
            success=True,
            terminal_status="completed",
            safe_text=full_text,
        )

    def get_committed_payload(self) -> Dict[str, Any]:
        if not self.is_committed or self._committed_text is None:
            raise RuntimeError("Unvalidated or uncommitted stream tokens cannot be represented as final answer")
        return {
            "status": self.final_status,
            "text": self._committed_text,
        }
