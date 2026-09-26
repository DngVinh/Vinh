from __future__ import annotations

import hashlib
import json
import random
from typing import Any

from identities import canonical_checksum, deterministic_uuid7, generate_identities

SAMPLE_COURSES = [
    ("IT201", "Lập trình Python và Ứng dụng", "H1-301", "ThS. Nguyễn Hoàng Long"),
    ("CS301", "Cơ sở dữ liệu nâng cao", "H1-302", "TS. Trần Văn Bách"),
    ("SE202", "Công nghệ phần mềm", "H2-201", "PGS.TS. Lê Thị Mai"),
    ("NW101", "Mạng máy tính cơ bản", "H2-202", "ThS. Phạm Quang Huy"),
]

ROOM_SPECS = [
    ("H1-301", "Phòng học đa năng H1-301", 50, ["PROJECTOR", "WIFI", "AIR_CONDITIONER"]),
    ("H1-302", "Phòng hội thảo sinh viên H1-302", 30, ["PROJECTOR", "WIFI", "WHITEBOARD"]),
    ("H2-201", "Phòng máy tính chuyên dụng H2-201", 40, ["COMPUTERS", "PROJECTOR", "AIR_CONDITIONER"]),
    ("H2-202", "Phòng thảo luận nhóm H2-202", 15, ["WIFI", "WHITEBOARD"]),
]


def generate_service_records(
    seed: int = 2472026,
    identity_data: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Generate deterministic synthetic service records (schedules, rooms, tickets, bookings)."""
    if identity_data is None:
        identity_data = generate_identities(seed=seed, student_count=10, staff_count=5)

    rng = random.Random(seed)
    students = identity_data["records"]["user_identity"][:5]

    schedules: list[dict[str, Any]] = []
    rooms: list[dict[str, Any]] = []
    tickets: list[dict[str, Any]] = []
    bookings: list[dict[str, Any]] = []

    # 1. Generate Rooms
    room_ids: dict[str, str] = {}
    for code, name, cap, feats in ROOM_SPECS:
        r_id = deterministic_uuid7(f"room-{seed}-{code}")
        room_ids[code] = r_id
        rooms.append({
            "id": r_id,
            "room_code": code,
            "display_name": name,
            "capacity": cap,
            "features": feats,
            "status": "AVAILABLE",
            "version": 1,
        })

    # 2. Generate Schedule Entries (Explicit UTC RFC3339, starts_at < ends_at)
    for s_idx, student in enumerate(students):
        student_id = student["id"]
        for c_idx, (c_code, c_name, loc, instructor) in enumerate(SAMPLE_COURSES):
            day = 15 + (s_idx + c_idx) % 10
            sch_id = deterministic_uuid7(f"schedule-{student_id}-{c_code}-{day}")
            starts_at = f"2026-10-{day:02d}T07:30:00Z"
            ends_at = f"2026-10-{day:02d}T10:30:00Z"

            schedules.append({
                "id": sch_id,
                "student_user_id": student_id,
                "source_system": "SYNTHETIC_SIS",
                "source_record_id": f"SIS-{student_id[:8]}-{c_code}",
                "course_code": c_code,
                "course_name": c_name,
                "starts_at": starts_at,
                "ends_at": ends_at,
                "location_label": loc,
                "instructor_display_name": instructor,
                "sync_version": 1,
            })

    # 3. Generate Tickets
    for idx, student in enumerate(students):
        student_id = student["id"]
        ticket_id = deterministic_uuid7(f"ticket-{student_id}-{idx}")
        tickets.append({
            "id": ticket_id,
            "requester_user_id": student_id,
            "category": "GENERAL_SUPPORT",
            "priority": "NORMAL",
            "status": "OPEN",
            "subject": f"Hỗ trợ thủ tục học vụ demo {idx + 1}",
            "description_redacted": "Yêu cầu hỗ trợ sinh viên thử nghiệm.",
            "queue_key": "HUCE_GENERAL",
            "version": 1,
        })

    # 4. Generate Room Bookings
    for idx, student in enumerate(students[:3]):
        student_id = student["id"]
        room_code = ROOM_SPECS[idx % len(ROOM_SPECS)][0]
        room_id = room_ids[room_code]
        booking_id = deterministic_uuid7(f"booking-{student_id}-{idx}")
        action_exec_id = deterministic_uuid7(f"action-exec-{booking_id}")
        day = 20 + idx

        bookings.append({
            "id": booking_id,
            "room_id": room_id,
            "requester_user_id": student_id,
            "starts_at": f"2026-10-{day:02d}T14:00:00Z",
            "ends_at": f"2026-10-{day:02d}T16:00:00Z",
            "purpose_redacted": "Học nhóm bài tập lớn",
            "attendee_count": 5,
            "status": "CONFIRMED",
            "action_execution_id": action_exec_id,
            "version": 1,
        })

    records = {
        "room": rooms,
        "schedule_entry": schedules,
        "ticket": tickets,
        "room_booking": bookings,
    }
    records_checksum = canonical_checksum(records)

    manifest = {
        "dataset_id": f"DATASET-SYNTH-SERVICES-SEED{seed}",
        "version": "1.0.0",
        "generator_version": "1.0.0",
        "seed": seed,
        "locale": "vi-VN",
        "simulation_label": True,
        "record_counts": {k: len(v) for k, v in records.items()},
        "records_checksum": records_checksum,
    }

    return {"manifest": manifest, "records": records}
