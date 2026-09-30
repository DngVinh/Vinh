from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
import threading
from typing import Any
from sqlalchemy import text
from sqlalchemy.engine import Engine

from campus247.domain.shared.values import generate_uuid7


class BookingOverlapError(Exception):
    pass


class IdempotencyConflictError(Exception):
    pass


@dataclass
class BookingRecord:
    id: str
    room_id: str
    requester_user_id: str
    starts_at: datetime
    ends_at: datetime
    purpose_redacted: str
    attendee_count: int
    status: str
    action_execution_id: str
    idempotency_key: str | None = None
    payload_hash: str | None = None
    cancelled_at: datetime | None = None


_room_locks: dict[str, threading.Lock] = {}
_meta_lock = threading.Lock()


def _get_room_lock(room_id: str) -> threading.Lock:
    with _meta_lock:
        if room_id not in _room_locks:
            _room_locks[room_id] = threading.Lock()
        return _room_locks[room_id]


def _compute_payload_hash(
    room_id: str,
    requester_user_id: str,
    starts_at: datetime,
    ends_at: datetime,
    purpose: str,
    attendee_count: int,
) -> str:
    canonical = {
        "room_id": room_id,
        "requester_user_id": requester_user_id,
        "starts_at": starts_at.isoformat(),
        "ends_at": ends_at.isoformat(),
        "purpose": purpose,
        "attendee_count": attendee_count,
    }
    raw = json.dumps(canonical, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


class DatabaseBookingRepository:
    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def create_booking(
        self,
        booking_id: str,
        room_id: str,
        requester_user_id: str,
        starts_at: datetime,
        ends_at: datetime,
        purpose_redacted: str,
        attendee_count: int,
        action_execution_id: str,
        idempotency_key: str | None = None,
    ) -> BookingRecord:
        current_hash = _compute_payload_hash(
            room_id=room_id,
            requester_user_id=requester_user_id,
            starts_at=starts_at,
            ends_at=ends_at,
            purpose=purpose_redacted,
            attendee_count=attendee_count,
        )

        room_lock = _get_room_lock(room_id)
        with room_lock:
            with self._engine.begin() as conn:
                # 1. Idempotency Check
                if idempotency_key:
                    existing = conn.execute(
                        text("""
                            SELECT id, room_id, requester_user_id, starts_at, ends_at,
                                   purpose_redacted, attendee_count, status, action_execution_id,
                                   idempotency_key, payload_hash, cancelled_at
                            FROM room_booking
                            WHERE idempotency_key = :key
                        """),
                        {"key": idempotency_key},
                    ).fetchone()

                    if existing:
                        # Existing row matched
                        if existing.payload_hash == current_hash:
                            # AC-TASK-DB-BOOKFIX-001-02: Same-key same-payload retries return the original outcome
                            return BookingRecord(
                                id=existing.id,
                                room_id=existing.room_id,
                                requester_user_id=existing.requester_user_id,
                                starts_at=existing.starts_at,
                                ends_at=existing.ends_at,
                                purpose_redacted=existing.purpose_redacted,
                                attendee_count=existing.attendee_count,
                                status=existing.status,
                                action_execution_id=existing.action_execution_id,
                                idempotency_key=existing.idempotency_key,
                                payload_hash=existing.payload_hash,
                                cancelled_at=existing.cancelled_at,
                            )
                        else:
                            # AC-TASK-DB-BOOKFIX-001-02: Same-key different-payload retries fail
                            raise IdempotencyConflictError(
                                f"Idempotency key '{idempotency_key}' reused with conflicting payload"
                            )

                # 2. Concurrency & Overlap Check
                # AC-TASK-DB-BOOKFIX-001-01: At most one conflicting active booking commits
                # Active if status == 'CONFIRMED'
                # Overlap condition: starts_at < existing.ends_at AND ends_at > existing.starts_at
                overlap = conn.execute(
                    text("""
                        SELECT id FROM room_booking
                        WHERE room_id = :room_id
                          AND status = 'CONFIRMED'
                          AND starts_at < :ends_at
                          AND ends_at > :starts_at
                    """),
                    {
                        "room_id": room_id,
                        "starts_at": starts_at,
                        "ends_at": ends_at,
                    },
                ).fetchone()

                if overlap:
                    raise BookingOverlapError(
                        f"Active conflicting booking '{overlap.id}' already occupies room '{room_id}' during requested time"
                    )

                # 3. Insert new booking
                conn.execute(
                    text("""
                        INSERT INTO room_booking (
                            id, room_id, requester_user_id, starts_at, ends_at,
                            purpose_redacted, attendee_count, status, action_execution_id,
                            idempotency_key, payload_hash
                        ) VALUES (
                            :id, :room_id, :requester_user_id, :starts_at, :ends_at,
                            :purpose_redacted, :attendee_count, 'CONFIRMED', :action_execution_id,
                            :idempotency_key, :payload_hash
                        )
                    """),
                    {
                        "id": booking_id,
                        "room_id": room_id,
                        "requester_user_id": requester_user_id,
                        "starts_at": starts_at,
                        "ends_at": ends_at,
                        "purpose_redacted": purpose_redacted,
                        "attendee_count": attendee_count,
                        "action_execution_id": action_execution_id,
                        "idempotency_key": idempotency_key,
                        "payload_hash": current_hash,
                    },
                )

        return BookingRecord(
            id=booking_id,
            room_id=room_id,
            requester_user_id=requester_user_id,
            starts_at=starts_at,
            ends_at=ends_at,
            purpose_redacted=purpose_redacted,
            attendee_count=attendee_count,
            status="CONFIRMED",
            action_execution_id=action_execution_id,
            idempotency_key=idempotency_key,
            payload_hash=current_hash,
        )

    def cancel_booking(self, booking_id: str) -> None:
        now = datetime.now(timezone.utc)
        with self._engine.begin() as conn:
            conn.execute(
                text("""
                    UPDATE room_booking
                    SET status = 'CANCELLED', cancelled_at = :now
                    WHERE id = :id
                """),
                {"id": booking_id, "now": now},
            )
