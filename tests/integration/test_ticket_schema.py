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


def test_migration_0005_upgrade_and_downgrade(sqlite_engine):
    """Verify upgrade creates ticket and ticket_event tables, and downgrade drops them."""
    mods = [load_module(f"mod_{i}", path) for i, path in enumerate(MIGRATION_FILES)]
    mod5 = mods[4]
    assert mod5.revision == "0005"
    assert mod5.down_revision == "0004"

    with sqlite_engine.connect() as conn:
        ctx = MigrationContext.configure(conn)
        op = Operations(ctx)

        for m in mods:
            m.op = op
            m.upgrade()
        conn.commit()

        tables = set(inspect(conn).get_table_names())
        expected_tables = {"ticket", "ticket_event"}
        assert expected_tables.issubset(tables)

        # Setup requester user
        conn.execute(
            text(
                """
                INSERT INTO user_identity (id, display_name, primary_email, status, is_synthetic, version)
                VALUES ('018f6c4a-5b6c-7123-8abc-def012345630', 'Requester Student', 'req@huce.edu.vn', 'ACTIVE', 1, 1);
                """
            )
        )
        # Positive path: create ticket and event
        conn.execute(
            text(
                """
                INSERT INTO ticket (id, requester_user_id, category, priority, status, subject, description_redacted, queue_key, version)
                VALUES ('018f6c4a-5b6c-7123-8abc-def012345631', '018f6c4a-5b6c-7123-8abc-def012345630', 'GENERAL_SUPPORT', 'NORMAL', 'OPEN', 'Hỗ trợ tài khoản', 'Mô tả hỗ trợ', 'HUCE_GENERAL', 1);
                """
            )
        )
        conn.execute(
            text(
                """
                INSERT INTO ticket_event (id, ticket_id, sequence_no, event_type, actor_user_id, visibility)
                VALUES ('018f6c4a-5b6c-7123-8abc-def012345632', '018f6c4a-5b6c-7123-8abc-def012345631', 1, 'CREATED', '018f6c4a-5b6c-7123-8abc-def012345630', 'REQUESTER_AND_STAFF');
                """
            )
        )
        conn.commit()

        # Negative path 1: duplicate sequence_no for same ticket
        with pytest.raises(IntegrityError):
            conn.execute(
                text(
                    """
                    INSERT INTO ticket_event (id, ticket_id, sequence_no, event_type, actor_user_id, visibility)
                    VALUES ('018f6c4a-5b6c-7123-8abc-def012345633', '018f6c4a-5b6c-7123-8abc-def012345631', 1, 'COMMENTED', '018f6c4a-5b6c-7123-8abc-def012345630', 'REQUESTER_AND_STAFF');
                    """
                )
            )
            conn.commit()
        conn.rollback()

        # Negative path 2: invalid ticket category
        with pytest.raises(IntegrityError):
            conn.execute(
                text(
                    """
                    INSERT INTO ticket (id, requester_user_id, category, priority, status, subject, description_redacted, queue_key, version)
                    VALUES ('018f6c4a-5b6c-7123-8abc-def012345634', '018f6c4a-5b6c-7123-8abc-def012345630', 'INVALID_CAT', 'NORMAL', 'OPEN', 'Sub', 'Desc', 'HUCE_GENERAL', 1);
                    """
                )
            )
            conn.commit()
        conn.rollback()

        # Downgrade 0005
        mod5.downgrade()
        conn.commit()

        tables_after = set(inspect(conn).get_table_names())
        assert not expected_tables.intersection(tables_after)
        assert "user_identity" in tables_after
