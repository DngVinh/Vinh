"""Tests for the deterministic evidence gate."""
from __future__ import annotations

from datetime import datetime, timezone

import pytest

from campus247.agent.grounding.evidence_gate import (
    Citation,
    Claim,
    EvidenceGate,
    GateDecision,
)


def create_valid_citation(cit_id: str) -> Citation:
    return Citation(
        citation_id=cit_id,
        is_published=True,
        is_authorized=True,
        effective_from=None,
        effective_until=None,
        has_contradiction=False,
        is_synthetic=False,
        support_score=0.98,
        source_type="RAG",
    )


def test_gate_allows_fully_supported_claims():
    gate = EvidenceGate(threshold_high_risk=0.95, threshold_normal=0.90)
    bundle = {"CIT-001": create_valid_citation("CIT-001")}
    claims = [
        Claim(
            claim_id="CLM-1",
            text="Deadline is tomorrow",
            citation_ids=["CIT-001"],
            claim_type="deadline",
        )
    ]
    
    result = gate.evaluate(claims, bundle, current_time=datetime.now(timezone.utc))
    assert result.decision == GateDecision.GROUNDED
    assert not result.reasons


def test_gate_abstains_if_missing_citation():
    gate = EvidenceGate()
    bundle = {}
    claims = [
        Claim(
            claim_id="CLM-1",
            text="Fee is 500k",
            citation_ids=["CIT-MISSING"],
            claim_type="fee",
        )
    ]
    
    result = gate.evaluate(claims, bundle, current_time=datetime.now(timezone.utc))
    assert result.decision == GateDecision.ABSTAIN
    assert "Missing citation ID: CIT-MISSING" in result.reasons[0]


def test_gate_abstains_if_stale_or_unpublished():
    gate = EvidenceGate()
    cit = create_valid_citation("CIT-001")
    cit.is_published = False
    
    result = gate.evaluate(
        [Claim("CLM-1", "text", ["CIT-001"], "policy")],
        {"CIT-001": cit},
        datetime.now(timezone.utc)
    )
    assert result.decision == GateDecision.ABSTAIN
    assert "Source not published or not authorized" in result.reasons[0]


def test_gate_abstains_on_contradiction():
    gate = EvidenceGate()
    cit = create_valid_citation("CIT-001")
    cit.has_contradiction = True
    
    result = gate.evaluate(
        [Claim("CLM-1", "text", ["CIT-001"], "policy")],
        {"CIT-001": cit},
        datetime.now(timezone.utc)
    )
    assert result.decision == GateDecision.ABSTAIN
    assert "Unresolved contradiction" in result.reasons[0]


def test_gate_abstains_if_score_below_threshold():
    gate = EvidenceGate(threshold_high_risk=0.95, threshold_normal=0.85)
    cit = create_valid_citation("CIT-001")
    cit.support_score = 0.90  # below 0.95 required for deadline
    
    result = gate.evaluate(
        [Claim("CLM-1", "text", ["CIT-001"], "deadline")],
        {"CIT-001": cit},
        datetime.now(timezone.utc)
    )
    assert result.decision == GateDecision.ABSTAIN
    assert "Insufficient support score" in result.reasons[0]


def test_gate_requires_tool_source_for_personal_data():
    gate = EvidenceGate()
    cit = create_valid_citation("CIT-001")
    cit.source_type = "RAG"  # Must be TOOL
    
    result = gate.evaluate(
        [Claim("CLM-1", "text", ["CIT-001"], "personal_data")],
        {"CIT-001": cit},
        datetime.now(timezone.utc)
    )
    assert result.decision == GateDecision.ABSTAIN
    assert "Personal data must come from Tool" in result.reasons[0]


