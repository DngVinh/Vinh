from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Protocol, runtime_checkable

from campus247.domain.shared.values import is_valid_uuid7


@dataclass(frozen=True)
class ScheduleEntry:
    id: str
    course_code: str
    course_name: str
    starts_at: datetime
    ends_at: datetime
    location_label: str | None = None
    instructor_display_name: str | None = None
    source_system: str = "SYNTHETIC_SIS"

    def __post_init__(self) -> None:
        if self.ends_at <= self.starts_at:
            raise ValueError("ends_at must be after starts_at")


@dataclass(frozen=True)
class SchedulePageMeta:
    next_cursor: str | None = None
    has_more: bool = False
    limit: int = 20


@dataclass(frozen=True)
class SchedulePage:
    items: tuple[ScheduleEntry, ...]
    page: SchedulePageMeta
    freshness_timestamp: datetime
    timezone: str = "Asia/Ho_Chi_Minh"
    is_synthetic: bool = True


@dataclass(frozen=True)
class StudentProfileSnapshot:
    student_id: str
    student_code: str
    display_name: str
    faculty_code: str | None = None
    academic_year: str | None = None
    status: str = "ACTIVE"
    source_system: str = "SYNTHETIC_SIS"


@dataclass(frozen=True)
class ScheduleQuery:
    internal_user_id: str
    starts_at: datetime
    ends_at: datetime
    cursor: str | None = None
    limit: int = 20

    def __post_init__(self) -> None:
        if not is_valid_uuid7(self.internal_user_id):
            raise ValueError(f"internal_user_id must be a valid UUIDv7 string, got: {self.internal_user_id}")
        if self.ends_at <= self.starts_at:
            raise ValueError("ends_at must be after starts_at")
        if not (1 <= self.limit <= 100):
            raise ValueError("limit must be between 1 and 100")


@runtime_checkable
class ScheduleReadPort(Protocol):
    async def get_student_profile(self, internal_user_id: str) -> StudentProfileSnapshot | None:
        ...

    async def list_schedule(self, query: ScheduleQuery) -> SchedulePage:
        ...
