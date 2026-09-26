from __future__ import annotations

from datetime import datetime, timezone, timedelta
from pathlib import Path
import sys
import pytest

ROOT = Path(__file__).resolve().parents[3]
API_SRC = ROOT / "services" / "api" / "src"
if str(API_SRC) not in sys.path:
    sys.path.insert(0, str(API_SRC))

from campus247.application.booking.availability import (
    ExistingBooking,
    RoomAvailabilityQuery,
    RoomAvailabilityService,
    RoomInfo,
)


@pytest.fixture
def sample_rooms():
    return [
        RoomInfo(id="r-1", room_code="H1-301", display_name="Phòng 301", capacity=50, features=("PROJECTOR", "WIFI")),
        RoomInfo(id="r-2", room_code="H1-302", display_name="Phòng 302", capacity=20, features=("WIFI",)),
        RoomInfo(id="r-3", room_code="H2-101", display_name="Phòng 101", capacity=100, features=("PROJECTOR",), status="MAINTENANCE"),
    ]


def test_find_available_rooms_no_bookings(sample_rooms):
    service = RoomAvailabilityService(rooms=sample_rooms)
    now = datetime.now(timezone.utc)
    query = RoomAvailabilityQuery(
        starts_at=now,
        ends_at=now + timedelta(hours=2),
        minimum_capacity=30,
    )
    available = service.find_available_rooms(query)
    assert len(available) == 1
    assert available[0].room_code == "H1-301"


def test_find_available_rooms_overlap_exclusion(sample_rooms):
    now = datetime.now(timezone.utc)
    bookings = [
        ExistingBooking(
            id="b-1",
            room_id="r-1",
            starts_at=now + timedelta(hours=1),
            ends_at=now + timedelta(hours=3),
            status="CONFIRMED",
        )
    ]
    service = RoomAvailabilityService(rooms=sample_rooms, bookings=bookings)

    # Query overlaps b-1 [now, now+2] with [now+1, now+3]
    query = RoomAvailabilityQuery(
        starts_at=now,
        ends_at=now + timedelta(hours=2),
        minimum_capacity=10,
    )
    available = service.find_available_rooms(query)
    codes = [r.room_code for r in available]
    assert "H1-301" not in codes
    assert "H1-302" in codes


def test_find_available_rooms_adjacent_allowed(sample_rooms):
    now = datetime.now(timezone.utc)
    bookings = [
        ExistingBooking(
            id="b-1",
            room_id="r-1",
            starts_at=now,
            ends_at=now + timedelta(hours=2),
            status="CONFIRMED",
        )
    ]
    service = RoomAvailabilityService(rooms=sample_rooms, bookings=bookings)

    # Query starts exactly when b-1 ends [now+2, now+4]
    query = RoomAvailabilityQuery(
        starts_at=now + timedelta(hours=2),
        ends_at=now + timedelta(hours=4),
        minimum_capacity=10,
    )
    available = service.find_available_rooms(query)
    codes = [r.room_code for r in available]
    assert "H1-301" in codes


def test_find_available_rooms_cancelled_ignored(sample_rooms):
    now = datetime.now(timezone.utc)
    bookings = [
        ExistingBooking(
            id="b-1",
            room_id="r-1",
            starts_at=now,
            ends_at=now + timedelta(hours=2),
            status="CANCELLED",
        )
    ]
    service = RoomAvailabilityService(rooms=sample_rooms, bookings=bookings)

    query = RoomAvailabilityQuery(
        starts_at=now,
        ends_at=now + timedelta(hours=2),
        minimum_capacity=10,
    )
    available = service.find_available_rooms(query)
    codes = [r.room_code for r in available]
    assert "H1-301" in codes


def test_invalid_range_raises_value_error():
    now = datetime.now(timezone.utc)
    with pytest.raises(ValueError, match="ends_at must be after starts_at"):
        RoomAvailabilityQuery(
            starts_at=now,
            ends_at=now - timedelta(hours=1),
        )
