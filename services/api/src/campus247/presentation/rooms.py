from __future__ import annotations

from datetime import datetime
from typing import Sequence
from fastapi import APIRouter, HTTPException, Query, Request
from starlette.responses import JSONResponse

from campus247.application.booking.availability import ExistingBooking, RoomInfo


def create_rooms_router(
    rooms: Sequence[RoomInfo],
    bookings: Sequence[ExistingBooking] | None = None,
) -> APIRouter:
    router = APIRouter(tags=["Rooms"])
    room_list = list(rooms)
    booking_list = list(bookings or [])

    @router.get("/v1/rooms")
    async def list_rooms(
        cursor: str | None = Query(None),
        limit: int = Query(20, ge=1, le=100),
        minimum_capacity: int | None = Query(None, ge=1, le=1000),
    ) -> JSONResponse:
        filtered = room_list
        if minimum_capacity is not None:
            filtered = [r for r in filtered if r.capacity >= minimum_capacity]

        filtered.sort(key=lambda r: (r.room_code, r.id))

        offset = 0
        if cursor:
            try:
                offset = int(cursor)
            except ValueError:
                offset = 0

        paged = filtered[offset : offset + limit]
        has_more = (offset + limit) < len(filtered)
        next_cursor = str(offset + limit) if has_more else None

        items = [
            {
                "id": r.id,
                "room_code": r.room_code,
                "display_name": r.display_name,
                "capacity": r.capacity,
                "features": list(r.features),
                "status": r.status,
            }
            for r in paged
        ]

        content = {
            "items": items,
            "page": {
                "next_cursor": next_cursor,
                "has_more": has_more,
                "limit": limit,
            },
        }
        return JSONResponse(status_code=200, content=content)

    @router.get("/v1/rooms/{room_id}/availability")
    async def get_room_availability(
        room_id: str,
        from_time: str = Query(..., alias="from"),
        to_time: str = Query(..., alias="to"),
    ) -> JSONResponse:
        room = next((r for r in room_list if r.id == room_id), None)
        if not room:
            raise HTTPException(status_code=404, detail="Room not found")

        try:
            starts_at = datetime.fromisoformat(from_time.replace("Z", "+00:00"))
            ends_at = datetime.fromisoformat(to_time.replace("Z", "+00:00"))
        except Exception:
            raise HTTPException(status_code=422, detail="Invalid date format for from/to")

        if starts_at >= ends_at:
            raise HTTPException(status_code=422, detail="'from' must be before 'to'")

        conflicts = [
            b
            for b in booking_list
            if b.room_id == room_id
            and b.status == "CONFIRMED"
            and b.starts_at < ends_at
            and b.ends_at > starts_at
        ]

        intervals = [
            {
                "starts_at": b.starts_at.isoformat(),
                "ends_at": b.ends_at.isoformat(),
            }
            for b in conflicts
        ]

        content = {
            "room_id": room_id,
            "from": from_time,
            "to": to_time,
            "unavailable_intervals": intervals,
            "advisory": True,
        }
        return JSONResponse(status_code=200, content=content, headers={"Cache-Control": "no-store"})

    return router
