from __future__ import annotations

import re
from campus247.agent.state import SafetyDecision, SafetySeverity

CRITICAL_SELF_HARM_PATTERNS = [
    r"tự\s*tử",
    r"tự\s*sát",
    r"muốn\s*chết",
    r"cắt\s*cổ\s*tay",
    r"nhảy\s*lầu",
    r"uống\s*thuốc\s*ngủ",
    r"kết\s*liễu",
]

CRITICAL_VIOLENCE_PATTERNS = [
    r"đâm\s*chết",
    r"giết\s*người",
    r"mang\s*súng",
    r"đặt\s*bom",
    r"đốt\s*trường",
]

CRITICAL_MEDICAL_PATTERNS = [
    r"ngất\s*xỉu",
    r"co\s*giật",
    r"khó\s*thở",
    r"đột\s*quỵ",
    r"ngừng\s*tim",
]

HIGH_PROMPT_INJECTION_PATTERNS = [
    r"ignore\s+previous\s+instructions",
    r"system\s+prompt",
    r"bỏ\s*qua\s*(các\s*)?chỉ\s*thị\s*trước",
    r"tiết\s*lộ\s*hướng\s*dẫn\s*hệ\s*thống",
]


def evaluate_deterministic_safety(query_text: str) -> SafetyDecision:
    """Evaluates input query against deterministic critical/high safety rules."""
    text = query_text.lower().strip()

    for pattern in CRITICAL_SELF_HARM_PATTERNS:
        if re.search(pattern, text):
            return SafetyDecision(
                severity=SafetySeverity.CRITICAL,
                is_crisis=True,
                reason="self_harm_imminent",
            )

    for pattern in CRITICAL_VIOLENCE_PATTERNS:
        if re.search(pattern, text):
            return SafetyDecision(
                severity=SafetySeverity.CRITICAL,
                is_crisis=True,
                reason="violence_imminent",
            )

    for pattern in CRITICAL_MEDICAL_PATTERNS:
        if re.search(pattern, text):
            return SafetyDecision(
                severity=SafetySeverity.CRITICAL,
                is_crisis=True,
                reason="medical_emergency",
            )

    for pattern in HIGH_PROMPT_INJECTION_PATTERNS:
        if re.search(pattern, text):
            if any(kw in text for kw in ["học lại", "học bổng", "quy định", "thủ tục", "học phí"]):
                return SafetyDecision(
                    severity=SafetySeverity.LOW,
                    is_crisis=False,
                    reason="prompt_injection_signal_benign_inquiry",
                )
            return SafetyDecision(
                severity=SafetySeverity.HIGH,
                is_crisis=False,
                reason="prompt_injection_signal",
            )

    return SafetyDecision(
        severity=SafetySeverity.NORMAL,
        is_crisis=False,
        reason=None,
    )
