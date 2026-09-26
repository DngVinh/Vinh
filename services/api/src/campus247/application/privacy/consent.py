from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from campus247.application.audit.writer import AuditWriter
from campus247.domain.shared.values import generate_uuid7
from campus247.ports.identity import IdentityContext


class ServiceUnavailableError(Exception):
    pass


@dataclass(frozen=True)
class PrivacyNoticeConfig:
    notice_id: str
    version: str
    effective_at: datetime
    status: str
    disclaimer: dict[str, Any]
    data_categories: list[str]
    purposes: list[str]
    retention_summary: list[dict[str, Any]]


@dataclass(frozen=True)
class ConsentRecord:
    id: str
    user_id: str
    purpose: str
    decision: str
    notice_version: str
    recorded_at: datetime


VALID_PURPOSES = {"QUALITY_FEEDBACK", "OPTIONAL_PERSONALIZATION"}
VALID_DECISIONS = {"GRANTED", "WITHDRAWN"}


class PrivacyConsentService:
    def __init__(
        self,
        active_notice: PrivacyNoticeConfig | None = None,
        audit_writer: AuditWriter | None = None,
    ) -> None:
        self._active_notice = active_notice
        self._audit_writer = audit_writer or AuditWriter()
        self._consents: list[ConsentRecord] = []

    def get_active_notice(self) -> PrivacyNoticeConfig:
        if not self._active_notice:
            raise ServiceUnavailableError("Active privacy notice is unavailable")
        return self._active_notice

    def list_user_consents(self, user_id: str) -> list[ConsentRecord]:
        return [c for c in self._consents if c.user_id == user_id]

    def record_consent(
        self,
        actor: IdentityContext,
        purpose: str,
        decision: str,
        notice_version: str,
    ) -> ConsentRecord:
        notice = self.get_active_notice()
        if notice_version != notice.version:
            raise ValueError(f"Notice version mismatch: expected active '{notice.version}', got '{notice_version}'")

        if purpose not in VALID_PURPOSES:
            raise ValueError(f"Unknown consent purpose: {purpose}")

        if decision not in VALID_DECISIONS:
            raise ValueError(f"Unknown consent decision: {decision}")

        now = datetime.now(timezone.utc)
        record = ConsentRecord(
            id=generate_uuid7(),
            user_id=actor.subject_id,
            purpose=purpose,
            decision=decision,
            notice_version=notice_version,
            recorded_at=now,
        )
        self._consents.append(record)

        self._audit_writer.record_event(
            actor_type=actor.roles[0].value if actor.roles else "STUDENT",
            actor_id=actor.subject_id,
            action_code=f"privacy.consent_{decision.lower()}",
            resource_type="consent",
            resource_id=record.id,
            outcome="SUCCESS",
            metadata={"purpose": purpose, "notice_version": notice_version},
        )

        return record
