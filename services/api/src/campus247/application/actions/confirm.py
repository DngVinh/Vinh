from __future__ import annotations

from datetime import datetime
import threading
from typing import Any, Callable

from campus247.domain.actions.confirmation import (
    ConfirmationTokenService,
    ConfirmationValidationResult,
)


class ConfirmationError(Exception):
    """Raised when confirmation validation or reservation fails."""
    pass


class ConfirmationReservationService:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._reserved_tokens: dict[str, tuple[str, str]] = {}

    def reserve(self, token: str, preview_id: str, actor_id: str) -> bool:
        """Atomically reserve a token. Exactly one concurrent caller succeeds."""
        if not isinstance(token, str) or not token:
            return False
        with self._lock:
            if token in self._reserved_tokens:
                return False
            self._reserved_tokens[token] = (preview_id, actor_id)
            return True

    def is_reserved(self, token: str) -> bool:
        with self._lock:
            return isinstance(token, str) and token in self._reserved_tokens

    def clear(self) -> None:
        with self._lock:
            self._reserved_tokens.clear()


class ConfirmationExecutionManager:
    def __init__(
        self,
        token_service: ConfirmationTokenService,
        reservation_service: ConfirmationReservationService,
        audit_writer: Any | None = None,
    ) -> None:
        self._token_service = token_service
        self._reservation_service = reservation_service
        self._audit_writer = audit_writer

    def execute(
        self,
        token: str,
        preview_id: str,
        actor_id: str,
        action_type: str,
        payload_hash: str,
        version: int,
        action_fn: Callable[[], Any],
        at_time: datetime | None = None,
    ) -> Any:
        # 1. Validate token binding cryptographically and temporally
        val_res: ConfirmationValidationResult = self._token_service.validate_token(
            token=token,
            expected_preview_id=preview_id,
            expected_actor_id=actor_id,
            expected_action_type=action_type,
            expected_payload_hash=payload_hash,
            expected_version=version,
            at_time=at_time,
        )
        if not val_res.is_valid:
            if self._audit_writer:
                self._audit_writer.append_transition(
                    action_type=action_type,
                    actor_id=actor_id,
                    preview_id=preview_id,
                    binding_hash=payload_hash,
                    stage="VALIDATION",
                    outcome="DENIED",
                    metadata={"error": val_res.error_code},
                )
            raise ConfirmationError(f"Confirmation validation failed: {val_res.error_code}")

        # 2. Stage 1: Pre-dispatch audit logging (Audit failure aborts execution immediately)
        if self._audit_writer:
            self._audit_writer.append_transition(
                action_type=action_type,
                actor_id=actor_id,
                preview_id=preview_id,
                binding_hash=payload_hash,
                stage="RESERVED",
                outcome="SUCCESS",
            )

        # 3. Atomically reserve token - reject replay or concurrent execution
        reserved = self._reservation_service.reserve(token, preview_id, actor_id)
        if not reserved:
            if self._audit_writer:
                self._audit_writer.append_transition(
                    action_type=action_type,
                    actor_id=actor_id,
                    preview_id=preview_id,
                    binding_hash=payload_hash,
                    stage="RESERVATION",
                    outcome="FAILED",
                    metadata={"error": "ALREADY_RESERVED"},
                )
            raise ConfirmationError("Confirmation token ALREADY_RESERVED: replay rejected")

        # 4. Stage 2: Execute controlled side-effect
        try:
            result = action_fn()
        except Exception as exc:
            if self._audit_writer:
                self._audit_writer.append_transition(
                    action_type=action_type,
                    actor_id=actor_id,
                    preview_id=preview_id,
                    binding_hash=payload_hash,
                    stage="COMPLETED",
                    outcome="FAILED",
                    metadata={"error_code": "ACTION_FAILED"},
                )
            raise

        # 5. Stage 3: Post-dispatch completion audit
        if self._audit_writer:
            self._audit_writer.append_transition(
                action_type=action_type,
                actor_id=actor_id,
                preview_id=preview_id,
                binding_hash=payload_hash,
                stage="COMPLETED",
                outcome="SUCCESS",
            )

        return result
