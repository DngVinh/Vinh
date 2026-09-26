from __future__ import annotations

from pathlib import Path
import sys
import pytest

ROOT = Path(__file__).resolve().parents[3]
API_SRC = ROOT / "services" / "api" / "src"
if str(API_SRC) not in sys.path:
    sys.path.insert(0, str(API_SRC))

from campus247.agent.nodes.retrieve import RetrieveEvidenceNode
from campus247.agent.state import (
    AgentState,
    NormalizedTurn,
    Route,
    Terminal,
)


def make_state(query: str, route: Route = Route.GROUNDED_FAQ) -> AgentState:
    return AgentState(
        request=NormalizedTurn(session_id="s1", turn_id="t1", user_id="u1", query=query),
        route=route,
    )


def test_retrieve_node_success_with_candidates() -> None:
    chunks = [
        {
            "chunk_id": "c1",
            "source_id": "s1",
            "document_version_id": "v1",
            "title": "Học phí",
            "content_text": "Mức học phí là 480.000 VNĐ.",
        }
    ]
    node = RetrieveEvidenceNode(search_fn=lambda query: chunks)
    state = make_state("Học phí")
    next_state = node.execute(state)

    assert next_state.retrieval is not None
    assert next_state.retrieval.candidate_ids == ("c1",)
    assert next_state.terminal is None


def test_retrieve_node_abstains_when_no_candidates() -> None:
    node = RetrieveEvidenceNode(search_fn=lambda query: [])
    state = make_state("Không có tài liệu nào về việc này")
    next_state = node.execute(state)

    assert next_state.terminal == Terminal.ABSTAINED
    assert next_state.draft is not None
    assert "chưa tìm thấy tài liệu" in next_state.draft.text
