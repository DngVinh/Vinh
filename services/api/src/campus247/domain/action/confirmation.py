from __future__ import annotations

import base64
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import hmac
import json

from campus247.domain.action.preview import ActionPreviewValue


@dataclass(frozen=True)
class ConfirmationValidationResult:
    is_valid: bool
    preview_id: str | None = None
    actor_user_id: str | None = None
    error_code: str | None = None


class ConfirmationTokenService:
    def __init__(self, signing_key: str) -> None:
        self._key = signing_key.encode("utf-8")

    def mint_token(self, preview: ActionPreviewValue) -> str:
        payload = {
            "pid": preview.id,
            "act": preview.actor_user_id,
            "phash": preview.payload_hash,
            "exp": int(preview.expires_at.timestamp()),
        }
        raw_payload = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
        b64_payload = base64.urlsafe_b64encode(raw_payload).decode("ascii")
        sig = hmac.new(self._key, b64_payload.encode("ascii"), hashlib.sha256).digest()
        b64_sig = base64.urlsafe_b64encode(sig).decode("ascii")
        return f"{b64_payload}.{b64_sig}"

    def validate_token(
        self,
        token: str,
        expected_preview_id: str,
        expected_actor_id: str,
        expected_payload_hash: str,
        at_time: datetime | None = None,
    ) -> ConfirmationValidationResult:
        parts = token.split(".")
        if len(parts) != 2:
            return ConfirmationValidationResult(is_valid=False, error_code="FORMAT_INVALID")
        b64_payload, b64_sig = parts
        try:
            expected_sig = hmac.new(self._key, b64_payload.encode("ascii"), hashlib.sha256).digest()
            actual_sig = base64.urlsafe_b64decode(b64_sig.encode("ascii"))
            if not hmac.compare_digest(expected_sig, actual_sig):
                return ConfirmationValidationResult(is_valid=False, error_code="SIGNATURE_INVALID")

            payload = json.loads(base64.urlsafe_b64decode(b64_payload.encode("ascii")).decode("utf-8"))
        except Exception:
            return ConfirmationValidationResult(is_valid=False, error_code="SIGNATURE_INVALID")

        check_time = at_time or datetime.now(timezone.utc)
        if payload.get("exp", 0) <= int(check_time.timestamp()):
            return ConfirmationValidationResult(is_valid=False, error_code="TOKEN_EXPIRED")

        if payload.get("pid") != expected_preview_id:
            return ConfirmationValidationResult(is_valid=False, error_code="PREVIEW_ID_MISMATCH")

        if payload.get("act") != expected_actor_id:
            return ConfirmationValidationResult(is_valid=False, error_code="ACTOR_MISMATCH")

        if payload.get("phash") != expected_payload_hash:
            return ConfirmationValidationResult(is_valid=False, error_code="PAYLOAD_HASH_MISMATCH")

        return ConfirmationValidationResult(
            is_valid=True,
            preview_id=payload["pid"],
            actor_user_id=payload["act"],
        )
