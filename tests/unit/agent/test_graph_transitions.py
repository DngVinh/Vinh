from __future__ import annotations

from pathlib import Path
import sys
import pytest

ROOT = Path(__file__).resolve().parents[3]
API_SRC = ROOT / "services" / "api" / "src"
if str(API_SRC) not in sys.path:
    sys.path.insert(0, str(API_SRC))

from campus247.agent.graph import CampusAgentWorkflow
from campus247.agent.state import (
    AgentState,
    NormalizedTurn,
    Route,
    SafetySeverity,
    Terminal,
)


def test_workflow_runs_faq_to_answered() -> None:
    knowledge_db = {
        "học phí": [
            {
                "chunk_id": "c1",
                "source_id": "s1",
                "document_version_id": "v1",
                "title": "Học phí",
                "content_text": "Mức học phí là 480.000 VNĐ.",
            }
        ]
    }
    workflow = CampusAgentWorkflow(search_fn=lambda q: knowledge_db.get("học phí", []))

    turn = NormalizedTurn(
        session_id="s1",
        turn_id="t1",
        user_id="u1",
        query="Học phí HUCE là bao nhiêu?",
    )
    final_state = workflow.run(turn)

    assert final_state.route == Route.GROUNDED_FAQ
    assert final_state.terminal == Terminal.ANSWERED
    assert final_state.draft is not None
    assert "480.000 VNĐ" in final_state.draft.text


def test_workflow_runs_crisis_to_handed_over() -> None:
    workflow = CampusAgentWorkflow(search_fn=lambda q: [])
    turn = NormalizedTurn(
        session_id="s1",
        turn_id="t2",
        user_id="u1",
        query="Tôi muốn tự tử nhảy lầu",
    )
    final_state = workflow.run(turn)

    assert final_state.safety.severity == SafetySeverity.CRITICAL
    assert final_state.route == Route.SENSITIVE_CASE
    assert final_state.terminal == Terminal.HANDED_OVER
    assert "khẩn cấp" in (final_state.draft.text if final_state.draft else "")


def test_workflow_runs_unknown_faq_to_abstained() -> None:
    workflow = CampusAgentWorkflow(search_fn=lambda q: [])
    turn = NormalizedTurn(
        session_id="s1",
        turn_id="t3",
        user_id="u1",
        query="Quy định xây dựng đường tàu vũ trụ",
    )
    final_state = workflow.run(turn)

    assert final_state.terminal == Terminal.ABSTAINED
    assert "chưa tìm thấy tài liệu" in (final_state.draft.text if final_state.draft else "")
