from __future__ import annotations

import base64
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import hmac
import json
import secrets
from typing import Any


@dataclass(frozen=True)
class ConfirmationValidationResult:
    is_valid: bool
    preview_id: str | None = None
    actor_id: str | None = None
    action_type: str | None = None
    version: int | None = None
    error_code: str | None = None


class ConfirmationTokenService:
    def __init__(self, signing_key: str) -> None:
        if not isinstance(signing_key, str) or not signing_key:
            raise ValueError("confirmation signing key must be configured")
        self._key = signing_key.encode("utf-8")

    @staticmethod
    def canonicalize_payload(payload: dict[str, Any] | str) -> str:
        """Deterministic canonical JSON serialization."""
        if isinstance(payload, str):
            try:
                parsed = json.loads(payload)
                return json.dumps(parsed, sort_keys=True, separators=(",", ":"))
            except Exception:
                return payload.strip()
        return json.dumps(payload, sort_keys=True, separators=(",", ":"))

    @classmethod
    def compute_payload_hash(cls, payload: dict[str, Any] | str) -> str:
        canonical = cls.canonicalize_payload(payload)
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    def mint_token(
        self,
        preview_id: str,
        actor_id: str,
        action_type: str,
        payload_hash: str,
        preview_version: int,
        expires_at: datetime,
        session_id: str = "none",
        conversation_id: str = "none",
        tool_version: str = "1.0",
        policy_version: str = "1.0",
    ) -> str:
        data = {
            "pid": preview_id,
            "act": actor_id,
            "sid": session_id,
            "cid": conversation_id,
            "tver": tool_version,
            "pver": policy_version,
            "atyp": action_type,
            "phash": payload_hash,
            "ver": preview_version,
            "exp": int(expires_at.timestamp()),
            "nonce": secrets.token_urlsafe(16),
        }
        raw_payload = json.dumps(data, sort_keys=True, separators=(",", ":")).encode("utf-8")
        b64_payload = base64.urlsafe_b64encode(raw_payload).decode("ascii")
        sig = hmac.new(self._key, b64_payload.encode("ascii"), hashlib.sha256).digest()
        b64_sig = base64.urlsafe_b64encode(sig).decode("ascii")
        return f"{b64_payload}.{b64_sig}"

    def validate_token(
        self,
        token: str,
        expected_preview_id: str,
        expected_actor_id: str,
        expected_action_type: str,
        expected_payload_hash: str,
        expected_version: int,
        expected_session_id: str = "none",
        expected_conversation_id: str = "none",
        expected_tool_version: str = "1.0",
        expected_policy_version: str = "1.0",
        at_time: datetime | None = None,
    ) -> ConfirmationValidationResult:
        if not isinstance(token, str):
            return ConfirmationValidationResult(is_valid=False, error_code="FORMAT_INVALID")
        parts = token.split(".")
        if len(parts) != 2 or not all(parts):
            return ConfirmationValidationResult(is_valid=False, error_code="FORMAT_INVALID")
        b64_payload, b64_sig = parts
        try:
            expected_sig = hmac.new(self._key, b64_payload.encode("ascii"), hashlib.sha256).digest()
            actual_sig = base64.urlsafe_b64decode(b64_sig.encode("ascii"))
            if len(actual_sig) != len(expected_sig) or not hmac.compare_digest(expected_sig, actual_sig):
                return ConfirmationValidationResult(is_valid=False, error_code="SIGNATURE_INVALID")

            payload = json.loads(base64.urlsafe_b64decode(b64_payload.encode("ascii")).decode("utf-8"))
        except Exception:
            return ConfirmationValidationResult(is_valid=False, error_code="SIGNATURE_INVALID")

        if not isinstance(payload, dict):
            return ConfirmationValidationResult(is_valid=False, error_code="FORMAT_INVALID")

        expires_at = payload.get("exp")
        preview_version = payload.get("ver")
        required_text_fields = ("pid", "act", "atyp", "phash", "nonce")
        if (
            not isinstance(expires_at, int)
            or isinstance(expires_at, bool)
            or not isinstance(preview_version, int)
            or isinstance(preview_version, bool)
            or any(not isinstance(payload.get(field), str) or not payload[field] for field in required_text_fields)
        ):
            return ConfirmationValidationResult(is_valid=False, error_code="FORMAT_INVALID")

        check_time = at_time or datetime.now(timezone.utc)
        if expires_at <= int(check_time.timestamp()):
            return ConfirmationValidationResult(is_valid=False, error_code="TOKEN_EXPIRED")

        if payload.get("pid") != expected_preview_id:
            return ConfirmationValidationResult(is_valid=False, error_code="PREVIEW_ID_MISMATCH")

        if payload.get("act") != expected_actor_id:
            return ConfirmationValidationResult(is_valid=False, error_code="ACTOR_MISMATCH")

        if payload.get("atyp") != expected_action_type:
            return ConfirmationValidationResult(is_valid=False, error_code="ACTION_TYPE_MISMATCH")

        if payload.get("phash") != expected_payload_hash:
            return ConfirmationValidationResult(is_valid=False, error_code="PAYLOAD_HASH_MISMATCH")

        if preview_version != expected_version:
            return ConfirmationValidationResult(is_valid=False, error_code="VERSION_MISMATCH")

        return ConfirmationValidationResult(
            is_valid=True,
            preview_id=payload["pid"],
            actor_id=payload["act"],
            action_type=payload["atyp"],
            version=payload["ver"],
        )
