"""Deterministic claim-to-evidence validation for grounded answers."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import StrEnum
import math
import re
from typing import Mapping


class GateDecision(StrEnum):
    GROUNDED = "grounded"
    QUALIFIED = "qualified"
    CLARIFY = "clarify"
    ABSTAIN = "abstain"


class GateReason(StrEnum):
    MISSING_CITATION = "missing_citation"
    UNKNOWN_CITATION = "unknown_citation"
    INVALID_CITATION = "invalid_citation"
    SOURCE_NOT_PUBLISHED_OR_AUTHORIZED = "source_not_published_or_authorized"
    SOURCE_INACCESSIBLE = "source_inaccessible"
    CONTRADICTORY_SOURCE = "contradictory_source"
    SOURCE_NOT_YET_EFFECTIVE = "source_not_yet_effective"
    SOURCE_EXPIRED = "source_expired"
    INVALID_EFFECTIVE_DATE = "invalid_effective_date"
    PERSONAL_DATA_SOURCE_INVALID = "personal_data_source_invalid"
    SYNTHETIC_SOURCE_REQUIRES_NOTICE = "synthetic_source_requires_notice"
    CLAIM_NOT_BOUND = "claim_not_bound"
    INVALID_SUPPORT_SCORE = "invalid_support_score"
    SUPPORT_BELOW_THRESHOLD = "support_below_threshold"
    INVALID_CLAIM = "invalid_claim"
    CLARIFICATION_REQUIRED = "clarification_required"


@dataclass(frozen=True)
class ClaimGateResult:
    claim_id: str
    supported: bool
    citation_ids: tuple[str, ...] = ()
    reason_codes: tuple[str, ...] = ()


@dataclass
class GateResult:
    decision: GateDecision
    reasons: list[str]
    claim_results: tuple[ClaimGateResult, ...] = ()


@dataclass
class Citation:
    citation_id: str
    is_published: bool
    is_authorized: bool
    effective_from: datetime | None
    effective_until: datetime | None
    has_contradiction: bool
    is_synthetic: bool
    support_score: float
    source_type: str = "RAG"  # RAG or TOOL
    is_accessible: bool = True
    supported_claim_ids: tuple[str, ...] | None = None


@dataclass
class Claim:
    claim_id: str
    text: str
    citation_ids: list[str]
    claim_type: str  # policy, procedure, deadline, fee, contact, personal_data
    is_material: bool = True
    needs_clarification: bool = False


_CLAIM_TYPES = frozenset({"policy", "procedure", "deadline", "fee", "contact", "personal_data"})
_HIGH_RISK_TYPES = frozenset({"policy", "deadline", "fee", "personal_data"})
_SAFE_IDENTIFIER = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:-]{0,63}$")


def _safe_identifier(value: object) -> str:
    """Keep diagnostics to bounded IDs; never echo arbitrary claim payloads."""
    if isinstance(value, str) and _SAFE_IDENTIFIER.fullmatch(value):
        return value
    return "redacted-id"


def _utc(value: datetime) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


class EvidenceGate:
    def __init__(
        self,
        threshold_high_risk: float = 0.95,
        threshold_normal: float = 0.90,
        qualification_threshold: float = 0.75,
    ) -> None:
        thresholds = (threshold_high_risk, threshold_normal, qualification_threshold)
        if any(not math.isfinite(value) or not 0.0 <= value <= 1.0 for value in thresholds):
            raise ValueError("Evidence thresholds must be finite values in the range 0..1")
        if qualification_threshold > threshold_normal:
            raise ValueError("qualification_threshold cannot exceed threshold_normal")

        self.threshold_high_risk = threshold_high_risk
        self.threshold_normal = threshold_normal
        self.qualification_threshold = qualification_threshold
        self.high_risk_types = _HIGH_RISK_TYPES

    def evaluate(
        self,
        claims: list[Claim],
        citation_bundle: Mapping[str, Citation],
        current_time: datetime,
        *,
        simulation_notice_present: bool = False,
    ) -> GateResult:
        """Return a deterministic decision without mutating claims or citations."""
        if not isinstance(current_time, datetime):
            raise ValueError("current_time must be a datetime")
        now = _utc(current_time)
        reasons: list[str] = []
        claim_results: list[ClaimGateResult] = []
        seen_claim_ids: set[str] = set()
        has_hard_failure = False
        needs_qualification = False
        needs_clarification = False

        for claim in claims:
            claim_id = _safe_identifier(claim.claim_id)
            claim_reason_codes: list[str] = []
            claim_has_hard_failure = False
            claim_needs_qualification = False
            claim_supported = False

            if not isinstance(claim.claim_id, str) or not claim.claim_id or claim.claim_id in seen_claim_ids:
                self._add_reason(
                    reasons,
                    claim_reason_codes,
                    GateReason.INVALID_CLAIM,
                    f"Invalid or duplicate claim ID: {claim_id}",
                )
                claim_has_hard_failure = True
            else:
                seen_claim_ids.add(claim.claim_id)

            if not claim.is_material:
                claim_results.append(
                    ClaimGateResult(
                        claim_id=claim_id,
                        supported=True,
                        citation_ids=tuple(),
                        reason_codes=("non_material_claim",),
                    )
                )
                continue

            if not isinstance(claim.claim_type, str) or claim.claim_type not in _CLAIM_TYPES:
                self._add_reason(
                    reasons,
                    claim_reason_codes,
                    GateReason.INVALID_CLAIM,
                    f"Unsupported claim type for {claim_id}",
                )
                claim_has_hard_failure = True

            if claim.needs_clarification:
                self._add_reason(
                    reasons,
                    claim_reason_codes,
                    GateReason.CLARIFICATION_REQUIRED,
                    f"Clarification required for claim {claim_id}",
                )
                needs_clarification = True

            raw_citation_ids = claim.citation_ids if isinstance(claim.citation_ids, (list, tuple)) else ()
            citation_ids = tuple(raw_citation_ids)
            if not isinstance(claim.citation_ids, (list, tuple)):
                self._add_reason(
                    reasons,
                    claim_reason_codes,
                    GateReason.INVALID_CITATION,
                    f"Invalid citation IDs for claim {claim_id}",
                )
                claim_has_hard_failure = True
            if any(not isinstance(value, str) or not value for value in citation_ids):
                self._add_reason(
                    reasons,
                    claim_reason_codes,
                    GateReason.INVALID_CITATION,
                    f"Invalid citation IDs for claim {claim_id}",
                )
                claim_has_hard_failure = True
            if not citation_ids:
                self._add_reason(
                    reasons,
                    claim_reason_codes,
                    GateReason.MISSING_CITATION,
                    f"Claim {claim_id} lacks citations.",
                )
                claim_has_hard_failure = True
            elif len({value for value in citation_ids if isinstance(value, str)}) != len(citation_ids):
                self._add_reason(
                    reasons,
                    claim_reason_codes,
                    GateReason.INVALID_CITATION,
                    f"Duplicate citation IDs for claim {claim_id}",
                )
                claim_has_hard_failure = True

            for citation_id in citation_ids:
                safe_citation_id = _safe_identifier(citation_id)
                citation = citation_bundle.get(citation_id) if isinstance(citation_id, str) else None
                if not isinstance(citation, Citation):
                    self._add_reason(
                        reasons,
                        claim_reason_codes,
                        GateReason.UNKNOWN_CITATION,
                        f"Missing citation ID: {safe_citation_id} for claim {claim_id}",
                    )
                    claim_has_hard_failure = True
                    continue

                if not citation.is_published or not citation.is_authorized:
                    self._add_reason(
                        reasons,
                        claim_reason_codes,
                        GateReason.SOURCE_NOT_PUBLISHED_OR_AUTHORIZED,
                        f"Source not published or not authorized: {safe_citation_id}",
                    )
                    claim_has_hard_failure = True

                if not citation.is_accessible:
                    self._add_reason(
                        reasons,
                        claim_reason_codes,
                        GateReason.SOURCE_INACCESSIBLE,
                        f"Source inaccessible: {safe_citation_id}",
                    )
                    claim_has_hard_failure = True

                if citation.has_contradiction:
                    self._add_reason(
                        reasons,
                        claim_reason_codes,
                        GateReason.CONTRADICTORY_SOURCE,
                        f"Unresolved contradiction in source: {safe_citation_id}",
                    )
                    claim_has_hard_failure = True

                for field_name, reason_code, message in (
                    (
                        "effective_from",
                        GateReason.SOURCE_NOT_YET_EFFECTIVE,
                        f"Source not yet effective: {safe_citation_id}",
                    ),
                    (
                        "effective_until",
                        GateReason.SOURCE_EXPIRED,
                        f"Source expired: {safe_citation_id}",
                    ),
                ):
                    date_value = getattr(citation, field_name)
                    if date_value is None:
                        continue
                    if not isinstance(date_value, datetime):
                        self._add_reason(
                            reasons,
                            claim_reason_codes,
                            GateReason.INVALID_EFFECTIVE_DATE,
                            f"Invalid effective date: {safe_citation_id}",
                        )
                        claim_has_hard_failure = True
                        continue
                    normalized_date = _utc(date_value)
                    if field_name == "effective_from" and normalized_date > now:
                        self._add_reason(reasons, claim_reason_codes, reason_code, message)
                        claim_has_hard_failure = True
                    elif field_name == "effective_until" and normalized_date < now:
                        self._add_reason(reasons, claim_reason_codes, reason_code, message)
                        claim_has_hard_failure = True

                if claim.claim_type == "personal_data" and (
                    not isinstance(citation.source_type, str) or citation.source_type.upper() != "TOOL"
                ):
                    self._add_reason(
                        reasons,
                        claim_reason_codes,
                        GateReason.PERSONAL_DATA_SOURCE_INVALID,
                        f"Personal data must come from Tool, not RAG: {safe_citation_id}",
                    )
                    claim_has_hard_failure = True

                if citation.is_synthetic and not simulation_notice_present:
                    self._add_reason(
                        reasons,
                        claim_reason_codes,
                        GateReason.SYNTHETIC_SOURCE_REQUIRES_NOTICE,
                        f"Synthetic source requires a simulation notice: {safe_citation_id}",
                    )
                    claim_has_hard_failure = True

                if citation.supported_claim_ids is not None and claim.claim_id not in citation.supported_claim_ids:
                    self._add_reason(
                        reasons,
                        claim_reason_codes,
                        GateReason.CLAIM_NOT_BOUND,
                        f"Citation is not bound to claim {claim_id}: {safe_citation_id}",
                    )
                    claim_has_hard_failure = True

                score = citation.support_score
                required_threshold = (
                    self.threshold_high_risk
                    if claim.claim_type in self.high_risk_types
                    else self.threshold_normal
                )
                if not isinstance(score, (int, float)) or isinstance(score, bool) or not math.isfinite(score):
                    self._add_reason(
                        reasons,
                        claim_reason_codes,
                        GateReason.INVALID_SUPPORT_SCORE,
                        f"Invalid support score: {safe_citation_id}",
                    )
                    claim_has_hard_failure = True
                elif score < 0.0 or score > 1.0:
                    self._add_reason(
                        reasons,
                        claim_reason_codes,
                        GateReason.INVALID_SUPPORT_SCORE,
                        f"Invalid support score: {safe_citation_id}",
                    )
                    claim_has_hard_failure = True
                elif score < required_threshold:
                    self._add_reason(
                        reasons,
                        claim_reason_codes,
                        GateReason.SUPPORT_BELOW_THRESHOLD,
                        f"Insufficient support score ({score} < {required_threshold}) for {safe_citation_id}",
                    )
                    if claim.claim_type in self.high_risk_types or score < self.qualification_threshold:
                        claim_has_hard_failure = True
                    else:
                        claim_needs_qualification = True

            claim_supported = bool(citation_ids) and not claim_has_hard_failure and not claim_needs_qualification
            if claim_has_hard_failure:
                has_hard_failure = True
            if claim_needs_qualification:
                needs_qualification = True
            claim_results.append(
                ClaimGateResult(
                    claim_id=claim_id,
                    supported=claim_supported,
                    citation_ids=tuple(_safe_identifier(value) for value in citation_ids),
                    reason_codes=tuple(claim_reason_codes),
                )
            )

        if has_hard_failure:
            decision = GateDecision.ABSTAIN
        elif needs_clarification:
            decision = GateDecision.CLARIFY
        elif needs_qualification:
            decision = GateDecision.QUALIFIED
        else:
            decision = GateDecision.GROUNDED
        return GateResult(decision=decision, reasons=reasons, claim_results=tuple(claim_results))

    @staticmethod
    def _add_reason(
        reasons: list[str],
        reason_codes: list[str],
        code: GateReason,
        message: str,
    ) -> None:
        reasons.append(message)
        reason_codes.append(code.value)
