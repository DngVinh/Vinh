from __future__ import annotations

import importlib.util
from pathlib import Path
import pytest
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.exc import IntegrityError
from alembic.migration import MigrationContext
from alembic.operations import Operations

ROOT = Path(__file__).resolve().parents[2]
MIGRATION_0001 = ROOT / "services" / "api" / "migrations" / "versions" / "0001_identity.py"
MIGRATION_0002 = ROOT / "services" / "api" / "migrations" / "versions" / "0002_knowledge.py"
MIGRATION_0003 = ROOT / "services" / "api" / "migrations" / "versions" / "0003_conversation.py"


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


def test_migration_0003_upgrade_and_downgrade(sqlite_engine):
    """Verify upgrade creates conversation and handover tables and downgrade drops them."""
    mod1 = load_module("migration_0001", MIGRATION_0001)
    mod2 = load_module("migration_0002", MIGRATION_0002)
    mod3 = load_module("migration_0003", MIGRATION_0003)

    assert mod3.revision == "0003"
    assert mod3.down_revision == "0002"

    with sqlite_engine.connect() as conn:
        ctx = MigrationContext.configure(conn)
        op = Operations(ctx)

        for mod in (mod1, mod2, mod3):
            mod.op = op
            mod.upgrade()
        conn.commit()

        tables = set(inspect(conn).get_table_names())
        expected_tables = {"conversation", "message", "handover"}
        assert expected_tables.issubset(tables)

        # Setup user
        conn.execute(
            text(
                """
                INSERT INTO user_identity (id, display_name, primary_email, status, is_synthetic, version)
                VALUES ('018f6c4a-5b6c-7123-8abc-def012345610', 'Student Conv', 'sconv@huce.edu.vn', 'ACTIVE', 1, 1);
                """
            )
        )
        # Positive path: conversation, message, handover
        conn.execute(
            text(
                """
                INSERT INTO conversation (id, owner_user_id, status, channel, retention_expires_at, version)
                VALUES ('018f6c4a-5b6c-7123-8abc-def012345611', '018f6c4a-5b6c-7123-8abc-def012345610', 'ACTIVE', 'WEB', '2027-01-01 00:00:00', 1);
                """
            )
        )
        conn.execute(
            text(
                """
                INSERT INTO message (id, conversation_id, sequence_no, sender_type, content_redacted, content_format)
                VALUES ('018f6c4a-5b6c-7123-8abc-def012345612', '018f6c4a-5b6c-7123-8abc-def012345611', 1, 'USER', 'Xin chào', 'PLAIN_TEXT');
                """
            )
        )
        conn.execute(
            text(
                """
                INSERT INTO handover (id, conversation_id, requester_user_id, queue_key, reason_code, risk_level, status, summary_redacted, version)
                VALUES ('018f6c4a-5b6c-7123-8abc-def012345613', '018f6c4a-5b6c-7123-8abc-def012345611', '018f6c4a-5b6c-7123-8abc-def012345610', 'HUCE_GENERAL', 'USER_REQUESTED_HUMAN', 'LOW', 'QUEUED', 'Cần gặp tư vấn viên', 1);
                """
            )
        )
        conn.commit()

        # Negative path 1: duplicate sequence_no in same conversation
        with pytest.raises(IntegrityError):
            conn.execute(
                text(
                    """
                    INSERT INTO message (id, conversation_id, sequence_no, sender_type, content_redacted, content_format)
                    VALUES ('018f6c4a-5b6c-7123-8abc-def012345614', '018f6c4a-5b6c-7123-8abc-def012345611', 1, 'ASSISTANT', 'Chào bạn', 'PLAIN_TEXT');
                    """
                )
            )
            conn.commit()
        conn.rollback()

        # Negative path 2: invalid risk_level in handover
        with pytest.raises(IntegrityError):
            conn.execute(
                text(
                    """
                    INSERT INTO handover (id, conversation_id, requester_user_id, queue_key, reason_code, risk_level, status, summary_redacted, version)
                    VALUES ('018f6c4a-5b6c-7123-8abc-def012345615', '018f6c4a-5b6c-7123-8abc-def012345611', '018f6c4a-5b6c-7123-8abc-def012345610', 'HUCE_GENERAL', 'USER_REQUESTED_HUMAN', 'INVALID_RISK', 'QUEUED', 'Cần tư vấn', 1);
                    """
                )
            )
            conn.commit()
        conn.rollback()

        # Downgrade 0003
        mod3.downgrade()
        conn.commit()

        tables_after = set(inspect(conn).get_table_names())
        assert not expected_tables.intersection(tables_after)
        assert "user_identity" in tables_after
