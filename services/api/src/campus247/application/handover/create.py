from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
from typing import Any

from campus247.application.action.idempotency import IdempotencyLedger, ReservationStatus
from campus247.application.audit.writer import AuditWriter
from campus247.domain.handover.model import Handover, HandoverRiskLevel, HandoverStatus
from campus247.domain.shared.values import is_valid_uuid7
from campus247.ports.identity import IdentityContext

VALID_CATEGORIES = {
    "USER_REQUEST",
    "INSUFFICIENT_EVIDENCE",
    "ACADEMIC_RIGHTS",
    "COMPLAINT_OR_DISCIPLINE",
    "SENSITIVE_WELLBEING",
    "PRIVACY_OR_SECURITY",
    "TOOL_UNCERTAINTY",
    "OTHER_REVIEW",
}

VALID_REASON_CODES = {
    "USER_REQUESTED_HUMAN",
    "INSUFFICIENT_EVIDENCE",
    "POLICY_EXCEPTION",
    "ACADEMIC_RIGHTS_IMPACT",
    "COMPLAINT_OR_DISCIPLINE",
    "SENSITIVE_WELLBEING",
    "POTENTIAL_SELF_HARM",
    "POTENTIAL_VIOLENCE",
    "HARASSMENT_OR_ABUSE",
    "DATA_PRIVACY_INCIDENT",
    "TOOL_OR_INTEGRATION_FAILURE",
    "OTHER_REVIEW_REQUIRED",
}


@dataclass(frozen=True)
class CreateHandoverCommand:
    conversation_id: str
    category: str
    severity: str
    summary: str
    reason_codes: list[str]
    related_reference_ids: list[str] | None = None


@dataclass(frozen=True)
class TruthfulReceipt:
    handover_id: str
    queue_key: str
    status: str
    reason_code: str
    risk_level: str
    created_at: str
    version: int
    truthful_notice: str


@dataclass(frozen=True)
class HandoverCreationResult:
    handover: Handover
    receipt: TruthfulReceipt
    is_replay: bool = False


def route_handover(category: str, reason_codes: list[str], severity: str) -> tuple[str, HandoverRiskLevel]:
    reasons = set(reason_codes)
    if category == "PRIVACY_OR_SECURITY" or "DATA_PRIVACY_INCIDENT" in reasons:
        return "PRIVACY_SECURITY", HandoverRiskLevel.CRITICAL
    if category == "SENSITIVE_WELLBEING" or bool(
        {"POTENTIAL_SELF_HARM", "POTENTIAL_VIOLENCE", "HARASSMENT_OR_ABUSE", "SENSITIVE_WELLBEING"} & reasons
    ):
        risk = (
            HandoverRiskLevel.CRITICAL
            if bool({"POTENTIAL_SELF_HARM", "POTENTIAL_VIOLENCE"} & reasons) or severity == "critical"
            else HandoverRiskLevel.HIGH
        )
        return "SAFETY_RESTRICTED", risk
    if category == "ACADEMIC_RIGHTS" or bool({"ACADEMIC_RIGHTS_IMPACT", "POLICY_EXCEPTION"} & reasons):
        risk = (
            HandoverRiskLevel.HIGH
            if severity == "critical"
            else (HandoverRiskLevel.MEDIUM if severity == "high" else HandoverRiskLevel.LOW)
        )
        return "ACADEMIC_POLICY", risk
    if category == "TOOL_UNCERTAINTY" or "TOOL_OR_INTEGRATION_FAILURE" in reasons:
        risk = HandoverRiskLevel.HIGH if severity == "critical" else HandoverRiskLevel.MEDIUM
        return "OPERATIONS_FALLBACK", risk
    risk = (
        HandoverRiskLevel.HIGH
        if severity == "critical"
        else (HandoverRiskLevel.MEDIUM if severity == "high" else HandoverRiskLevel.LOW)
    )
    return "STUDENT_SUPPORT_GENERAL", risk


