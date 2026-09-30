from __future__ import annotations

import concurrent.futures
from datetime import datetime, timezone, timedelta
from pathlib import Path
import sys
import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

ROOT = Path(__file__).resolve().parents[2]
API_SRC = ROOT / "services" / "api" / "src"
if str(API_SRC) not in sys.path:
    sys.path.insert(0, str(API_SRC))

from campus247.domain.shared.values import generate_uuid7
from campus247.infrastructure.repositories.bookings import (
    BookingOverlapError,
    DatabaseBookingRepository,
    IdempotencyConflictError,
)
import importlib.util
_mig_path = ROOT / "services" / "api" / "migrations" / "versions" / "booking_overlap_guard.py"
_mig_spec = importlib.util.spec_from_file_location("booking_overlap_guard", _mig_path)
_mig_mod = importlib.util.module_from_spec(_mig_spec)
_mig_spec.loader.exec_module(_mig_mod)
preflight_check = _mig_mod.preflight_check


@pytest.fixture
def db_engine(tmp_path):
    # Use SQLite file for multi-thread concurrency support
    db_file = tmp_path / "test_concurrency.db"
    engine = create_engine(
        f"sqlite:///{db_file}?timeout=20",
        connect_args={"check_same_thread": False},
    )
    with engine.begin() as conn:
        conn.execute(text("PRAGMA journal_mode=WAL;"))
        # Create minimal tables for testing
        conn.execute(text("""
            CREATE TABLE room (
                id TEXT PRIMARY KEY,
                room_code TEXT UNIQUE NOT NULL,
                display_name TEXT NOT NULL,
                capacity INTEGER NOT NULL,
                features TEXT NOT NULL DEFAULT '[]',
                status TEXT NOT NULL,
                version INTEGER NOT NULL DEFAULT 1
            );
        """))
        conn.execute(text("""
            CREATE TABLE room_booking (
                id TEXT PRIMARY KEY,
                room_id TEXT NOT NULL,
                requester_user_id TEXT NOT NULL,
                starts_at TIMESTAMP NOT NULL,
                ends_at TIMESTAMP NOT NULL,
                purpose_redacted TEXT NOT NULL,
                attendee_count INTEGER NOT NULL,
                status TEXT NOT NULL,
                action_execution_id TEXT NOT NULL,
                idempotency_key TEXT UNIQUE,
                payload_hash TEXT,
                cancelled_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                version INTEGER NOT NULL DEFAULT 1
            );
        """))
        # Seed test room
        conn.execute(text("""
            INSERT INTO room (id, room_code, display_name, capacity, status)
            VALUES ('room-101', 'H1-101', 'Phòng Hội thảo H1-101', 50, 'AVAILABLE');
        """))
    return engine


def test_concurrent_overlapping_bookings(db_engine):
    """AC-TASK-DB-BOOKFIX-001-01: At most one conflicting active booking commits under concurrent transactions."""
    now = datetime.now(timezone.utc).replace(second=0, microsecond=0)
    start_time = now + timedelta(days=1, hours=2)
    end_time = start_time + timedelta(hours=2)

    repo = DatabaseBookingRepository(db_engine)

    def attempt_booking(user_suffix: str):
        try:
            return repo.create_booking(
                booking_id=generate_uuid7(),
                room_id="room-101",
                requester_user_id=f"user-{user_suffix}",
                starts_at=start_time,
                ends_at=end_time,
                purpose_redacted="Họp CLB Nghiên cứu khoa học",
                attendee_count=10,
                action_execution_id=generate_uuid7(),
                idempotency_key=f"idem-key-{user_suffix}",
            )
        except BookingOverlapError:
            return "OVERLAP_REJECTED"

    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(attempt_booking, f"worker-{i}") for i in range(5)]
        results = [f.result() for f in futures]

    # Exactly one succeeded and the rest were rejected due to overlap
    success_count = sum(1 for r in results if r != "OVERLAP_REJECTED")
    overlap_count = sum(1 for r in results if r == "OVERLAP_REJECTED")

    assert success_count == 1
    assert overlap_count == 4


def test_boundary_touching_slots_allowed(db_engine):
    """Slots that touch boundaries (end of slot A == start of slot B) do not conflict."""
    now = datetime.now(timezone.utc).replace(second=0, microsecond=0)
    slot1_start = now + timedelta(days=2, hours=8)
    slot1_end = slot1_start + timedelta(hours=1)
    slot2_start = slot1_end  # exactly touching
    slot2_end = slot2_start + timedelta(hours=1)

    repo = DatabaseBookingRepository(db_engine)

    b1 = repo.create_booking(
        booking_id=generate_uuid7(),
        room_id="room-101",
        requester_user_id="user-1",
        starts_at=slot1_start,
        ends_at=slot1_end,
        purpose_redacted="Slot 1",
        attendee_count=5,
        action_execution_id=generate_uuid7(),
        idempotency_key="key-touch-1",
    )
    b2 = repo.create_booking(
        booking_id=generate_uuid7(),
        room_id="room-101",
        requester_user_id="user-2",
        starts_at=slot2_start,
        ends_at=slot2_end,
        purpose_redacted="Slot 2",
        attendee_count=5,
        action_execution_id=generate_uuid7(),
        idempotency_key="key-touch-2",
    )
    assert b1.id != b2.id
    assert b1.status == "CONFIRMED"
    assert b2.status == "CONFIRMED"


