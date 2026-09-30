from __future__ import annotations

import base64
import binascii
from dataclasses import dataclass
from enum import StrEnum
import html
import re
import unicodedata
from urllib.parse import unquote

try:
    from campus247.agent.prompts.composer import TrustDomain
except (ImportError, ModuleNotFoundError):
    import importlib.util
    from pathlib import Path
    _c_path = Path(__file__).resolve().parents[1] / "prompts" / "composer.py"
    _spec = importlib.util.spec_from_file_location("campus247.agent.prompts.composer", _c_path)
    _mod = importlib.util.module_from_spec(_spec)
    _spec.loader.exec_module(_mod)
    TrustDomain = _mod.TrustDomain


class InjectionThreatCategory(StrEnum):
    DIRECT_OVERRIDE = "direct_override"
    INDIRECT_DOCUMENT_INJECTION = "indirect_document_injection"
    DELIMITER_BREAKOUT = "delimiter_breakout"
    ROLE_IMPERSONATION = "role_impersonation"
    OVERSIZED_CONTENT = "oversized_content"


@dataclass(frozen=True)
class InjectionDetectionResult:
    is_injection: bool
    threat_category: InjectionThreatCategory | None = None
    sanitized_content: str = ""
    confidence: float = 0.0


MAX_SCAN_CHARS = 12000
_BASE64_TOKEN = re.compile(r"(?<![A-Za-z0-9+/])[A-Za-z0-9+/]{24,}={0,2}(?![A-Za-z0-9+/])")

DIRECT_PATTERNS = [
    re.compile(r"\b(?:ignore|forget|disregard|override)\s+(?:all\s+)?(?:prior|previous|existing)\s+(?:instructions|rules|guidelines|prompts)\b"),
    re.compile(r"\b(?:ignora|olvida)\s+(?:todas?\s+)?(?:las\s+)?(?:instrucciones|reglas)\b"),
    re.compile(r"\bbo\s*qua\s+(?:cac\s+)?(?:chi\s*thi|quy\s*dinh|quy\s*tac)\b"),
    re.compile(r"\b(?:you\s+are\s+now\s+in\s+developer\s+mode|enable\s+developer\s+mode|dan\s+mode|unrestricted\s+assistant)\b"),
    re.compile(r"\b(?:system\s+override|bypass\s+security|disable\s+guardrails|disable\s+confirmation|skip\s+authorization)\b"),
    re.compile(r"\b(?:reveal|show|print|disclose|leak)\b.{0,50}\b(?:system\s+prompt|hidden\s+prompt|api\s+key|secret|token|chain\s+of\s+thought)\b"),
    re.compile(r"\b(?:grant|give)\b.{0,40}\b(?:full\s+admin|admin\s+privileges|write\s+access)\b"),
    re.compile(r"\b(?:call|invoke|execute)\b.{0,50}\b(?:delete|drop|send|transfer|write)\b"),
]

INDIRECT_PATTERNS = [
    re.compile(r"\[\s*system\s+override\b.*?\]"),
    re.compile(r"\b(?:assistant|agent|model|tool)\s+(?:must|should)\b.{0,100}\b(?:ignore|execute|call|grant|reveal|delete|send)\b"),
    re.compile(r"\b(?:tool|function|api)\s+(?:result|output|response)\b.{0,100}\b(?:ignore|execute|call|grant|reveal|delete|send)\b"),
]

ROLE_PATTERNS = [
    re.compile(r"<\s*(?:system|developer|assistant)\b"),
    re.compile(r"\[\s*(?:system|developer|assistant)(?:\s+override)?\s*\]"),
    re.compile(r"\b(?:system|developer|assistant)\s*:\s*"),
]

DELIMITER_PATTERNS = [
    re.compile(r"<\/?(?:data_block|system_policy|developer_config|system|instruction)[^>]*>"),
]

