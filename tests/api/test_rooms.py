from __future__ import annotations

from datetime import datetime, timezone, timedelta
from pathlib import Path
import sys
from fastapi import FastAPI
from fastapi.testclient import TestClient
import pytest

ROOT = Path(__file__).resolve().parents[2]
API_SRC = ROOT / "services" / "api" / "src"
if str(API_SRC) not in sys.path:
    sys.path.insert(0, str(API_SRC))

from campus247.application.booking.availability import ExistingBooking, RoomInfo
from campus247.presentation.rooms import create_rooms_router


@pytest.fixture
def client_and_data():
    app = FastAPI()
    rooms = [
        RoomInfo(id="01923456-789a-7def-8123-456789abcde1", room_code="H1-301", display_name="Phòng 301", capacity=50, features=("WIFI",)),
        RoomInfo(id="01923456-789a-7def-8123-456789abcde2", room_code="H1-302", display_name="Phòng 302", capacity=20, features=("WIFI",)),
    ]
    now = datetime(2026, 10, 15, 8, 0, tzinfo=timezone.utc)
    bookings = [
        ExistingBooking(
            id="01923456-789a-7def-8123-456789abcde3",
            room_id="01923456-789a-7def-8123-456789abcde1",
            starts_at=now,
            ends_at=now + timedelta(hours=2),
            status="CONFIRMED",
        )
    ]
    router = create_rooms_router(rooms=rooms, bookings=bookings)
    app.include_router(router)
    return TestClient(app), rooms, bookings


def test_list_rooms(client_and_data):
    client, _, _ = client_and_data
    resp = client.get("/v1/rooms?minimum_capacity=30")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["items"]) == 1
    assert data["items"][0]["room_code"] == "H1-301"


def test_room_availability_not_found(client_and_data):
    client, _, _ = client_and_data
    resp = client.get(
        "/v1/rooms/01923456-789a-7def-8123-456789abcdee/availability?from=2026-10-15T08:00:00Z&to=2026-10-15T10:00:00Z"
    )
    assert resp.status_code == 404


def test_room_availability_invalid_range(client_and_data):
    client, rooms, _ = client_and_data
    r_id = rooms[0].id
    resp = client.get(
        f"/v1/rooms/{r_id}/availability?from=2026-10-15T10:00:00Z&to=2026-10-15T08:00:00Z"
    )
    assert resp.status_code == 422


def test_room_availability_with_conflict(client_and_data):
    client, rooms, _ = client_and_data
    r_id = rooms[0].id
    resp = client.get(
        f"/v1/rooms/{r_id}/availability?from=2026-10-15T07:00:00Z&to=2026-10-15T11:00:00Z"
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["room_id"] == r_id
    assert data["advisory"] is True
    assert len(data["unavailable_intervals"]) == 1
    assert data["unavailable_intervals"][0]["starts_at"] == "2026-10-15T08:00:00+00:00"


def test_room_availability_clean(client_and_data):
    client, rooms, _ = client_and_data
    r_id = rooms[1].id
    resp = client.get(
        f"/v1/rooms/{r_id}/availability?from=2026-10-15T07:00:00Z&to=2026-10-15T11:00:00Z"
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["room_id"] == r_id
    assert len(data["unavailable_intervals"]) == 0
