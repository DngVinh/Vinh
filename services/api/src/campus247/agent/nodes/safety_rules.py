from __future__ import annotations

import re
import unicodedata

from campus247.agent.state import SafetyDecision, SafetySeverity


_CRITICAL_RULES: tuple[tuple[str, str], ...] = (
    (
        "self_harm_imminent",
        r"(?:\btu\s*(?:tu|sat)\b|\bmuon\s*chet\b|\bkhong\s*muon\s*song\b|"
        r"\bnhay\s+(?:lau|tu\s+tang|xuong)\b|\bcat\s+(?:co|tay)\b|"
        r"\buong\s+thuoc\s+ngu\b|\bket\s*lieu\b)",
    ),
    (
        "violence_imminent",
        r"(?:\b(?:dam|giet)\s+(?:chet|nguoi)\b|\b(?:mang|vac|cam)\s+(?:dao|sung|bom)\b|"
        r"\b(?:dat|danh)\s+bom\b|\bdot\s+(?:truong|phong|nguoi)\b|"
        r"\b(?:dao|sung)\b.{0,60}\b(?:xu|giet|dam|tan\s*cong)\b)",
    ),
    (
        "medical_emergency",
        r"(?:\bngat\s*xiu\b|\bco\s*giat\b|\bkho\s*tho\b|\bdot\s*quy\b|"
        r"\bngung\s*tim\b|\bbat\s*tinh\b|\bdau\s*nguc\b.{0,40}\b(?:kho\s*tho|ngat)\b)",
    ),
)

_HIGH_RULES: tuple[tuple[str, str], ...] = (
    (
        "harassment_or_abuse",
        r"(?:\bquay\s*roi\b|\bxam\s*hai\b|\bbat\s*nat\b|\bboc\s*phot\b|\bdim\s*chet\b|"
        r"\bga\s*tinh\b|\bxin\s*so\s*do\b|\bvo\s*tich\s*su\b|\blam\s*an\s*nhu\s*hac\b|"
        r"\bday\s*dot\s*nhu\s*bo\b|\bcut\s*ve\s*que\b|\blam\s*ban\s*truong\b|\bde\s*doa\b)",
    ),
    (
        "disciplinary_or_legal",
        r"(?:\bto\s*cao\b|\bnhan\s*tien\s*chay\s*diem\b|\bchay\s*diem\b|"
        r"\bkhieu\s*nai\b.{0,40}\bky\s*luat\b|\bbi\s*dinh\s*chi\b)",
    ),
    (
        "academic_rights_impact",
        r"(?:\bdoi\s*diem\b|\bmat\s*quyen\b|\bngoai\s*le\b.{0,40}\bdeadline\b|"
        r"\bgia\s*han\b.{0,40}\bdeadline\b|\bcam\s*thi\b|\btu\s*choi\b.{0,40}\bhoc\s*bong\b)",
    ),
    (
        "privacy_or_security_incident",
        r"(?:\bphishing\b|\bbi\s*hack\b|\blo\s*(?:mat\s*khau|thong\s*tin|tai\s*khoan)\b|"
        r"\bbi\s*danh\s*cap\b.{0,30}\btai\s*khoan\b|\bgui\b.{0,20}\bmat\s*khau\b)",
    ),
    (
        "financial_impact",
        r"(?:\bhoan\s*tien\b|\bmien\s*giam\s*hoc\s*phi\b|\bno\s*hoc\s*phi\b.{0,30}\bbi\b|"
        r"\btang\s*hoc\s*phi\b.{0,30}\bvo\s*ly\b|\bkhong\s*du\s*tien\b.{0,30}\bhoc\b)",
    ),
    (
        "mental_health_distress",
        r"(?:\bkhong\s*chiu\s*noi\b|\bsuy\s*sup\b|\bhoang\s*loan\b|\bap\s*luc\b.{0,30}\bkhong\s*ngu\b|"
        r"\bstress\b.{0,30}\bkhong\s*on\b)",
    ),
)

_PROMPT_INJECTION_RULE = re.compile(
    r"(?:\bignore\s+previous\s+instructions\b|\bsystem\s+prompt\b|"
    r"\bbo\s*qua\s*(?:cac\s*)?chi\s*thi\s*truoc\b|\btiet\s*lo\b.{0,30}\bhuong\s*dan\s*he\s*thong\b)"
)


def _normalize(text: str) -> str:
    decomposed = unicodedata.normalize("NFD", text.lower().replace("đ", "d"))
    without_marks = "".join(char for char in decomposed if unicodedata.category(char) != "Mn")
    return " ".join(without_marks.split())


def _decision(severity: SafetySeverity, reason: str | None, *, crisis: bool = False) -> SafetyDecision:
    return SafetyDecision(severity=severity, is_crisis=crisis, reason=reason)


def evaluate_deterministic_safety(query_text: str) -> SafetyDecision:
    """Apply bounded, ordered safety rules without side effects or external calls."""
    if not isinstance(query_text, str):
        return _decision(SafetySeverity.NORMAL, None)

    text = _normalize(query_text)
    for reason, pattern in _CRITICAL_RULES:
        if re.search(pattern, text):
            return _decision(SafetySeverity.CRITICAL, reason, crisis=True)

    for reason, pattern in _HIGH_RULES:
        if re.search(pattern, text):
            return _decision(SafetySeverity.HIGH, reason)

    if _PROMPT_INJECTION_RULE.search(text):
        benign_academic_context = any(
            marker in text
            for marker in ("hoc lai", "hoc bong", "quy dinh", "thu tuc", "hoc phi", "mon hoc")
        )
        if benign_academic_context:
            return _decision(SafetySeverity.NORMAL, "prompt_injection_signal_benign_inquiry")
        return _decision(SafetySeverity.HIGH, "prompt_injection_signal")

    return _decision(SafetySeverity.NORMAL, None)
