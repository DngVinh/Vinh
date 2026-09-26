from __future__ import annotations

import json
from pathlib import Path
import re
import sys
import pytest

ROOT = Path(__file__).resolve().parents[3]
SRC = ROOT / "packages" / "synthetic" / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from identities import (
    SYNTHETIC_EMAIL_DOMAIN,
    canonical_checksum,
    generate_identities,
)

UUIDV7_REGEX = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-7[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$"
)


def test_deterministic_generation_same_seed():
    """AC-REQ-NF-DATA-001-01: Same seed produces identical records and canonical checksum."""
    run1 = generate_identities(seed=2472026, student_count=10, staff_count=5)
    run2 = generate_identities(seed=2472026, student_count=10, staff_count=5)

    assert run1["manifest"]["records_checksum"] == run2["manifest"]["records_checksum"]
    assert canonical_checksum(run1["records"]) == canonical_checksum(run2["records"])
    assert run1["records"] == run2["records"]


def test_different_seeds_produce_different_checksums():
    """Verify different seeds produce divergent outputs."""
    run1 = generate_identities(seed=111, student_count=5, staff_count=3)
    run2 = generate_identities(seed=222, student_count=5, staff_count=3)

    assert run1["manifest"]["records_checksum"] != run2["manifest"]["records_checksum"]


def test_synthetic_identity_constraints():
    """Verify synthetic identities comply with privacy markers and allowed role taxonomy."""
    data = generate_identities(seed=2472026, student_count=10, staff_count=5)
    records = data["records"]

    allowed_roles = {"STUDENT", "SUPPORT_OFFICER", "KNOWLEDGE_ADMIN", "SYSTEM_ADMIN"}

    for user in records["user_identity"]:
        assert user["is_synthetic"] is True
        assert UUIDV7_REGEX.fullmatch(user["id"])
        assert user["primary_email"].endswith(f"@{SYNTHETIC_EMAIL_DOMAIN}")
        assert user["status"] == "ACTIVE"

    for link in records["identity_link"]:
        assert link["provider_type"] == "SYNTHETIC"
        assert UUIDV7_REGEX.fullmatch(link["id"])

    for role in records["role_binding"]:
        assert role["role"] in allowed_roles
        assert UUIDV7_REGEX.fullmatch(role["id"])

    for profile in records["student_profile"]:
        assert 2000 <= profile["cohort_year"] <= 2100
        assert profile["academic_status"] == "ACTIVE"


def test_committed_sample_integrity():
    """Verify committed sample file matches deterministic generator output."""
    sample_path = ROOT / "packages" / "synthetic" / "samples" / "identities.json"
    assert sample_path.is_file(), "identities.json sample file must exist"

    sample_data = json.loads(sample_path.read_text(encoding="utf-8"))
    assert sample_data["manifest"]["seed"] == 2472026
    expected = generate_identities(seed=2472026, student_count=10, staff_count=5)
    assert sample_data["manifest"]["records_checksum"] == expected["manifest"]["records_checksum"]
