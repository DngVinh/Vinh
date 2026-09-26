from __future__ import annotations

from pathlib import Path
import sys
import pytest

ROOT = Path(__file__).resolve().parents[3]
API_SRC = ROOT / "services" / "api" / "src"
if str(API_SRC) not in sys.path:
    sys.path.insert(0, str(API_SRC))

from campus247.application.retrieval.citations import CitationBundle
from campus247.application.retrieval.evidence_gate import (
    EvidenceGate,
    EvidenceGateResult,
    GroundedClaim,
    GroundedDraft,
)


@pytest.fixture
def sample_bundle() -> CitationBundle:
    return CitationBundle.build(
        [
            {
                "chunk_id": "chunk_1",
                "source_id": "src_1",
                "document_version_id": "ver_1",
                "title": "Học phí",
                "content_text": "Mức học phí đại học chính quy là 480.000 VNĐ một tín chỉ.",
            }
        ]
    )


def test_evidence_gate_passes_grounded_claim(sample_bundle: CitationBundle) -> None:
    gate = EvidenceGate()
    draft = GroundedDraft(
        response_text="Học phí là 480.000 VNĐ mỗi tín chỉ [CIT-001].",
        claims=(
            GroundedClaim(
                claim_id="CLM-001",
                text="Học phí là 480.000 VNĐ một tín chỉ",
                citation_ids=("CIT-001",),
                claim_type="fee",
            ),
        ),
    )

    res = gate.verify(draft, bundle=sample_bundle)
    assert isinstance(res, EvidenceGateResult)
    assert res.passed is True
    assert len(res.unsupported_claims) == 0


def test_evidence_gate_fails_uncited_claim(sample_bundle: CitationBundle) -> None:
    gate = EvidenceGate()
    draft = GroundedDraft(
        response_text="Học phí là 480.000 VNĐ.",
        claims=(
            GroundedClaim(
                claim_id="CLM-001",
                text="Học phí là 480.000 VNĐ",
                citation_ids=(),  # Missing citation
                claim_type="fee",
            ),
        ),
    )

    res = gate.verify(draft, bundle=sample_bundle)
    assert res.passed is False
    assert "CLM-001" in res.unsupported_claims


def test_evidence_gate_fails_hallucinated_citation(sample_bundle: CitationBundle) -> None:
    gate = EvidenceGate()
    draft = GroundedDraft(
        response_text="Test",
        claims=(
            GroundedClaim(
                claim_id="CLM-001",
                text="Học phí 480.000",
                citation_ids=("CIT-999",),  # Not in bundle
                claim_type="fee",
            ),
        ),
    )

    res = gate.verify(draft, bundle=sample_bundle)
    assert res.passed is False
    assert "CLM-001" in res.unsupported_claims


def test_evidence_gate_fails_unsupported_content(sample_bundle: CitationBundle) -> None:
    gate = EvidenceGate()
    # Claim text has zero overlap with "Học phí đại học..." chunk
    draft = GroundedDraft(
        response_text="Sinh viên được cấp xe máy miễn phí",
        claims=(
            GroundedClaim(
                claim_id="CLM-002",
                text="Sinh viên được tặng xe ô tô điện VinFast miễn phí",
                citation_ids=("CIT-001",),
                claim_type="policy",
            ),
        ),
    )

    res = gate.verify(draft, bundle=sample_bundle)
    assert res.passed is False
    assert "CLM-002" in res.unsupported_claims
