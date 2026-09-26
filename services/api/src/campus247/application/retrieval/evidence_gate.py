from __future__ import annotations

from dataclasses import dataclass
import re

from campus247.application.retrieval.citations import CitationBundle


@dataclass(frozen=True)
class GroundedClaim:
    claim_id: str
    text: str
    citation_ids: tuple[str, ...]
    claim_type: str


@dataclass(frozen=True)
class GroundedDraft:
    response_text: str
    claims: tuple[GroundedClaim, ...] = ()


@dataclass(frozen=True)
class EvidenceGateResult:
    passed: bool
    unsupported_claims: tuple[str, ...] = ()
    reasons: tuple[str, ...] = ()


class EvidenceGate:
    """Verifies that all material claims have valid citations and lexical grounding in cited chunks."""

    def __init__(self, min_token_overlap_ratio: float = 0.25) -> None:
        self._min_token_overlap_ratio = min_token_overlap_ratio

    def verify(self, draft: GroundedDraft, bundle: CitationBundle) -> EvidenceGateResult:
        unsupported: list[str] = []
        reasons: list[str] = []

        for claim in draft.claims:
            # 1. Check claim has citation
            if not claim.citation_ids:
                unsupported.append(claim.claim_id)
                reasons.append(f"Claim '{claim.claim_id}' has no citations")
                continue

            # 2. Check citation IDs exist in bundle
            cited_records = []
            has_unknown_citation = False
            for cit_id in claim.citation_ids:
                rec = bundle.resolve(cit_id)
                if rec is None:
                    has_unknown_citation = True
                    unsupported.append(claim.claim_id)
                    reasons.append(f"Claim '{claim.claim_id}' references unknown citation '{cit_id}'")
                    break
                cited_records.append(rec)

            if has_unknown_citation:
                continue

            # 3. Check lexical grounding in cited content
            claim_tokens = set(t.lower() for t in re.findall(r"\w+", claim.text) if len(t) > 2)
            if not claim_tokens:
                continue

            combined_cited_text = " ".join(r.content_text.lower() for r in cited_records)
            matching_tokens = {t for t in claim_tokens if t in combined_cited_text}
            overlap_ratio = len(matching_tokens) / len(claim_tokens)

            if overlap_ratio < self._min_token_overlap_ratio:
                unsupported.append(claim.claim_id)
                reasons.append(
                    f"Claim '{claim.claim_id}' lacks grounding (overlap {overlap_ratio:.2f} < {self._min_token_overlap_ratio})"
                )

        passed = len(unsupported) == 0
        return EvidenceGateResult(
            passed=passed,
            unsupported_claims=tuple(unsupported),
            reasons=tuple(reasons),
        )
