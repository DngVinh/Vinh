from __future__ import annotations

import hashlib
import json
import random
from typing import Any
import uuid

SYNTHETIC_ISSUER = "urn:campus247:issuer:synthetic"
SYNTHETIC_EMAIL_DOMAIN = "demo.huce.example"

FIRST_NAMES = ["Nguyễn", "Trần", "Lê", "Phạm", "Hoàng", "Huỳnh", "Vũ", "Võ", "Đặng", "Bùi"]
MIDDLE_NAMES = ["Văn", "Thị", "Hoàng", "Minh", "Đức", "Thanh", "Hải", "Quang"]
LAST_NAMES = ["An", "Bình", "Cường", "Dung", "Em", "Giang", "Hải", "Khánh", "Linh", "Minh"]


def deterministic_uuid7(seed_val: str) -> str:
    """Derive deterministic UUID with version 7 bits from seed string."""
    h = hashlib.sha256(seed_val.encode("utf-8")).digest()
    raw = bytearray(h[:16])
    raw[6] = (raw[6] & 0x0F) | 0x70  # Version 7
    raw[8] = (raw[8] & 0x3F) | 0x80  # Variant RFC 4122 / 9562
    return str(uuid.UUID(bytes=bytes(raw)))


def canonical_checksum(payload: Any) -> str:
    """Compute sha256 checksum of canonically serialized JSON."""
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return f"sha256:{hashlib.sha256(encoded).hexdigest()}"


def generate_identities(
    seed: int = 2472026,
    student_count: int = 15,
    staff_count: int = 5,
) -> dict[str, Any]:
    """Generate deterministic synthetic user identities, links, roles, and profiles."""
    rng = random.Random(seed)
    users: list[dict[str, Any]] = []
    links: list[dict[str, Any]] = []
    roles: list[dict[str, Any]] = []
    profiles: list[dict[str, Any]] = []

    # 1. Generate Students
    for i in range(student_count):
        uid = deterministic_uuid7(f"user-student-{seed}-{i}")
        name = f"{rng.choice(FIRST_NAMES)} {rng.choice(MIDDLE_NAMES)} {rng.choice(LAST_NAMES)}"
        code = f"SV{240000 + i:06d}"
        email = f"{code.lower()}@{SYNTHETIC_EMAIL_DOMAIN}"
        cohort = 2024

        users.append({
            "id": uid,
            "display_name": name,
            "primary_email": email,
            "status": "ACTIVE",
            "is_synthetic": True,
            "version": 1,
        })
        links.append({
            "id": deterministic_uuid7(f"link-{uid}"),
            "user_id": uid,
            "issuer": SYNTHETIC_ISSUER,
            "subject": f"sub-{code}",
            "provider_type": "SYNTHETIC",
            "claims_version": "v1",
        })
        roles.append({
            "id": deterministic_uuid7(f"role-{uid}"),
            "user_id": uid,
            "role": "STUDENT",
            "scope_type": "INSTITUTION",
            "scope_key": "HUCE",
            "valid_from": "2026-09-01T00:00:00Z",
            "valid_until": None,
        })
        profiles.append({
            "user_id": uid,
            "student_code": code,
            "faculty_code": "FIT",
            "program_code": "IT_STANDARD",
            "cohort_year": cohort,
            "academic_status": "ACTIVE",
            "version": 1,
        })

    # 2. Generate Staff Roles (SUPPORT_OFFICER, KNOWLEDGE_ADMIN, SYSTEM_ADMIN)
    staff_specs = [
        ("SUPPORT_OFFICER", "QUEUE", "HUCE_GENERAL"),
        ("SUPPORT_OFFICER", "QUEUE", "ACADEMIC_SERVICES"),
        ("KNOWLEDGE_ADMIN", "FACULTY", "FIT"),
        ("KNOWLEDGE_ADMIN", "INSTITUTION", "HUCE"),
        ("SYSTEM_ADMIN", "INSTITUTION", "HUCE"),
    ]
    for idx, (role_name, s_type, s_key) in enumerate(staff_specs[:staff_count]):
        uid = deterministic_uuid7(f"user-staff-{seed}-{idx}")
        name = f"Cán bộ {role_name} {idx + 1}"
        email = f"staff_{idx + 1}@{SYNTHETIC_EMAIL_DOMAIN}"

        users.append({
            "id": uid,
            "display_name": name,
            "primary_email": email,
            "status": "ACTIVE",
            "is_synthetic": True,
            "version": 1,
        })
        links.append({
            "id": deterministic_uuid7(f"link-{uid}"),
            "user_id": uid,
            "issuer": SYNTHETIC_ISSUER,
            "subject": f"staff-sub-{idx + 1}",
            "provider_type": "SYNTHETIC",
            "claims_version": "v1",
        })
        roles.append({
            "id": deterministic_uuid7(f"role-{uid}"),
            "user_id": uid,
            "role": role_name,
            "scope_type": s_type,
            "scope_key": s_key,
            "valid_from": "2026-09-01T00:00:00Z",
            "valid_until": None,
        })

    records = {
        "user_identity": users,
        "identity_link": links,
        "role_binding": roles,
        "student_profile": profiles,
    }
    records_checksum = canonical_checksum(records)

    manifest = {
        "dataset_id": f"DATASET-SYNTH-IDENTITIES-SEED{seed}",
        "version": "1.0.0",
        "generator_version": "1.0.0",
        "seed": seed,
        "locale": "vi-VN",
        "simulation_label": True,
        "record_counts": {
            "user_identity": len(users),
            "identity_link": len(links),
            "role_binding": len(roles),
            "student_profile": len(profiles),
        },
        "records_checksum": records_checksum,
    }

    return {"manifest": manifest, "records": records}
