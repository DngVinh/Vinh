from __future__ import annotations

from pathlib import Path
import sys
import pytest

ROOT = Path(__file__).resolve().parents[3]
API_SRC = ROOT / "services" / "api" / "src"
if str(API_SRC) not in sys.path:
    sys.path.insert(0, str(API_SRC))

from campus247.agent.nodes.compose import ComposeGroundedNode, OutputGuardNode
from campus247.agent.state import (
    AgentState,
    DraftResponse,
    NormalizedTurn,
    Route,
    Terminal,
)
from campus247.application.retrieval.citations import CitationBundle


@pytest.fixture
def sample_bundle() -> CitationBundle:
    return CitationBundle.build(
        [
            {
                "chunk_id": "c1",
                "source_id": "s1",
                "document_version_id": "v1",
                "title": "Học phí",
                "content_text": "Mức học phí là 480.000 VNĐ một tín chỉ.",
            }
        ]
    )


def test_compose_grounded_node_creates_draft(sample_bundle: CitationBundle) -> None:
    composer = ComposeGroundedNode()
    state = AgentState(
        request=NormalizedTurn(session_id="s1", turn_id="t1", user_id="u1", query="Học phí?"),
        route=Route.GROUNDED_FAQ,
    )
    next_state = composer.execute(state, bundle=sample_bundle)
    assert next_state.draft is not None
    assert "[CIT-001]" in next_state.draft.text
    assert next_state.draft.is_grounded is True


def test_output_guard_passes_clean_draft() -> None:
    guard = OutputGuardNode()
    state = AgentState(
        request=NormalizedTurn(session_id="s1", turn_id="t1", user_id="u1", query="Học phí?"),
        draft=DraftResponse(text="Mức học phí là 480.000 VNĐ [CIT-001].", is_grounded=True, gate_decision="grounded"),
    )
    final_state = guard.execute(state)
    assert final_state.terminal == Terminal.ANSWERED
    assert "480.000 VNĐ" in final_state.draft.text


def test_output_guard_blocks_secret_leakage() -> None:
    guard = OutputGuardNode()
    state = AgentState(
        request=NormalizedTurn(session_id="s1", turn_id="t1", user_id="u1", query="Secret?"),
        draft=DraftResponse(
            text="Hệ thống có secret_token: sk-live-1234567890abcdef12345678",
            is_grounded=True,
        ),
    )
    final_state = guard.execute(state)
    assert final_state.terminal == Terminal.SAFE_FAILURE
    assert "sk-live" not in final_state.draft.text


def test_output_guard_blocks_policy_violations() -> None:
    from campus247.agent.nodes.compose import OutputGuardNode
    guard = OutputGuardNode()
    
    # Test diagnostic/legal claim
    state = AgentState(
        request=NormalizedTurn(session_id="s1", turn_id="t1", user_id="u1", query="Bệnh?"),
        draft=DraftResponse(
            text="Bạn đã được chẩn đoán mắc bệnh nghiêm trọng.",
            is_grounded=True,
        ),
    )
    final_state = guard.execute(state)
    assert final_state.terminal == Terminal.SAFE_FAILURE
    assert "chẩn đoán" not in final_state.draft.text

    # Test false delivery promise
    state2 = AgentState(
        request=NormalizedTurn(session_id="s2", turn_id="t2", user_id="u2", query="Giúp?"),
        draft=DraftResponse(
            text="Hệ thống đã gọi cấp cứu thành công.",
            is_grounded=True,
        ),
    )
    final_state2 = guard.execute(state2)
    assert final_state2.terminal == Terminal.SAFE_FAILURE
    assert "thành công" not in final_state2.draft.text
