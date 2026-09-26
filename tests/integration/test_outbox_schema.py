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
    ROOT / "services" / "api" / "migrations" / "versions" / "0007_booking.py",
    ROOT / "services" / "api" / "migrations" / "versions" / "0008_audit_outbox.py",
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


def test_migration_0008_upgrade_and_downgrade(sqlite_engine):
    """Verify upgrade creates audit, outbox, and inbox_receipt tables, and downgrade drops them."""
    mods = [load_module(f"mod_{i}", path) for i, path in enumerate(MIGRATION_FILES)]
    mod8 = mods[7]
    assert mod8.revision == "0008"
    assert mod8.down_revision == "0007"

    with sqlite_engine.connect() as conn:
        ctx = MigrationContext.configure(conn)
        op = Operations(ctx)

        for m in mods:
            m.op = op
            m.upgrade()
        conn.commit()

        tables = set(inspect(conn).get_table_names())
        assert {"audit_event", "outbox_event", "inbox_receipt"}.issubset(tables)

        # Positive path: audit, outbox, inbox
        conn.execute(
            text(
                """
                INSERT INTO audit_event (id, actor_type, action_code, resource_type, outcome)
                VALUES ('018f6c4a-5b6c-7123-8abc-def012345660', 'USER', 'CREATE_TICKET', 'ticket', 'SUCCESS');
                """
            )
        )
        conn.execute(
            text(
                """
                INSERT INTO outbox_event (id, event_type, aggregate_type, aggregate_id, partition_key, payload)
                VALUES ('018f6c4a-5b6c-7123-8abc-def012345661', 'ticket.created', 'ticket', '018f6c4a-5b6c-7123-8abc-def012345662', '018f6c4a-5b6c-7123-8abc-def012345662', '{}');
                """
            )
        )
        conn.execute(
            text(
                """
                INSERT INTO inbox_receipt (consumer_name, event_id, outcome)
                VALUES ('notification_consumer', '018f6c4a-5b6c-7123-8abc-def012345661', 'PROCESSED');
                """
            )
        )
        conn.commit()

        # Negative path 1: duplicate composite PK on inbox_receipt
        with pytest.raises(IntegrityError):
            conn.execute(
                text(
                    """
                    INSERT INTO inbox_receipt (consumer_name, event_id, outcome)
                    VALUES ('notification_consumer', '018f6c4a-5b6c-7123-8abc-def012345661', 'DUPLICATE');
                    """
                )
            )
            conn.commit()
        conn.rollback()

        # Negative path 2: negative publish attempts
        with pytest.raises(IntegrityError):
            conn.execute(
                text(
                    """
                    INSERT INTO outbox_event (id, event_type, aggregate_type, aggregate_id, partition_key, payload, publish_attempts)
                    VALUES ('018f6c4a-5b6c-7123-8abc-def012345663', 'ticket.created', 'ticket', '018f6c4a-5b6c-7123-8abc-def012345662', '018f6c4a-5b6c-7123-8abc-def012345662', '{}', -1);
                    """
                )
            )
            conn.commit()
        conn.rollback()

        # Downgrade 0008
        mod8.downgrade()
        conn.commit()

        tables_after = set(inspect(conn).get_table_names())
        assert not {"audit_event", "outbox_event", "inbox_receipt"}.intersection(tables_after)
        assert "room_booking" in tables_after
