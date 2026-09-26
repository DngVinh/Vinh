from __future__ import annotations

import asyncio
from datetime import datetime
import json
import os
from pathlib import Path
import sys
from typing import Any

# 1. Adds project paths to sys.path
ROOT = Path(__file__).resolve().parents[1]
API_SRC = ROOT / "services" / "api" / "src"
SYNTH_SRC = ROOT / "packages" / "synthetic" / "src"

for p in (str(SYNTH_SRC), str(API_SRC)):
    if p not in sys.path:
        sys.path.insert(0, p)

import asyncpg
from identities import generate_identities
from knowledge import generate_knowledge_corpus
from services import generate_service_records


def load_database_url() -> str:
    """Load DATABASE_URL from .env file or environment."""
    env_file = ROOT / ".env"
    if env_file.is_file():
        for line in env_file.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if line.startswith("DATABASE_URL="):
                val = line.split("=", 1)[1].strip()
                if (val.startswith('"') and val.endswith('"')) or (val.startswith("'") and val.endswith("'")):
                    val = val[1:-1]
                return val
    return os.getenv("DATABASE_URL", "postgresql://campus247:campus247_local_dev@localhost:5433/campus247_local")


def normalize_asyncpg_url(url: str) -> str:
    """Convert SQLAlchemy async URL to standard asyncpg connection URL."""
    prefix = "postgresql+asyncpg://"
    if url.startswith(prefix):
        return "postgresql://" + url[len(prefix):]
    return url


def parse_dt(val: Any) -> datetime | None:
    if val is None:
        return None
    if isinstance(val, datetime):
        return val
    if isinstance(val, str):
        # Support ISO 8601 with trailing Z or timezone offset
        return datetime.fromisoformat(val.replace("Z", "+00:00"))
    return None


def prepare_seed_data() -> dict[str, list[tuple[Any, ...]]]:
    """Generate and map synthetic records for DB insertion."""
    identity_data = generate_identities(seed=2472026, student_count=100, staff_count=20)
    service_data = generate_service_records(seed=2472026, identity_data=identity_data)
    knowledge_data = generate_knowledge_corpus(seed=2026, include_courses=True)

    # 1. user_identity
    user_rows: list[tuple[Any, ...]] = [
        (
            u["id"],
            u["display_name"],
            u.get("primary_email"),
            u["status"],
            u.get("is_synthetic", True),
            u.get("version", 1),
        )
        for u in identity_data["records"]["user_identity"]
    ]

    # 2. identity_link
    link_rows: list[tuple[Any, ...]] = [
        (
            link["id"],
            link["user_id"],
            link["issuer"],
            link["subject"],
            link["provider_type"],
            link["claims_version"],
        )
        for link in identity_data["records"]["identity_link"]
    ]

    # 3. role_binding
    role_rows: list[tuple[Any, ...]] = [
        (
            rb["id"],
            rb["user_id"],
            rb["role"],
            rb["scope_type"],
            rb["scope_key"],
            parse_dt(rb["valid_from"]),
            parse_dt(rb.get("valid_until")),
        )
        for rb in identity_data["records"]["role_binding"]
    ]

    # 4. student_profile
    profile_rows: list[tuple[Any, ...]] = [
        (
            sp["user_id"],
            sp["student_code"],
            sp["faculty_code"],
            sp["program_code"],
            sp["cohort_year"],
            sp["academic_status"],
            sp.get("version", 1),
        )
        for sp in identity_data["records"]["student_profile"]
    ]

    # 5. room
    room_rows: list[tuple[Any, ...]] = [
        (
            rm["id"],
            rm["room_code"],
            rm["display_name"],
            rm["capacity"],
            json.dumps(rm["features"]) if isinstance(rm.get("features"), (list, dict)) else str(rm.get("features") or "[]"),
            rm["status"],
            rm.get("version", 1),
        )
        for rm in service_data["records"]["room"]
    ]

    # 6. schedule_entry
    schedule_rows: list[tuple[Any, ...]] = [
        (
            sch["id"],
            sch["student_user_id"],
            sch["source_system"],
            sch["source_record_id"],
            sch["course_code"],
            sch["course_name"],
            parse_dt(sch["starts_at"]),
            parse_dt(sch["ends_at"]),
            sch.get("location_label"),
            sch.get("instructor_display_name"),
            sch.get("sync_version", 1),
        )
        for sch in service_data["records"]["schedule_entry"]
    ]

    # 7. ticket
    ticket_rows: list[tuple[Any, ...]] = [
        (
            t["id"],
            t["requester_user_id"],
            t["category"],
            t["priority"],
            t["status"],
            t["subject"],
            t["description_redacted"],
            t["queue_key"],
            t.get("version", 1),
        )
        for t in service_data["records"]["ticket"]
    ]

    # 8. knowledge_source
    # source_type: convert 'policy' to 'SYNTHETIC_DOCUMENT'
    source_rows: list[tuple[Any, ...]] = [
        (
            src["source_id"],
            src["name"][:300],
            "SYNTHETIC_DOCUMENT" if src["source_type"] == "policy" else src["source_type"],
            src["uri"],
            "HUCE",
            50,
            "APPROVED",
            True,
            1,
        )
        for src in knowledge_data["sources"]
    ]

    # 9. document_version
    # status: 'PUBLISHED', storage_object_key: f's3://campus247-knowledge/{source_id}/{version_tag}'
    doc_rows: list[tuple[Any, ...]] = [
        (
            doc["document_version_id"],
            doc["source_id"],
            doc["version_tag"][:64],
            doc["canonical_hash"][:64],
            parse_dt(doc["effective_from"]),
            "PUBLISHED",
            f"s3://campus247-knowledge/{doc['source_id']}/{doc['version_tag']}"[:255],
            1,
        )
        for doc in knowledge_data["documents"]
    ]

    return {
        "user_identity": user_rows,
        "identity_link": link_rows,
        "role_binding": role_rows,
        "student_profile": profile_rows,
        "room": room_rows,
        "schedule_entry": schedule_rows,
        "ticket": ticket_rows,
        "knowledge_source": source_rows,
        "document_version": doc_rows,
    }


