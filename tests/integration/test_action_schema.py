from __future__ import annotations

import importlib.util
from pathlib import Path
import pytest
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.exc import IntegrityError
from alembic.migration import MigrationContext
from alembic.operations import Operations

ROOT = Path(__file__).resolve().parents[2]
MIGRATION_FILES = [
    ROOT / "services" / "api" / "migrations" / "versions" / "0001_identity.py",
    ROOT / "services" / "api" / "migrations" / "versions" / "0002_knowledge.py",
    ROOT / "services" / "api" / "migrations" / "versions" / "0003_conversation.py",
    ROOT / "services" / "api" / "migrations" / "versions" / "0004_action.py",
]


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
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


def test_migration_0004_upgrade_and_downgrade(sqlite_engine):
    """Verify upgrade creates action tables and constraints, and downgrade drops them."""
    mods = [load_module(f"mod_{i}", path) for i, path in enumerate(MIGRATION_FILES)]
    mod4 = mods[3]
    assert mod4.revision == "0004"
    assert mod4.down_revision == "0003"

    with sqlite_engine.connect() as conn:
        ctx = MigrationContext.configure(conn)
        op = Operations(ctx)

        for m in mods:
            m.op = op
            m.upgrade()
        conn.commit()

        tables = set(inspect(conn).get_table_names())
        expected_tables = {"action_preview", "action_confirmation", "action_execution", "idempotency_record"}
        assert expected_tables.issubset(tables)

        # Setup user
        conn.execute(
            text(
                """
                INSERT INTO user_identity (id, display_name, primary_email, status, is_synthetic, version)
                VALUES ('018f6c4a-5b6c-7123-8abc-def012345620', 'Action Actor', 'actor@huce.edu.vn', 'ACTIVE', 1, 1);
                """
            )
        )
        # Positive path
        conn.execute(
            text(
                """
                INSERT INTO action_preview (id, actor_user_id, action_type, normalized_payload, payload_hash, policy_decision, confirmation_secret_hash, expires_at, version)
                VALUES ('018f6c4a-5b6c-7123-8abc-def012345621', '018f6c4a-5b6c-7123-8abc-def012345620', 'CREATE_TICKET', '{}', 'sha256:abc', 'ALLOWED', 'hash123', '2026-12-31 23:59:59', 1);
                """
            )
        )
        conn.execute(
            text(
                """
                INSERT INTO action_confirmation (id, preview_id, actor_user_id, confirmation_token_hash)
                VALUES ('018f6c4a-5b6c-7123-8abc-def012345622', '018f6c4a-5b6c-7123-8abc-def012345621', '018f6c4a-5b6c-7123-8abc-def012345620', 'tokenhash123');
                """
            )
        )
        conn.execute(
            text(
                """
                INSERT INTO action_execution (id, preview_id, status, target_type, target_id, attempt_count, version)
                VALUES ('018f6c4a-5b6c-7123-8abc-def012345623', '018f6c4a-5b6c-7123-8abc-def012345621', 'SUCCEEDED', 'ticket', '018f6c4a-5b6c-7123-8abc-def012345624', 1, 1);
                """
            )
        )
        conn.execute(
            text(
                """
                INSERT INTO idempotency_record (id, actor_user_id, operation_id, idempotency_key, request_fingerprint, state, expires_at)
                VALUES ('018f6c4a-5b6c-7123-8abc-def012345625', '018f6c4a-5b6c-7123-8abc-def012345620', 'op_create_ticket', 'idem-key-1', 'sha256:fp1', 'COMPLETED', '2026-12-31 23:59:59');
                """
            )
        )
        conn.commit()

        # Negative path 1: duplicate idempotency key
        with pytest.raises(IntegrityError):
            conn.execute(
                text(
                    """
                    INSERT INTO idempotency_record (id, actor_user_id, operation_id, idempotency_key, request_fingerprint, state, expires_at)
                    VALUES ('018f6c4a-5b6c-7123-8abc-def012345626', '018f6c4a-5b6c-7123-8abc-def012345620', 'op_create_ticket', 'idem-key-1', 'sha256:fp2', 'IN_PROGRESS', '2026-12-31 23:59:59');
                    """
                )
            )
            conn.commit()
        conn.rollback()

        # Negative path 2: invalid execution status
        with pytest.raises(IntegrityError):
            conn.execute(
                text(
                    """
                    INSERT INTO action_execution (id, preview_id, status, version)
                    VALUES ('018f6c4a-5b6c-7123-8abc-def012345627', '018f6c4a-5b6c-7123-8abc-def012345621', 'INVALID_STATUS', 1);
                    """
                )
            )
            conn.commit()
        conn.rollback()

        # Downgrade 0004
        mod4.downgrade()
        conn.commit()

        tables_after = set(inspect(conn).get_table_names())
        assert not expected_tables.intersection(tables_after)
        assert "user_identity" in tables_after