class HandoverCreationService:
    def __init__(
        self,
        idempotency_ledger: IdempotencyLedger | None = None,
        audit_writer: AuditWriter | None = None,
    ) -> None:
        self._idempotency_ledger = idempotency_ledger or IdempotencyLedger()
        self._audit_writer = audit_writer or AuditWriter()
        self._handovers: dict[str, Handover] = {}
        self._receipts: dict[str, TruthfulReceipt] = {}

    def create_handover(
        self,
        actor: IdentityContext,
        command: CreateHandoverCommand,
        idempotency_key: str | None = None,
    ) -> HandoverCreationResult:
        if not is_valid_uuid7(command.conversation_id):
            raise ValueError(f"Invalid conversation_id UUIDv7: {command.conversation_id}")
        if command.category not in VALID_CATEGORIES:
            raise ValueError(f"Invalid handover category: {command.category}")
        if not command.reason_codes or len(command.reason_codes) > 10:
            raise ValueError("reason_codes must contain between 1 and 10 items")
        for code in command.reason_codes:
            if code not in VALID_REASON_CODES:
                raise ValueError(f"Invalid reason code: {code}")
        summary_clean = command.summary.strip()
        if not summary_clean:
            raise ValueError("Summary cannot be empty")
        if len(summary_clean) > 2000:
            raise ValueError("Summary exceeds maximum length of 2000 characters")

        payload_dict = {
            "conversation_id": command.conversation_id,
            "category": command.category,
            "severity": command.severity,
            "summary": summary_clean,
            "reason_codes": sorted(command.reason_codes),
        }
        payload_hash = hashlib.sha256(json.dumps(payload_dict, sort_keys=True).encode("utf-8")).hexdigest()

        if idempotency_key:
            res = self._idempotency_ledger.reserve(
                actor_user_id=actor.subject_id,
                operation_id="handover.create",
                idempotency_key=idempotency_key,
                request_fingerprint=payload_hash,
            )
            if res.status == ReservationStatus.REPLAY:
                h_id = res.record.response_reference if res.record else None
                if h_id and h_id in self._handovers:
                    return HandoverCreationResult(
                        handover=self._handovers[h_id],
                        receipt=self._receipts[h_id],
                        is_replay=True,
                    )
            if res.status in (ReservationStatus.CONFLICT_REUSED, ReservationStatus.CONFLICT_IN_PROGRESS):
                raise ValueError("Idempotency conflict detected for handover.create")

        queue_key, risk_level = route_handover(command.category, command.reason_codes, command.severity)
        ref_ids = ",".join(command.related_reference_ids) if command.related_reference_ids else None
        handover = Handover.create_queued(
            conversation_id=command.conversation_id,
            requester_user_id=actor.subject_id,
            queue_key=queue_key,
            reason_code=command.reason_codes[0],
            risk_level=risk_level,
            summary=summary_clean,
            context_reference_ids=ref_ids,
        )
        self._handovers[handover.id] = handover

        notice = (
            f"Yêu cầu hỗ trợ đã được chuyển tiếp thành công đến hàng đợi {queue_key} "
            f"với trạng thái {handover.status.value}. Cán bộ phụ trách sẽ tiếp nhận và xử lý theo quy trình. "
            "Hệ thống không theo dõi theo thời gian thực và không hứa hẹn thời gian phản hồi tức thì."
        )
        receipt = TruthfulReceipt(
            handover_id=handover.id,
            queue_key=queue_key,
            status=handover.status.value,
            reason_code=handover.reason_code,
            risk_level=handover.risk_level.value,
            created_at=handover.created_at.isoformat(),
            version=handover.version,
            truthful_notice=notice,
        )
        self._receipts[handover.id] = receipt

        actor_type = actor.roles[0].value if actor.roles else "STUDENT"
        self._audit_writer.record_event(
            actor_type=actor_type,
            actor_id=actor.subject_id,
            action_code="handover.routed_create",
            resource_type="handover",
            resource_id=handover.id,
            outcome="SUCCESS",
        )

        if idempotency_key:
            self._idempotency_ledger.complete(
                actor_user_id=actor.subject_id,
                operation_id="handover.create",
                idempotency_key=idempotency_key,
                http_status=201,
                response_payload=handover.id,
            )

        return HandoverCreationResult(handover=handover, receipt=receipt, is_replay=False)
