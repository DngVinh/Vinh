from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import sys
import pytest

ROOT = Path(__file__).resolve().parents[3]
API_SRC = ROOT / "services" / "api" / "src"
if str(API_SRC) not in sys.path:
    sys.path.insert(0, str(API_SRC))

from campus247.ports.schedule import ScheduleQuery, ScheduleReadPort
from campus247.infrastructure.schedule.synthetic import SyntheticScheduleAdapter


@pytest.fixture
def adapter() -> SyntheticScheduleAdapter:
    return SyntheticScheduleAdapter()


def test_adapter_satisfies_port(adapter: SyntheticScheduleAdapter):
    assert isinstance(adapter, ScheduleReadPort)


@pytest.mark.asyncio
async def test_get_student_profile(adapter: SyntheticScheduleAdapter):
    # Known synthetic student from identities.json
    student_id = "4b419a1b-6d41-7dfb-8943-2edd9f071385"
    profile = await adapter.get_student_profile(student_id)
    assert profile is not None
    assert profile.student_id == student_id
    assert profile.source_system == "SYNTHETIC_SIS"

    # Non-existent student
    unknown_id = "01923456-789a-7def-8123-456789abcdef"
    unknown_profile = await adapter.get_student_profile(unknown_id)
    assert unknown_profile is None


@pytest.mark.asyncio
async def test_list_schedule_isolation(adapter: SyntheticScheduleAdapter):
    student_1 = "4b419a1b-6d41-7dfb-8943-2edd9f071385"
    student_2 = "87cb3594-5226-724e-b5c0-bbd4f3b584a5"

    query = ScheduleQuery(
        internal_user_id=student_1,
        starts_at=datetime(2026, 10, 1, tzinfo=timezone.utc),
        ends_at=datetime(2026, 10, 31, tzinfo=timezone.utc),
        limit=50,
    )
    res = await adapter.list_schedule(query)
    assert res.is_synthetic is True
    assert res.timezone == "Asia/Ho_Chi_Minh"
    assert res.freshness_timestamp is not None
    assert len(res.items) > 0

    # Ensure no items belong to student_2 or other students
    # (Checking that query for student_2 returns different items or distinct)
    query_2 = ScheduleQuery(
        internal_user_id=student_2,
        starts_at=datetime(2026, 10, 1, tzinfo=timezone.utc),
        ends_at=datetime(2026, 10, 31, tzinfo=timezone.utc),
        limit=50,
    )
    res_2 = await adapter.list_schedule(query_2)
    s1_ids = {item.id for item in res.items}
    s2_ids = {item.id for item in res_2.items}
    assert s1_ids.isdisjoint(s2_ids)


@pytest.mark.asyncio
async def test_list_schedule_range_filter(adapter: SyntheticScheduleAdapter):
    student_id = "4b419a1b-6d41-7dfb-8943-2edd9f071385"
    query = ScheduleQuery(
        internal_user_id=student_id,
        starts_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        ends_at=datetime(2026, 1, 31, tzinfo=timezone.utc),
        limit=50,
    )
    res = await adapter.list_schedule(query)
    assert len(res.items) == 0
    assert res.page.has_more is False
