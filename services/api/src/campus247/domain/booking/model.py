from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime, timezone
from enum import StrEnum
from typing import Sequence

from campus247.domain.shared.values import generate_uuid7, is_valid_uuid7


class BookingStatus(StrEnum):
    CONFIRMED = "CONFIRMED"
    CANCELLED = "CANCELLED"
    COMPLETED = "COMPLETED"


class RoomSlotUnavailableError(Exception):
    pass


class InvalidBookingValidationError(ValueError):
    pass


class InvalidBookingStateError(Exception):
    pass


@dataclass(frozen=True)
class RoomBooking:
    id: str
    room_id: str
    requester_user_id: str
    starts_at: datetime
    ends_at: datetime
    purpose_redacted: str
    attendee_count: int
    status: BookingStatus
    action_execution_id: str
    created_at: datetime
    updated_at: datetime
    cancelled_at: datetime | None = None
    version: int = 1

    def __post_init__(self) -> None:
        if not is_valid_uuid7(self.room_id):
            raise InvalidBookingValidationError(f"room_id must be a valid UUIDv7, got {self.room_id}")
        if not is_valid_uuid7(self.requester_user_id):
            raise InvalidBookingValidationError(f"requester_user_id must be a valid UUIDv7, got {self.requester_user_id}")
        if not is_valid_uuid7(self.action_execution_id):
            raise InvalidBookingValidationError(f"action_execution_id must be a valid UUIDv7, got {self.action_execution_id}")
        if self.ends_at <= self.starts_at:
            raise InvalidBookingValidationError("ends_at must be after starts_at")
        if self.attendee_count < 1:
            raise InvalidBookingValidationError("attendee_count must be >= 1")
        if not self.purpose_redacted or len(self.purpose_redacted) > 300:
            raise InvalidBookingValidationError("purpose_redacted must be non-empty and <= 300 chars")

    @classmethod
    def confirm_booking(
        cls,
        room_id: str,
        requester_user_id: str,
        starts_at: datetime,
        ends_at: datetime,
        purpose_redacted: str,
        attendee_count: int,
        action_execution_id: str,
    ) -> RoomBooking:
        now = datetime.now(timezone.utc)
        return cls(
            id=generate_uuid7(),
            room_id=room_id,
            requester_user_id=requester_user_id,
            starts_at=starts_at,
            ends_at=ends_at,
            purpose_redacted=purpose_redacted,
            attendee_count=attendee_count,
            status=BookingStatus.CONFIRMED,
            action_execution_id=action_execution_id,
            created_at=now,
            updated_at=now,
            version=1,
        )

    def cancel(self, cancelled_at: datetime | None = None) -> RoomBooking:
        if self.status != BookingStatus.CONFIRMED:
            raise InvalidBookingStateError(f"Cannot cancel booking with status {self.status}")
        now = cancelled_at or datetime.now(timezone.utc)
        return replace(
            self,
            status=BookingStatus.CANCELLED,
            cancelled_at=now,
            updated_at=now,
            version=self.version + 1,
        )

    def complete(self) -> RoomBooking:
        if self.status != BookingStatus.CONFIRMED:
            raise InvalidBookingStateError(f"Cannot complete booking with status {self.status}")
        now = datetime.now(timezone.utc)
        return replace(
            self,
            status=BookingStatus.COMPLETED,
            updated_at=now,
            version=self.version + 1,
        )


def check_booking_conflict(
    room_id: str,
    starts_at: datetime,
    ends_at: datetime,
    existing_bookings: Sequence[RoomBooking],
) -> None:
    for b in existing_bookings:
        if b.room_id == room_id and b.status == BookingStatus.CONFIRMED:
            if b.starts_at < ends_at and b.ends_at > starts_at:
                raise RoomSlotUnavailableError(
                    f"Room slot is no longer available (conflict with booking {b.id})"
                )
