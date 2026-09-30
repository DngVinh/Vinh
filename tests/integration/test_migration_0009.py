from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
import pytest
from alembic.config import Config
from alembic.script import ScriptDirectory

ROOT = Path(__file__).resolve().parents[2]
ALEMBIC_INI = ROOT / "services" / "api" / "alembic.ini"
MIGRATION_0009_PATH = ROOT / "services" / "api" / "migrations" / "versions" / "0009_schedule_and_vectors.py"


def test_migration_0009_file_exists():
    assert MIGRATION_0009_PATH.is_file(), "0009_schedule_and_vectors.py must exist"


def test_migration_0009_attributes():
    spec = importlib.util.spec_from_file_location("migration_0009", str(MIGRATION_0009_PATH))
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    assert mod.revision == "0009"
    assert mod.down_revision == "0008"
    assert callable(mod.upgrade)
    assert callable(mod.downgrade)


def test_alembic_head_is_0010():
    config = Config(str(ALEMBIC_INI))
    script = ScriptDirectory.from_config(config)
    assert script.get_heads() == ["0010"]
