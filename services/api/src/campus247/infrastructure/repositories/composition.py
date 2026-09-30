from __future__ import annotations

from typing import Any

from campus247.application.booking.availability import ExistingBooking, RoomInfo
from campus247.infrastructure.schedule.synthetic import SyntheticScheduleAdapter


class RepositoryComposition:
    """Explicit repository composition root for the application.
    
    Responsible for resolving external adapters based on the environment
    and ensuring production deployments fail closed if durable adapters are missing.
    """
    
    ticket_store: dict[str, Any]
    doc_store: dict[str, Any]
    handover_store: dict[str, Any]
    sources_store: dict[str, Any]
    versions_store: dict[str, Any]
    rooms_list: list[RoomInfo]
    bookings_list: list[ExistingBooking]
    schedule_adapter: Any
    
    def __init__(self, environment: str):
        self.environment = environment
        
        if self.environment == "production":
            # In production, we MUST not use in-memory fallbacks.
            # Fail closed and identify missing adapters.
            missing_adapters = [
                "ticket_store", 
                "doc_store", 
                "handover_store",
                "sources_store",
                "versions_store",
                "schedule_adapter",
                "rooms_list",
                "bookings_list"
            ]
            raise RuntimeError(
                f"Startup aborted: production environment requires durable adapters. "
                f"Missing production configurations for: {', '.join(missing_adapters)}"
            )
            
        # Development / Testing synthetic adapters
        self.ticket_store = {}
        self.doc_store = {}
        self.handover_store = {}
        self.sources_store = {}
        self.versions_store = {}
        
        self.rooms_list = [
            RoomInfo(
                id="01923456-789a-7def-8123-456789abcde1",
                room_code="H1-301",
                display_name="Phòng 301 - Giảng đường H1",
                capacity=50,
                features=("WIFI", "PROJECTOR"),
            ),
            RoomInfo(
                id="01923456-789a-7def-8123-456789abcde2",
                room_code="H1-302",
                display_name="Phòng 302 - Giảng đường H1",
                capacity=25,
                features=("WIFI",),
            ),
            RoomInfo(
                id="01923456-789a-7def-8123-456789abcde3",
                room_code="H2-101",
                display_name="Hội trường H2",
                capacity=150,
                features=("PROJECTOR", "MIC", "STAGE"),
            ),
        ]
        self.bookings_list = []
        self.schedule_adapter = SyntheticScheduleAdapter()
