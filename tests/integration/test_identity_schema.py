from __future__ import annotations

import importlib.util
from pathlib import Path
import pytest
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.exc import IntegrityError
from alembic.migration import MigrationContext
from alembic.operations import Operations

ROOT = Path(__file__).resolve().parents[2]
MIGRATION_PATH = ROOT / "services" / "api" / "migrations" / "versions" / "0001_identity.py"


def load_migration_module():
    spec = importlib.util.spec_from_file_location("migration_0001", MIGRATION_PATH)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture
def sqlite_engine():
    engine = create_engine("sqlite:///:memory:", echo=False)
    with engine.connect() as conn:
        conn.execute(text("PRAGMA foreign_keys = ON;"))
    return engine


def test_migration_0001_upgrade_and_downgrade(sqlite_engine):
    """Verify upgrade creates all identity tables with proper columns and downgrade drops them."""
    mod = load_migration_module()
    assert mod.revision == "0001"
    assert mod.down_revision is None

    with sqlite_engine.connect() as conn:
        ctx = MigrationContext.configure(conn)
        op = Operations(ctx)
        mod.op = op

        # Run upgrade
        mod.upgrade()
        conn.commit()

        inspector = inspect(sqlite_engine)
        tables = set(inspector.get_table_names())
        expected_tables = {"user_identity", "identity_link", "role_binding", "student_profile"}
        assert expected_tables.issubset(tables)

        # Positive test: insert valid identity records
        conn.execute(
            text(
                """
                INSERT INTO user_identity (id, display_name, primary_email, status, is_synthetic, version)
                VALUES ('018f6c4a-5b6c-7123-8abc-def012345678', 'Test Student', 'student@huce.edu.vn', 'ACTIVE', 1, 1);
                """
            )
        )
        conn.execute(
            text(
                """
                INSERT INTO student_profile (user_id, student_code, faculty_code, program_code, cohort_year, academic_status, version)
                VALUES ('018f6c4a-5b6c-7123-8abc-def012345678', 'SV123456', 'FIT', 'CS_V1', 2024, 'ACTIVE', 1);
                """
            )
        )
        conn.commit()

        # Negative test 1: invalid academic status violates check constraint
        with pytest.raises(IntegrityError):
            conn.execute(
                text(
                    """
                    INSERT INTO student_profile (user_id, student_code, faculty_code, program_code, cohort_year, academic_status, version)
                    VALUES ('018f6c4a-5b6c-7123-8abc-def012345679', 'SV999999', 'FIT', 'CS_V1', 2024, 'INVALID_STATUS', 1);
                    """
                )
            )
            conn.commit()
        conn.rollback()

        # Negative test 2: duplicate student_code violates unique constraint
        with pytest.raises(IntegrityError):
            conn.execute(
                text(
                    """
                    INSERT INTO user_identity (id, display_name, primary_email, status, is_synthetic, version)
                    VALUES ('018f6c4a-5b6c-7123-8abc-def012345679', 'Student 2', 's2@huce.edu.vn', 'ACTIVE', 1, 1);
                    """
                )
            )
            conn.execute(
                text(
                    """
                    INSERT INTO student_profile (user_id, student_code, faculty_code, program_code, cohort_year, academic_status, version)
                    VALUES ('018f6c4a-5b6c-7123-8abc-def012345679', 'SV123456', 'FIT', 'CS_V1', 2024, 'ACTIVE', 1);
                    """
                )
            )
            conn.commit()
        conn.rollback()

        # Run downgrade
        mod.downgrade()
        conn.commit()

        tables_after = set(inspect(conn).get_table_names())
        assert not expected_tables.intersection(tables_after)
