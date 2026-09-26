from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
import pytest

ROOT = Path(__file__).resolve().parents[2]
SEED_SCRIPT_PATH = ROOT / "scripts" / "seed_database.py"


def test_seed_database_script_exists():
    assert SEED_SCRIPT_PATH.is_file(), "scripts/seed_database.py must exist"


def test_seed_database_helpers():
    spec = importlib.util.spec_from_file_location("seed_database", str(SEED_SCRIPT_PATH))
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    # Test URL normalizer
    sa_url = "postgresql+asyncpg://user:pass@localhost:5432/db"
    assert mod.normalize_asyncpg_url(sa_url) == "postgresql://user:pass@localhost:5432/db"

    # Test prepare_records
    prepared = mod.prepare_seed_data()
    assert "user_identity" in prepared
    assert "identity_link" in prepared
    assert "role_binding" in prepared
    assert "student_profile" in prepared
    assert "room" in prepared
    assert "schedule_entry" in prepared
    assert "ticket" in prepared
    assert "knowledge_source" in prepared
    assert "document_version" in prepared

    # Check student_count=100 and staff_count=20 (identities.py has 5 staff specs, so 100 + 5 = 105)
    assert len(prepared["user_identity"]) == 105
    assert len(prepared["student_profile"]) == 100
    assert len(prepared["role_binding"]) == 105
    assert len(prepared["room"]) == 4
    assert len(prepared["knowledge_source"]) > 0
    assert len(prepared["document_version"]) > 0

    # Ensure role_binding valid_from is datetime
    assert hasattr(prepared["role_binding"][0][5], "year")

    # Ensure schedule_entry starts_at and ends_at are datetime
    assert hasattr(prepared["schedule_entry"][0][6], "year")
    assert hasattr(prepared["schedule_entry"][0][7], "year")
