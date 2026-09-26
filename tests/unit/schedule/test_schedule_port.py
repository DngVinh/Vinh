from __future__ import annotations

from datetime import datetime, timezone, timedelta
from pathlib import Path
import sys
import pytest

ROOT = Path(__file__).resolve().parents[3]
API_SRC = ROOT / "services" / "api" / "src"
if str(API_SRC) not in sys.path:
    sys.path.insert(0, str(API_SRC))

from campus247.ports.schedule import (
    ScheduleEntry,
    SchedulePage,
    SchedulePageMeta,
    StudentProfileSnapshot,
    ScheduleQuery,
    ScheduleReadPort,
)


def test_schedule_entry_valid():
    now = datetime.now(timezone.utc)
    entry = ScheduleEntry(
        id="01923456-789a-7def-8123-456789abcdef",
        course_code="IT101",
        course_name="Lập trình nâng cao",
        starts_at=now,
        ends_at=now + timedelta(hours=2),
        location_label="P.301-H1",
        instructor_display_name="TS. Nguyễn Văn A",
    )
    assert entry.course_code == "IT101"
    assert entry.source_system == "SYNTHETIC_SIS"


def test_schedule_entry_invalid_time_range():
    now = datetime.now(timezone.utc)
    with pytest.raises(ValueError, match="ends_at must be after starts_at"):
        ScheduleEntry(
            id="01923456-789a-7def-8123-456789abcdef",
            course_code="IT101",
            course_name="Lập trình nâng cao",
            starts_at=now,
            ends_at=now - timedelta(hours=1),
        )


def test_schedule_query_validation():
    now = datetime.now(timezone.utc)
    user_id = "01923456-789a-7def-8123-456789abcdef"
    
    query = ScheduleQuery(
        internal_user_id=user_id,
        starts_at=now,
        ends_at=now + timedelta(days=7),
        limit=20,
    )
    assert query.limit == 20

    with pytest.raises(ValueError, match="ends_at must be after starts_at"):
        ScheduleQuery(
            internal_user_id=user_id,
            starts_at=now,
            ends_at=now,
        )

    with pytest.raises(ValueError, match="limit must be between 1 and 100"):
        ScheduleQuery(
            internal_user_id=user_id,
            starts_at=now,
            ends_at=now + timedelta(days=1),
            limit=0,
        )

    with pytest.raises(ValueError, match="limit must be between 1 and 100"):
        ScheduleQuery(
            internal_user_id=user_id,
            starts_at=now,
            ends_at=now + timedelta(days=1),
            limit=101,
        )


def test_schedule_page_structure():
    now = datetime.now(timezone.utc)
    entry = ScheduleEntry(
        id="01923456-789a-7def-8123-456789abcdef",
        course_code="IT101",
        course_name="Lập trình nâng cao",
        starts_at=now,
        ends_at=now + timedelta(hours=2),
    )
    page = SchedulePage(
        items=(entry,),
        page=SchedulePageMeta(next_cursor=None, has_more=False, limit=20),
        timezone="Asia/Ho_Chi_Minh",
        freshness_timestamp=now,
        is_synthetic=True,
    )
    assert len(page.items) == 1
    assert page.is_synthetic is True
    assert page.timezone == "Asia/Ho_Chi_Minh"


@pytest.mark.asyncio
async def test_schedule_read_port_implementation():
    class DummyScheduleAdapter:
        async def get_student_profile(self, internal_user_id: str) -> StudentProfileSnapshot | None:
            return StudentProfileSnapshot(
                student_id=internal_user_id,
                student_code="651234",
                display_name="Nguyễn Văn A",
            )

        async def list_schedule(self, query: ScheduleQuery) -> SchedulePage:
            now = datetime.now(timezone.utc)
            return SchedulePage(
                items=(),
                page=SchedulePageMeta(next_cursor=None, has_more=False, limit=query.limit),
                freshness_timestamp=now,
            )

    adapter = DummyScheduleAdapter()
    assert isinstance(adapter, ScheduleReadPort)

    profile = await adapter.get_student_profile("01923456-789a-7def-8123-456789abcdef")
    assert profile is not None
    assert profile.student_code == "651234"
    assert profile.source_system == "SYNTHETIC_SIS"
