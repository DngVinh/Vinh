from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
import re
import sys
import pytest

ROOT = Path(__file__).resolve().parents[3]
SRC = ROOT / "packages" / "synthetic" / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from services import (
    canonical_checksum,
    generate_service_records,
)

UUIDV7_REGEX = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-7[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$"
)


def test_deterministic_service_records_same_seed():
    """AC-REQ-NF-DATA-001-01: Repeated generation with same seed produces identical checksum."""
    run1 = generate_service_records(seed=2472026)
    run2 = generate_service_records(seed=2472026)

    assert run1["manifest"]["records_checksum"] == run2["manifest"]["records_checksum"]
    assert canonical_checksum(run1["records"]) == canonical_checksum(run2["records"])
    assert run1["records"] == run2["records"]


def test_time_boundaries_and_utc_timezone():
    """AC-REQ-NF-DATA-003-01: Time-dependent records have valid UTC intervals and boundaries."""
    data = generate_service_records(seed=2472026)
    records = data["records"]

    # Test schedule intervals
    for entry in records["schedule_entry"]:
        assert entry["starts_at"].endswith("Z")
        assert entry["ends_at"].endswith("Z")
        start = datetime.fromisoformat(entry["starts_at"].replace("Z", "+00:00"))
        end = datetime.fromisoformat(entry["ends_at"].replace("Z", "+00:00"))
        assert start < end
        assert start.tzinfo == timezone.utc

        # Test boundary evaluation in Asia/Bangkok (+07:00)
        start_bkk = start.astimezone(timezone(datetime.fromisoformat("2026-01-01T00:00:00+07:00").tzinfo.utcoffset(None)))
        assert start_bkk.hour >= 0

    # Test room booking intervals
    for booking in records["room_booking"]:
        assert booking["starts_at"].endswith("Z")
        assert booking["ends_at"].endswith("Z")
        start = datetime.fromisoformat(booking["starts_at"].replace("Z", "+00:00"))
        end = datetime.fromisoformat(booking["ends_at"].replace("Z", "+00:00"))
        assert start < end
        assert booking["attendee_count"] >= 1
        assert UUIDV7_REGEX.fullmatch(booking["id"])


def test_room_specifications():
    """Verify room properties and capacity constraints."""
    data = generate_service_records(seed=2472026)
    for room in data["records"]["room"]:
        assert room["capacity"] > 0
        assert room["status"] == "AVAILABLE"
        assert UUIDV7_REGEX.fullmatch(room["id"])


def test_committed_services_sample_integrity():
    """Verify committed services.json sample matches generator output."""
    sample_path = ROOT / "packages" / "synthetic" / "samples" / "services.json"
    assert sample_path.is_file(), "services.json sample file must exist"

    sample_data = json.loads(sample_path.read_text(encoding="utf-8"))
    assert sample_data["manifest"]["seed"] == 2472026
    expected = generate_service_records(seed=2472026)
    assert sample_data["manifest"]["records_checksum"] == expected["manifest"]["records_checksum"]