def test_gate_rejects_inaccessible_citation_and_reports_claim_result():
    gate = EvidenceGate()
    cit = create_valid_citation("CIT-001")
    cit.is_accessible = False

    result = gate.evaluate(
        [Claim("CLM-1", "text", ["CIT-001"], "procedure")],
        {"CIT-001": cit},
        datetime.now(timezone.utc),
    )

    assert result.decision == GateDecision.ABSTAIN
    assert "Source inaccessible" in result.reasons[0]
    assert result.claim_results[0].supported is False
    assert result.claim_results[0].reason_codes == ("source_inaccessible",)


def test_gate_rejects_citation_not_bound_to_claim():
    gate = EvidenceGate()
    cit = create_valid_citation("CIT-001")
    cit.supported_claim_ids = ("CLM-OTHER",)

    result = gate.evaluate(
        [Claim("CLM-1", "text", ["CIT-001"], "procedure")],
        {"CIT-001": cit},
        datetime.now(timezone.utc),
    )

    assert result.decision == GateDecision.ABSTAIN
    assert "not bound to claim" in result.reasons[0]


def test_gate_qualifies_low_confidence_normal_claim_without_grounding_it():
    gate = EvidenceGate(threshold_normal=0.90, qualification_threshold=0.75)
    cit = create_valid_citation("CIT-001")
    cit.support_score = 0.80

    result = gate.evaluate(
        [Claim("CLM-1", "text", ["CIT-001"], "procedure")],
        {"CIT-001": cit},
        datetime.now(timezone.utc),
    )

    assert result.decision == GateDecision.QUALIFIED
    assert result.claim_results[0].supported is False
    assert "Insufficient support score" in result.reasons[0]


def test_gate_clarifies_explicitly_ambiguous_claim():
    gate = EvidenceGate()
    result = gate.evaluate(
        [Claim("CLM-1", "text", ["CIT-001"], "procedure", needs_clarification=True)],
        {"CIT-001": create_valid_citation("CIT-001")},
        datetime.now(timezone.utc),
    )

    assert result.decision == GateDecision.CLARIFY
    assert result.claim_results[0].supported is True
    assert "Clarification required" in result.reasons[0]


def test_gate_is_deterministic_and_does_not_echo_claim_payload():
    gate = EvidenceGate()
    secret_text = "secret_token=do-not-include-in-evidence"
    claims = [Claim("CLM-1", secret_text, ["CIT-001"], "procedure")]
    bundle = {"CIT-001": create_valid_citation("CIT-001")}
    now = datetime(2026, 9, 28, tzinfo=timezone.utc)

    first = gate.evaluate(claims, bundle, now)
    second = gate.evaluate(claims, bundle, now)

    assert first == second
    assert all(secret_text not in reason for reason in first.reasons)


def test_evidence_gate_node_rejects_unsupported() -> None:
    from campus247.agent.nodes.definitions import evidence_gate_node
    from campus247.agent.state import AgentState, NormalizedTurn, ToolFlowState, DraftResponse, Terminal
    
    candidates = [{"chunk_id": "c1", "content_text": "Rules v1", "source_id": "doc_123"}]
    flow = ToolFlowState(candidates=candidates)
    
    # Missing citations
    state = AgentState(
        request=NormalizedTurn(session_id="s", turn_id="t", user_id="u", query="q"),
        tool_flow=flow,
        draft=DraftResponse(text="Mức học phí là 10.000.", is_grounded=True)
    )
    next_state = evidence_gate_node(state)
    assert next_state.terminal == Terminal.ABSTAINED
    assert "EVIDENCE_GATE_REJECTED" in next_state.errors
    
    # Wrong citation
    state2 = AgentState(
        request=NormalizedTurn(session_id="s", turn_id="t", user_id="u", query="q"),
        tool_flow=flow,
        draft=DraftResponse(text="Mức học phí là 10.000 [CIT-999].", is_grounded=True)
    )
    next_state2 = evidence_gate_node(state2)
    assert next_state2.terminal == Terminal.ABSTAINED
    assert "EVIDENCE_GATE_REJECTED" in next_state2.errors
