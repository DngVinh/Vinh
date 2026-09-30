from __future__ import annotations

import pytest
from campus247.agent.streaming import (
    StreamGuardrail,
    StreamValidationResult,
    StreamEventSequencer,
    StreamEvent,
)


def test_duplicate_or_reordered_events_ignored():
    sequencer = StreamEventSequencer()
    events = [
        StreamEvent(seq=1, delta="Xin "),
        StreamEvent(seq=2, delta="chào "),
        StreamEvent(seq=2, delta="chào trùng "),  # Duplicate seq
        StreamEvent(seq=1, delta="reordered "),   # Out of order
        StreamEvent(seq=3, delta="bạn."),
    ]
    accepted_deltas = []
    for evt in events:
        if sequencer.accept(evt):
            accepted_deltas.append(evt.delta)

    assert accepted_deltas == ["Xin ", "chào ", "bạn."]
    assert sequencer.last_seq == 3


def test_unvalidated_tokens_never_marked_complete():
    guardrail = StreamGuardrail()
    # Feed provisional chunks
    guardrail.push_provisional(seq=1, delta="Đang phân tích...")
    guardrail.push_provisional(seq=2, delta=" Thông tin học bổng.")

    # Status before terminal validation must remain uncommitted / provisional
    assert not guardrail.is_committed
    assert guardrail.final_status is None
    # Cannot get completed payload before commit
    with pytest.raises(RuntimeError, match="Unvalidated"):
        guardrail.get_committed_payload()


def test_late_failure_replaces_provisional_with_safe_abstention():
    guardrail = StreamGuardrail(
        forbidden_substrings=["INJECTION_PAYLOAD", "LEAK_SECRET"]
    )
    guardrail.push_provisional(seq=1, delta="Thông thường sinh viên cần...")
    guardrail.push_provisional(seq=2, delta=" INJECTION_PAYLOAD: lộ dữ liệu")

    # Late validation check
    validation = guardrail.validate_and_commit()
    assert validation.success is False
    assert validation.terminal_status == "abstained"
    assert "INJECTION_PAYLOAD" not in validation.safe_text
    assert "chính sách an toàn" in validation.safe_text
    assert guardrail.is_committed is False


def test_stream_successful_commit():
    guardrail = StreamGuardrail()
    guardrail.push_provisional(seq=1, delta="Lịch học kỳ này ")
    guardrail.push_provisional(seq=2, delta="bắt đầu vào thứ Hai.")

    validation = guardrail.validate_and_commit()
    assert validation.success is True
    assert validation.terminal_status == "completed"
    assert validation.safe_text == "Lịch học kỳ này bắt đầu vào thứ Hai."
    assert guardrail.is_committed is True
    assert guardrail.get_committed_payload()["text"] == "Lịch học kỳ này bắt đầu vào thứ Hai."