BENIGN_QUERY_INDICATORS = [
    re.compile(r"(?:thua thay|lam the nao|quy trinh cu the|nhu the nao|la gi|khi nao|em muon|hoi ve)"),
]


def _normalize(text: str) -> str:
    normalized = unicodedata.normalize("NFKC", text.lower().replace("đ", "d"))
    decomposed = unicodedata.normalize("NFD", normalized)
    safe_chars = (
        char
        for char in decomposed
        if unicodedata.category(char) not in {"Mn", "Cf"}
    )
    return " ".join("".join(safe_chars).split())


def _variants(text: str) -> tuple[str, ...]:
    variants = [_normalize(text), _normalize(unquote(text))]
    for token in _BASE64_TOKEN.findall(text):
        try:
            decoded = base64.b64decode(token, validate=True).decode("utf-8")
        except (UnicodeDecodeError, binascii.Error, ValueError):
            continue
        variants.append(_normalize(decoded))
    return tuple(dict.fromkeys(variant for variant in variants if variant))


def _matches(patterns: list[re.Pattern[str]], variants: tuple[str, ...]) -> bool:
    return any(pattern.search(variant) for pattern in patterns for variant in variants)


class PromptInjectionDetector:
    """Detects and neutralizes prompt injection threats while preserving benign user inquiries."""

    def scan(self, text: str, domain: TrustDomain) -> InjectionDetectionResult:
        if not isinstance(domain, TrustDomain):
            raise TypeError("Prompt injection domain must be a TrustDomain")
        if not isinstance(text, str):
            return InjectionDetectionResult(
                is_injection=True,
                threat_category=InjectionThreatCategory.OVERSIZED_CONTENT,
                sanitized_content="",
                confidence=1.0,
            )
        if len(text) > MAX_SCAN_CHARS:
            return InjectionDetectionResult(
                is_injection=True,
                threat_category=InjectionThreatCategory.OVERSIZED_CONTENT,
                sanitized_content="",
                confidence=1.0,
            )

        sanitized = html.escape(text, quote=True)
        if domain in (TrustDomain.SYSTEM_POLICY, TrustDomain.DEVELOPER_CONFIG):
            return InjectionDetectionResult(False, None, sanitized, 0.0)

        variants = _variants(text)
        normalized = variants[0] if variants else ""
        has_quotes = any(marker in text for marker in ("'", '"', "“", "”"))
        is_benign_inquiry = (
            domain == TrustDomain.USER_INPUT
            and has_quotes
            and ("?" in text or _matches(BENIGN_QUERY_INDICATORS, variants))
        )

        if _matches(DELIMITER_PATTERNS, variants):
            return InjectionDetectionResult(True, InjectionThreatCategory.DELIMITER_BREAKOUT, sanitized, 0.99)
        if _matches(ROLE_PATTERNS, variants):
            return InjectionDetectionResult(True, InjectionThreatCategory.ROLE_IMPERSONATION, sanitized, 0.98)

        if _matches(INDIRECT_PATTERNS, variants):
            return InjectionDetectionResult(
                True,
                InjectionThreatCategory.INDIRECT_DOCUMENT_INJECTION,
                sanitized,
                0.99,
            )

        if _matches(DIRECT_PATTERNS, variants):
            high_risk_direct = any(
                pattern.search(normalized)
                for pattern in DIRECT_PATTERNS[-3:]
            )
            if is_benign_inquiry and not high_risk_direct:
                return InjectionDetectionResult(False, None, sanitized, 0.0)
            category = (
                InjectionThreatCategory.INDIRECT_DOCUMENT_INJECTION
                if domain in (
                    TrustDomain.RETRIEVED_EVIDENCE,
                    TrustDomain.TOOL_OUTPUT,
                    TrustDomain.MEMORY,
                )
                else InjectionThreatCategory.DIRECT_OVERRIDE
            )
            return InjectionDetectionResult(True, category, sanitized, 0.99)

        return InjectionDetectionResult(False, None, sanitized, 0.0)
