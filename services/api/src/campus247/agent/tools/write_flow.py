from __future__ import annotations

from datetime import datetime, timedelta, timezone
import hashlib
import json
from typing import Any

from campus247.agent.state import ToolPhase
from campus247.domain.action.preview import ActionPreviewValue
from campus247.domain.shared.values import generate_uuid7


def _normalize_and_hash(payload: dict[str, Any]) -> tuple[str, str]:
    normalized = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    h = hashlib.sha256(normalized.encode("utf-8")).hexdigest()
    return normalized, h


class WriteToolFlowBroker:
    """Manages write-tool preview generation and human confirmation interrupt validation."""

    def __init__(self, expiry_minutes: int = 10) -> None:
        self._expiry_minutes = expiry_minutes

    def build_preview(
        self,
        actor_id: str,
        tool_id: str,
        arguments: dict[str, Any],
    ) -> ActionPreviewValue:
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(minutes=self._expiry_minutes)

        normalized_json, payload_hash = _normalize_and_hash(arguments)
        dummy_secret_hash = hashlib.sha256(f"secret-{payload_hash}".encode("utf-8")).hexdigest()

        return ActionPreviewValue(
            id=generate_uuid7(),
            actor_user_id=actor_id,
            action_type=tool_id,
            normalized_payload=normalized_json,
            payload_hash=payload_hash,
            policy_decision="ALLOW",
            confirmation_secret_hash=dummy_secret_hash,
            created_at=now,
            expires_at=expires_at,
        )

    def create_confirmation_interrupt(self, preview: ActionPreviewValue) -> dict[str, Any]:
        return {
            "phase": ToolPhase.AWAITING_CONFIRMATION,
            "preview_id": preview.id,
            "action_type": preview.action_type,
            "actor_id": preview.actor_user_id,
            "payload_hash": preview.payload_hash,
            "expires_at": preview.expires_at.isoformat(),
        }

    def revalidate(
        self,
        preview: ActionPreviewValue,
        arguments: dict[str, Any],
        at_time: datetime | None = None,
    ) -> bool:
        check_time = at_time or datetime.now(timezone.utc)
        if preview.is_expired(check_time):
            return False

        _, current_hash = _normalize_and_hash(arguments)
        if current_hash != preview.payload_hash:
            return False

        return True
