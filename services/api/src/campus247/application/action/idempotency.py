from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from enum import StrEnum

from campus247.domain.shared.values import generate_uuid7


class IdempotencyState(StrEnum):
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    FAILED_RETRYABLE = "FAILED_RETRYABLE"
    FAILED_FINAL = "FAILED_FINAL"


class ReservationStatus(StrEnum):
    ACQUIRED = "ACQUIRED"
    REPLAY = "REPLAY"
    CONFLICT_REUSED = "CONFLICT_REUSED"
    CONFLICT_IN_PROGRESS = "CONFLICT_IN_PROGRESS"


@dataclass
class IdempotencyRecord:
    id: str
    actor_user_id: str
    operation_id: str
    idempotency_key: str
    request_fingerprint: str
    state: IdempotencyState
    http_status: int | None = None
    response_reference: str | None = None
    expires_at: datetime | None = None


@dataclass(frozen=True)
class ReservationResult:
    status: ReservationStatus
    record: IdempotencyRecord | None = None
    error_code: str | None = None


class IdempotencyLedger:
    def __init__(self) -> None:
        self._records: dict[tuple[str, str, str], IdempotencyRecord] = {}

    def reserve(
        self,
        actor_user_id: str,
        operation_id: str,
        idempotency_key: str,
        request_fingerprint: str,
        ttl_seconds: int = 86400,
    ) -> ReservationResult:
        if not (16 <= len(idempotency_key) <= 128):
            raise ValueError("Idempotency key length must be between 16 and 128 characters")

        scope_key = (actor_user_id, operation_id, idempotency_key)
        existing = self._records.get(scope_key)

        now = datetime.now(timezone.utc)
        if existing:
            if existing.request_fingerprint != request_fingerprint:
                return ReservationResult(
                    status=ReservationStatus.CONFLICT_REUSED,
                    error_code="IDEMPOTENCY_KEY_REUSED",
                )
            if existing.state == IdempotencyState.IN_PROGRESS:
                return ReservationResult(
                    status=ReservationStatus.CONFLICT_IN_PROGRESS,
                    error_code="IDEMPOTENCY_IN_PROGRESS",
                )
            if existing.state == IdempotencyState.COMPLETED:
                return ReservationResult(
                    status=ReservationStatus.REPLAY,
                    record=existing,
                )

        record = IdempotencyRecord(
            id=generate_uuid7(),
            actor_user_id=actor_user_id,
            operation_id=operation_id,
            idempotency_key=idempotency_key,
            request_fingerprint=request_fingerprint,
            state=IdempotencyState.IN_PROGRESS,
            expires_at=now + timedelta(seconds=ttl_seconds),
        )
        self._records[scope_key] = record
        return ReservationResult(status=ReservationStatus.ACQUIRED, record=record)

    def complete(
        self,
        actor_user_id: str,
        operation_id: str,
        idempotency_key: str,
        http_status: int,
        response_payload: str,
    ) -> None:
        scope_key = (actor_user_id, operation_id, idempotency_key)
        existing = self._records.get(scope_key)
        if existing:
            existing.state = IdempotencyState.COMPLETED
            existing.http_status = http_status
            existing.response_reference = response_payload

    def fail(
        self,
        actor_user_id: str,
        operation_id: str,
        idempotency_key: str,
        retryable: bool = False,
    ) -> None:
        scope_key = (actor_user_id, operation_id, idempotency_key)
        existing = self._records.get(scope_key)
        if existing:
            existing.state = (
                IdempotencyState.FAILED_RETRYABLE if retryable else IdempotencyState.FAILED_FINAL
            )
