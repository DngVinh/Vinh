from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Sequence


@dataclass(frozen=True)
class RoomInfo:
    id: str
    room_code: str
    display_name: str
    capacity: int
    features: tuple[str, ...] = ()
    status: str = "AVAILABLE"


@dataclass(frozen=True)
class ExistingBooking:
    id: str
    room_id: str
    starts_at: datetime
    ends_at: datetime
    status: str = "CONFIRMED"


@dataclass(frozen=True)
class RoomAvailabilityQuery:
    starts_at: datetime
    ends_at: datetime
    minimum_capacity: int = 1
    required_features: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.ends_at <= self.starts_at:
            raise ValueError("ends_at must be after starts_at")
        if self.minimum_capacity < 1:
            raise ValueError("minimum_capacity must be >= 1")


class RoomAvailabilityService:
    def __init__(
        self,
        rooms: Sequence[RoomInfo] | None = None,
        bookings: Sequence[ExistingBooking] | None = None,
    ) -> None:
        self._rooms = list(rooms or [])
        self._bookings = list(bookings or [])

    def find_available_rooms(self, query: RoomAvailabilityQuery) -> list[RoomInfo]:
        available: list[RoomInfo] = []
        for room in self._rooms:
            if room.status != "AVAILABLE":
                continue
            if room.capacity < query.minimum_capacity:
                continue
            if query.required_features:
                if not set(query.required_features).issubset(set(room.features)):
                    continue

            has_overlap = any(
                b.room_id == room.id
                and b.status == "CONFIRMED"
                and b.starts_at < query.ends_at
                and b.ends_at > query.starts_at
                for b in self._bookings
            )
            if not has_overlap:
                available.append(room)

        return available

    def is_room_available(self, room_id: str, starts_at: datetime, ends_at: datetime) -> bool:
        if ends_at <= starts_at:
            raise ValueError("ends_at must be after starts_at")
        query = RoomAvailabilityQuery(starts_at=starts_at, ends_at=ends_at)
        available = self.find_available_rooms(query)
        return any(r.id == room_id for r in available)
