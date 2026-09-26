from __future__ import annotations

from datetime import datetime, timezone, timedelta
from pathlib import Path
import sys
import pytest

ROOT = Path(__file__).resolve().parents[3]
API_SRC = ROOT / "services" / "api" / "src"
if str(API_SRC) not in sys.path:
    sys.path.insert(0, str(API_SRC))

from campus247.domain.booking.model import (
    BookingStatus,
    InvalidBookingStateError,
    InvalidBookingValidationError,
    RoomBooking,
    RoomSlotUnavailableError,
    check_booking_conflict,
)


def test_confirm_booking_valid():
    now = datetime.now(timezone.utc)
    booking = RoomBooking.confirm_booking(
        room_id="01923456-789a-7def-8123-456789abcde1",
        requester_user_id="01923456-789a-7def-8123-456789abcde2",
        starts_at=now,
        ends_at=now + timedelta(hours=2),
        purpose_redacted="Họp CLB Tin học",
        attendee_count=10,
        action_execution_id="01923456-789a-7def-8123-456789abcde3",
    )
    assert booking.status == BookingStatus.CONFIRMED
    assert booking.attendee_count == 10
    assert booking.version == 1


def test_booking_validation_errors():
    now = datetime.now(timezone.utc)
    with pytest.raises(InvalidBookingValidationError, match="ends_at must be after starts_at"):
        RoomBooking.confirm_booking(
            room_id="01923456-789a-7def-8123-456789abcde1",
            requester_user_id="01923456-789a-7def-8123-456789abcde2",
            starts_at=now,
            ends_at=now - timedelta(hours=1),
            purpose_redacted="Họp",
            attendee_count=10,
            action_execution_id="01923456-789a-7def-8123-456789abcde3",
        )

    with pytest.raises(InvalidBookingValidationError, match="attendee_count must be >= 1"):
        RoomBooking.confirm_booking(
            room_id="01923456-789a-7def-8123-456789abcde1",
            requester_user_id="01923456-789a-7def-8123-456789abcde2",
            starts_at=now,
            ends_at=now + timedelta(hours=2),
            purpose_redacted="Họp",
            attendee_count=0,
            action_execution_id="01923456-789a-7def-8123-456789abcde3",
        )


def test_conflict_check_rejects_overlap():
    now = datetime.now(timezone.utc)
    room_id = "01923456-789a-7def-8123-456789abcde1"
    existing = RoomBooking.confirm_booking(
        room_id=room_id,
        requester_user_id="01923456-789a-7def-8123-456789abcde2",
        starts_at=now,
        ends_at=now + timedelta(hours=2),
        purpose_redacted="Họp",
        attendee_count=5,
        action_execution_id="01923456-789a-7def-8123-456789abcde3",
    )

    # Overlaps [now+1, now+3]
    with pytest.raises(RoomSlotUnavailableError, match="Room slot is no longer available"):
        check_booking_conflict(
            room_id=room_id,
            starts_at=now + timedelta(hours=1),
            ends_at=now + timedelta(hours=3),
            existing_bookings=[existing],
        )


def test_conflict_check_allows_adjacent_and_cancelled():
    now = datetime.now(timezone.utc)
    room_id = "01923456-789a-7def-8123-456789abcde1"
    existing = RoomBooking.confirm_booking(
        room_id=room_id,
        requester_user_id="01923456-789a-7def-8123-456789abcde2",
        starts_at=now,
        ends_at=now + timedelta(hours=2),
        purpose_redacted="Họp",
        attendee_count=5,
        action_execution_id="01923456-789a-7def-8123-456789abcde3",
    )

    # Adjacent: [now+2, now+4] -> allowed
    check_booking_conflict(
        room_id=room_id,
        starts_at=now + timedelta(hours=2),
        ends_at=now + timedelta(hours=4),
        existing_bookings=[existing],
    )

    # Cancelled: cancelled booking doesn't conflict
    cancelled = existing.cancel()
    check_booking_conflict(
        room_id=room_id,
        starts_at=now,
        ends_at=now + timedelta(hours=2),
        existing_bookings=[cancelled],
    )
