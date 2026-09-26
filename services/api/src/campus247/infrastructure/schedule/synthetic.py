from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[6]
SYNTH_SRC = ROOT / "packages" / "synthetic" / "src"
if str(SYNTH_SRC) not in sys.path:
    sys.path.insert(0, str(SYNTH_SRC))

from campus247.ports.schedule import (
    ScheduleEntry,
    SchedulePage,
    SchedulePageMeta,
    ScheduleQuery,
    ScheduleReadPort,
    StudentProfileSnapshot,
)


class SyntheticScheduleAdapter:
    def __init__(self, seed: int = 2472026) -> None:
        services_json = ROOT / "packages" / "synthetic" / "samples" / "services.json"
        identities_json = ROOT / "packages" / "synthetic" / "samples" / "identities.json"

        if services_json.exists() and identities_json.exists():
            with open(services_json, "r", encoding="utf-8") as f:
                srv_data = json.load(f)
            with open(identities_json, "r", encoding="utf-8") as f:
                idt_data = json.load(f)
        else:
            from identities import generate_identities
            from services import generate_service_records
            idt_data = generate_identities(seed=seed)
            srv_data = generate_service_records(seed=seed, identity_data=idt_data)

        self._users = {u["id"]: u for u in idt_data["records"]["user_identity"]}
        self._profiles = {p["user_id"]: p for p in idt_data["records"]["student_profile"]}
        self._schedules = srv_data["records"]["schedule_entry"]

    async def get_student_profile(self, internal_user_id: str) -> StudentProfileSnapshot | None:
        user = self._users.get(internal_user_id)
        prof = self._profiles.get(internal_user_id)
        if not user or not prof:
            return None

        return StudentProfileSnapshot(
            student_id=internal_user_id,
            student_code=prof["student_code"],
            display_name=user["display_name"],
            faculty_code=prof.get("faculty_code"),
            academic_year=prof.get("academic_year"),
            status=user.get("status", "ACTIVE"),
            source_system="SYNTHETIC_SIS",
        )

    async def list_schedule(self, query: ScheduleQuery) -> SchedulePage:
        # Strict actor isolation
        student_entries = [
            s for s in self._schedules if s.get("student_user_id") == query.internal_user_id
        ]

        matched: list[ScheduleEntry] = []
        for s in student_entries:
            starts_at = datetime.fromisoformat(s["starts_at"])
            ends_at = datetime.fromisoformat(s["ends_at"])
            # Entry overlaps with query range
            if starts_at < query.ends_at and ends_at > query.starts_at:
                matched.append(
                    ScheduleEntry(
                        id=s["id"],
                        course_code=s["course_code"],
                        course_name=s["course_name"],
                        starts_at=starts_at,
                        ends_at=ends_at,
                        location_label=s.get("location_label"),
                        instructor_display_name=s.get("instructor_display_name"),
                        source_system="SYNTHETIC_SIS",
                    )
                )

        # Order by starts_at ASC, id ASC
        matched.sort(key=lambda x: (x.starts_at, x.id))

        offset = 0
        if query.cursor:
            try:
                offset = int(query.cursor)
            except ValueError:
                offset = 0

        paged_items = matched[offset : offset + query.limit]
        has_more = (offset + query.limit) < len(matched)
        next_cursor = str(offset + query.limit) if has_more else None

        return SchedulePage(
            items=tuple(paged_items),
            page=SchedulePageMeta(
                next_cursor=next_cursor,
                has_more=has_more,
                limit=query.limit,
            ),
            freshness_timestamp=datetime.now(timezone.utc),
            timezone="Asia/Ho_Chi_Minh",
            is_synthetic=True,
        )