def test_cancelled_booking_does_not_block_new_booking(db_engine):
    """Cancelled booking leaves time slot available for a new booking."""
    now = datetime.now(timezone.utc).replace(second=0, microsecond=0)
    start_time = now + timedelta(days=3, hours=10)
    end_time = start_time + timedelta(hours=1)

    repo = DatabaseBookingRepository(db_engine)

    b1 = repo.create_booking(
        booking_id=generate_uuid7(),
        room_id="room-101",
        requester_user_id="user-1",
        starts_at=start_time,
        ends_at=end_time,
        purpose_redacted="To be cancelled",
        attendee_count=5,
        action_execution_id=generate_uuid7(),
        idempotency_key="key-cancel-1",
    )
    repo.cancel_booking(b1.id)

    # Now another booking for the same time should succeed
    b2 = repo.create_booking(
        booking_id=generate_uuid7(),
        room_id="room-101",
        requester_user_id="user-2",
        starts_at=start_time,
        ends_at=end_time,
        purpose_redacted="Replacement booking",
        attendee_count=5,
        action_execution_id=generate_uuid7(),
        idempotency_key="key-cancel-2",
    )
    assert b2.status == "CONFIRMED"


def test_same_key_same_payload_returns_original(db_engine):
    """AC-TASK-DB-BOOKFIX-001-02: Same-key same-payload retries return the original outcome."""
    now = datetime.now(timezone.utc).replace(second=0, microsecond=0)
    start_time = now + timedelta(days=4, hours=14)
    end_time = start_time + timedelta(hours=2)

    repo = DatabaseBookingRepository(db_engine)

    b1 = repo.create_booking(
        booking_id=generate_uuid7(),
        room_id="room-101",
        requester_user_id="user-idem",
        starts_at=start_time,
        ends_at=end_time,
        purpose_redacted="Original Request",
        attendee_count=8,
        action_execution_id=generate_uuid7(),
        idempotency_key="idempotent-key-100",
    )

    # Retry identical request with same key
    b2 = repo.create_booking(
        booking_id=generate_uuid7(),  # Even if new client booking_id passed
        room_id="room-101",
        requester_user_id="user-idem",
        starts_at=start_time,
        ends_at=end_time,
        purpose_redacted="Original Request",
        attendee_count=8,
        action_execution_id=generate_uuid7(),
        idempotency_key="idempotent-key-100",
    )

    assert b1.id == b2.id
    assert b2.status == "CONFIRMED"


def test_same_key_different_payload_fails(db_engine):
    """AC-TASK-DB-BOOKFIX-001-02: Same-key different-payload retries fail."""
    now = datetime.now(timezone.utc).replace(second=0, microsecond=0)
    start_time = now + timedelta(days=5, hours=9)
    end_time = start_time + timedelta(hours=1)

    repo = DatabaseBookingRepository(db_engine)

    repo.create_booking(
        booking_id=generate_uuid7(),
        room_id="room-101",
        requester_user_id="user-conflict",
        starts_at=start_time,
        ends_at=end_time,
        purpose_redacted="First Request",
        attendee_count=5,
        action_execution_id=generate_uuid7(),
        idempotency_key="conflict-key-999",
    )

    # Second request with same key but different room/time
    with pytest.raises(IdempotencyConflictError):
        repo.create_booking(
            booking_id=generate_uuid7(),
            room_id="room-101",
            requester_user_id="user-conflict",
            starts_at=start_time + timedelta(hours=5),  # Different time!
            ends_at=end_time + timedelta(hours=5),
            purpose_redacted="Tampered Request",
            attendee_count=5,
            action_execution_id=generate_uuid7(),
            idempotency_key="conflict-key-999",
        )


def test_migration_preflight_detects_legacy_conflicts(db_engine):
    """AC-TASK-DB-BOOKFIX-001-03: Migration preflight halts on ambiguous legacy conflicts."""
    now = datetime.now(timezone.utc).replace(second=0, microsecond=0)
    t1 = now + timedelta(days=6, hours=10)
    t2 = t1 + timedelta(hours=2)

    # Insert conflicting legacy data directly
    with db_engine.begin() as conn:
        conn.execute(text("""
            INSERT INTO room_booking (id, room_id, requester_user_id, starts_at, ends_at, purpose_redacted, attendee_count, status, action_execution_id)
            VALUES 
                ('legacy-1', 'room-101', 'u1', :s, :e, 'Legacy 1', 5, 'CONFIRMED', 'exec-1'),
                ('legacy-2', 'room-101', 'u2', :s, :e, 'Legacy 2', 5, 'CONFIRMED', 'exec-2');
        """), {"s": t1, "e": t2})

    with pytest.raises(RuntimeError) as exc_info:
        with db_engine.connect() as conn:
            preflight_check(conn)

    assert "Preflight" in str(exc_info.value)
    assert "overlapping active bookings detected" in str(exc_info.value)
