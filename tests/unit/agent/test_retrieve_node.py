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
    assert next_state.step_count == 1


def test_retrieve_node_abstains_when_no_candidates() -> None:
    node = RetrieveEvidenceNode(search_fn=lambda query: [])
    state = make_state("Không có tài liệu nào về việc này")
    next_state = node.execute(state)

    assert next_state.terminal == Terminal.ABSTAINED
    assert next_state.draft is not None
    assert "chưa tìm thấy tài liệu" in next_state.draft.text


def test_retrieve_node_bounds_candidates_and_deduplicates() -> None:
    chunks = [{"chunk_id": f"c{i}"} for i in range(40)] + [{"chunk_id": "c0"}]
    node = RetrieveEvidenceNode(search_fn=lambda query: chunks)

    next_state = node.execute(make_state("quy định học vụ"))

    assert next_state.retrieval is not None
    assert len(next_state.retrieval.candidate_ids) == 30
    assert next_state.retrieval.candidate_ids[-1] == "c29"


def test_retrieve_node_abstains_for_ineligible_candidates() -> None:
    chunks = [
        {"chunk_id": "draft", "status": "DRAFT"},
        {"chunk_id": "unauthorized", "is_authorized": False},
        {"chunk_id": "expired", "is_effective": False},
        {"title": "missing chunk id"},
    ]
    node = RetrieveEvidenceNode(search_fn=lambda query: chunks)

    next_state = node.execute(make_state("quy định học vụ"))

    assert next_state.terminal == Terminal.ABSTAINED
    assert next_state.retrieval is not None
    assert next_state.retrieval.candidate_ids == ()
    assert next_state.errors[-1] == "AI_RETRIEVAL_INSUFFICIENT"


def test_retrieve_node_provider_failure_abstains_without_leaking_error() -> None:
    secret_error = "provider-secret-and-private-detail"

    def failing_search(query: str) -> list[dict[str, str]]:
        raise RuntimeError(secret_error)

    next_state = RetrieveEvidenceNode(search_fn=failing_search).execute(make_state("quy định học vụ"))

    assert next_state.terminal == Terminal.ABSTAINED
    assert next_state.errors[-1] == "AI_RETRIEVAL_UNAVAILABLE"
    assert secret_error not in next_state.draft.text


def test_retrieve_evidence_node_detects_metadata_conflict() -> None:
    from campus247.agent.nodes.definitions import retrieve_evidence_node
    chunks = [
        {
            "chunk_id": "c1",
            "source_id": "doc_123",
            "document_version_id": "v1",
            "content_text": "Rules v1",
        },
        {
            "chunk_id": "c2",
            "source_id": "doc_123",
            "document_version_id": "v2",
            "content_text": "Rules v2",
        }
    ]
    state = make_state("Quy định học vụ")
    next_state = retrieve_evidence_node(state, search_fn=lambda q: chunks)
    
    assert next_state.terminal == Terminal.ABSTAINED
    assert next_state.retrieval.citation_bundle_ref == "bundle_conflicting"
    assert "mâu thuẫn" in next_state.draft.text