async def seed() -> None:
    raw_url = load_database_url()
    conn_url = normalize_asyncpg_url(raw_url)
    print(f"Connecting to database: {conn_url.split('@')[-1] if '@' in conn_url else conn_url}")

    conn = await asyncpg.connect(conn_url)
    try:
        data = prepare_seed_data()

        # user_identity
        await conn.executemany(
            """
            INSERT INTO user_identity (id, display_name, primary_email, status, is_synthetic, version)
            VALUES ($1, $2, $3, $4, $5, $6)
            ON CONFLICT DO NOTHING
            """,
            data["user_identity"],
        )

        # identity_link
        await conn.executemany(
            """
            INSERT INTO identity_link (id, user_id, issuer, subject, provider_type, claims_version)
            VALUES ($1, $2, $3, $4, $5, $6)
            ON CONFLICT DO NOTHING
            """,
            data["identity_link"],
        )

        # role_binding
        await conn.executemany(
            """
            INSERT INTO role_binding (id, user_id, role, scope_type, scope_key, valid_from, valid_until)
            VALUES ($1, $2, $3, $4, $5, $6, $7)
            ON CONFLICT DO NOTHING
            """,
            data["role_binding"],
        )

        # student_profile
        await conn.executemany(
            """
            INSERT INTO student_profile (user_id, student_code, faculty_code, program_code, cohort_year, academic_status, version)
            VALUES ($1, $2, $3, $4, $5, $6, $7)
            ON CONFLICT DO NOTHING
            """,
            data["student_profile"],
        )

        # room
        await conn.executemany(
            """
            INSERT INTO room (id, room_code, display_name, capacity, features, status, version)
            VALUES ($1, $2, $3, $4, $5, $6, $7)
            ON CONFLICT DO NOTHING
            """,
            data["room"],
        )

        # schedule_entry
        await conn.executemany(
            """
            INSERT INTO schedule_entry (
                id, student_user_id, source_system, source_record_id,
                course_code, course_name, starts_at, ends_at,
                location_label, instructor_display_name, sync_version
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
            ON CONFLICT DO NOTHING
            """,
            data["schedule_entry"],
        )

        # ticket
        await conn.executemany(
            """
            INSERT INTO ticket (
                id, requester_user_id, category, priority,
                status, subject, description_redacted, queue_key, version
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
            ON CONFLICT DO NOTHING
            """,
            data["ticket"],
        )

        # knowledge_source
        await conn.executemany(
            """
            INSERT INTO knowledge_source (
                id, title, source_type, canonical_uri,
                owner_unit, authority_level, approval_status, is_synthetic, version
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
            ON CONFLICT DO NOTHING
            """,
            data["knowledge_source"],
        )

        # document_version
        await conn.executemany(
            """
            INSERT INTO document_version (
                id, knowledge_source_id, version_label, content_checksum,
                effective_from, status, storage_object_key, version
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            ON CONFLICT DO NOTHING
            """,
            data["document_version"],
        )

        # 6. Run COUNT queries and print results
        counts = {
            "user_identity": await conn.fetchval("SELECT COUNT(*) FROM user_identity"),
            "identity_link": await conn.fetchval("SELECT COUNT(*) FROM identity_link"),
            "role_binding": await conn.fetchval("SELECT COUNT(*) FROM role_binding"),
            "student_profile": await conn.fetchval("SELECT COUNT(*) FROM student_profile"),
            "room": await conn.fetchval("SELECT COUNT(*) FROM room"),
            "schedule_entry": await conn.fetchval("SELECT COUNT(*) FROM schedule_entry"),
            "ticket": await conn.fetchval("SELECT COUNT(*) FROM ticket"),
            "knowledge_source": await conn.fetchval("SELECT COUNT(*) FROM knowledge_source"),
            "document_version": await conn.fetchval("SELECT COUNT(*) FROM document_version"),
        }

        print("--- Seed Record Counts ---")
        for table_name, count in counts.items():
            print(f"{table_name} count: {count}")

        # 7. Print 'Seed completed successfully' at the end
        print("Seed completed successfully")

    finally:
        await conn.close()


def main() -> None:
    asyncio.run(seed())


if __name__ == "__main__":
    main()
