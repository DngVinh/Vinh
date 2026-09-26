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
    ROOT / "services" / "api" / "migrations" / "versions" / "0005_ticket.py",
    ROOT / "services" / "api" / "migrations" / "versions" / "0006_document_request.py",
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


def test_migration_0006_upgrade_and_downgrade(sqlite_engine):
    """Verify upgrade creates document_request table and downgrade drops it."""
    mods = [load_module(f"mod_{i}", path) for i, path in enumerate(MIGRATION_FILES)]
    mod6 = mods[5]
    assert mod6.revision == "0006"
    assert mod6.down_revision == "0005"

    with sqlite_engine.connect() as conn:
        ctx = MigrationContext.configure(conn)
        op = Operations(ctx)

        for m in mods:
            m.op = op
            m.upgrade()
        conn.commit()

        tables = set(inspect(conn).get_table_names())
        assert "document_request" in tables

        # Setup student user, preview and execution
        conn.execute(
            text(
                """
                INSERT INTO user_identity (id, display_name, primary_email, status, is_synthetic, version)
                VALUES ('018f6c4a-5b6c-7123-8abc-def012345640', 'Doc Student', 'doc@huce.edu.vn', 'ACTIVE', 1, 1);
                """
            )
        )
        conn.execute(
            text(
                """
                INSERT INTO action_preview (id, actor_user_id, action_type, normalized_payload, payload_hash, policy_decision, confirmation_secret_hash, expires_at, version)
                VALUES ('018f6c4a-5b6c-7123-8abc-def012345641', '018f6c4a-5b6c-7123-8abc-def012345640', 'REQUEST_DOC', '{}', 'sha256:abc', 'ALLOWED', 'hash456', '2026-12-31 23:59:59', 1);
                """
            )
        )
        conn.execute(
            text(
                """
                INSERT INTO action_execution (id, preview_id, status, target_type, target_id, attempt_count, version)
                VALUES ('018f6c4a-5b6c-7123-8abc-def012345642', '018f6c4a-5b6c-7123-8abc-def012345641', 'SUCCEEDED', 'document_request', '018f6c4a-5b6c-7123-8abc-def012345643', 1, 1);
                """
            )
        )
        # Positive path: create document_request
        conn.execute(
            text(
                """
                INSERT INTO document_request (id, student_user_id, document_type, purpose_code, delivery_method, status, action_execution_id, version)
                VALUES ('018f6c4a-5b6c-7123-8abc-def012345643', '018f6c4a-5b6c-7123-8abc-def012345640', 'TRANSCRIPT', 'SCHOLARSHIP', 'DIGITAL', 'SUBMITTED', '018f6c4a-5b6c-7123-8abc-def012345642', 1);
                """
            )
        )
        conn.commit()

        # Negative path 1: invalid delivery_method
        with pytest.raises(IntegrityError):
            conn.execute(
                text(
                    """
                    INSERT INTO document_request (id, student_user_id, document_type, purpose_code, delivery_method, status, action_execution_id, version)
                    VALUES ('018f6c4a-5b6c-7123-8abc-def012345644', '018f6c4a-5b6c-7123-8abc-def012345640', 'TRANSCRIPT', 'SCHOLARSHIP', 'DRONE', 'SUBMITTED', '018f6c4a-5b6c-7123-8abc-def012345642', 1);
                    """
                )
            )
            conn.commit()
        conn.rollback()

        # Negative path 2: invalid status
        with pytest.raises(IntegrityError):
            conn.execute(
                text(
                    """
                    INSERT INTO document_request (id, student_user_id, document_type, purpose_code, delivery_method, status, action_execution_id, version)
                    VALUES ('018f6c4a-5b6c-7123-8abc-def012345645', '018f6c4a-5b6c-7123-8abc-def012345640', 'TRANSCRIPT', 'SCHOLARSHIP', 'DIGITAL', 'INVALID_STATUS', '018f6c4a-5b6c-7123-8abc-def012345642', 1);
                    """
                )
            )
            conn.commit()
        conn.rollback()

        # Downgrade 0006
        mod6.downgrade()
        conn.commit()

        tables_after = set(inspect(conn).get_table_names())
        assert "document_request" not in tables_after
        assert "ticket" in tables_after
