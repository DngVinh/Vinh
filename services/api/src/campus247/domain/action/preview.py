from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import hashlib
import json
import secrets
from typing import Any

from campus247.domain.shared.values import generate_uuid7, is_valid_uuid7


@dataclass(frozen=True)
class ActionPreviewValue:
    id: str
    actor_user_id: str
    session_id: str
    conversation_id: str
    action_type: str
    tool_version: str
    policy_version: str
    normalized_payload: str
    payload_hash: str
    policy_decision: str
    confirmation_secret_hash: str
    created_at: datetime
    expires_at: datetime
    consumed_at: datetime | None = None
    cancelled_at: datetime | None = None

    def __post_init__(self) -> None:
        if not is_valid_uuid7(self.id):
            raise ValueError(f"id must be a valid UUIDv7, got: {self.id}")
        if not is_valid_uuid7(self.actor_user_id):
            raise ValueError(f"actor_user_id must be a valid UUIDv7, got: {self.actor_user_id}")
        raw_hash = hashlib.sha256(self.normalized_payload.encode("utf-8")).hexdigest()
        expected_hash = f"sha256:{raw_hash}"
        if self.payload_hash != expected_hash:
            raise ValueError(f"payload_hash mismatch: expected {expected_hash}, got {self.payload_hash}")
        if self.expires_at <= self.created_at:
            raise ValueError("expires_at must be after created_at")

    def is_expired(self, at_time: datetime) -> bool:
        return at_time >= self.expires_at

    def is_consumed(self) -> bool:
        return self.consumed_at is not None

    def is_cancelled(self) -> bool:
        return self.cancelled_at is not None

    def is_active(self, at_time: datetime) -> bool:
        return not self.is_expired(at_time) and not self.is_consumed() and not self.is_cancelled()


def create_action_preview(
    actor_user_id: str,
    action_type: str,
    payload: dict[str, Any],
    session_id: str = "none",
    conversation_id: str = "none",
    tool_version: str = "1.0",
    policy_version: str = "1.0",
    ttl_seconds: int = 300,
    preview_id: str | None = None,
    policy_decision: str = "allow",
) -> ActionPreviewValue:
    pid = preview_id or generate_uuid7()
    normalized_json = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    raw_hash = hashlib.sha256(normalized_json.encode("utf-8")).hexdigest()
    payload_hash = f"sha256:{raw_hash}"

    raw_secret = secrets.token_urlsafe(32)
    secret_hash = hashlib.sha256(raw_secret.encode("utf-8")).hexdigest()

    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(seconds=ttl_seconds)

    return ActionPreviewValue(
        id=pid,
        actor_user_id=actor_user_id,
        session_id=session_id,
        conversation_id=conversation_id,
        action_type=action_type,
        tool_version=tool_version,
        policy_version=policy_version,
        normalized_payload=normalized_json,
        payload_hash=payload_hash,
        policy_decision=policy_decision,
        confirmation_secret_hash=secret_hash,
        created_at=now,
        expires_at=expires_at,
    )
