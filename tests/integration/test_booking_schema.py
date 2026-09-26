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


def test_migration_0007_upgrade_and_downgrade(sqlite_engine):
    """Verify upgrade creates room and room_booking tables and downgrade drops them."""
    mods = [load_module(f"mod_{i}", path) for i, path in enumerate(MIGRATION_FILES)]
    mod7 = mods[6]
    assert mod7.revision == "0007"
    assert mod7.down_revision == "0006"

    with sqlite_engine.connect() as conn:
        ctx = MigrationContext.configure(conn)
        op = Operations(ctx)

        for m in mods:
            m.op = op
            m.upgrade()
        conn.commit()

        tables = set(inspect(conn).get_table_names())
        assert {"room", "room_booking"}.issubset(tables)

        # Setup user, preview, execution
        conn.execute(
            text(
                """
                INSERT INTO user_identity (id, display_name, primary_email, status, is_synthetic, version)
                VALUES ('018f6c4a-5b6c-7123-8abc-def012345650', 'Booking Student', 'book@huce.edu.vn', 'ACTIVE', 1, 1);
                """
            )
        )
        conn.execute(
            text(
                """
                INSERT INTO action_preview (id, actor_user_id, action_type, normalized_payload, payload_hash, policy_decision, confirmation_secret_hash, expires_at, version)
                VALUES ('018f6c4a-5b6c-7123-8abc-def012345651', '018f6c4a-5b6c-7123-8abc-def012345650', 'BOOK_ROOM', '{}', 'sha256:abc', 'ALLOWED', 'hash789', '2026-12-31 23:59:59', 1);
                """
            )
        )
        conn.execute(
            text(
                """
                INSERT INTO action_execution (id, preview_id, status, target_type, target_id, attempt_count, version)
                VALUES ('018f6c4a-5b6c-7123-8abc-def012345652', '018f6c4a-5b6c-7123-8abc-def012345651', 'SUCCEEDED', 'room_booking', '018f6c4a-5b6c-7123-8abc-def012345653', 1, 1);
                """
            )
        )
        # Positive path: create room and booking
        conn.execute(
            text(
                """
                INSERT INTO room (id, room_code, display_name, capacity, status, version)
                VALUES ('018f6c4a-5b6c-7123-8abc-def012345654', 'H1-301', 'Phòng học H1-301', 40, 'AVAILABLE', 1);
                """
            )
        )
        conn.execute(
            text(
                """
                INSERT INTO room_booking (id, room_id, requester_user_id, starts_at, ends_at, purpose_redacted, attendee_count, status, action_execution_id, version)
                VALUES ('018f6c4a-5b6c-7123-8abc-def012345653', '018f6c4a-5b6c-7123-8abc-def012345654', '018f6c4a-5b6c-7123-8abc-def012345650', '2026-10-01 08:00:00', '2026-10-01 10:00:00', 'Học nhóm', 5, 'CONFIRMED', '018f6c4a-5b6c-7123-8abc-def012345652', 1);
                """
            )
        )
        conn.commit()

        # Negative path 1: capacity <= 0
        with pytest.raises(IntegrityError):
            conn.execute(
                text(
                    """
                    INSERT INTO room (id, room_code, display_name, capacity, status, version)
                    VALUES ('018f6c4a-5b6c-7123-8abc-def012345655', 'H1-302', 'Phòng H1-302', 0, 'AVAILABLE', 1);
                    """
                )
            )
            conn.commit()
        conn.rollback()

        # Negative path 2: starts_at >= ends_at
        with pytest.raises(IntegrityError):
            conn.execute(
                text(
                    """
                    INSERT INTO room_booking (id, room_id, requester_user_id, starts_at, ends_at, purpose_redacted, attendee_count, status, action_execution_id, version)
                    VALUES ('018f6c4a-5b6c-7123-8abc-def012345656', '018f6c4a-5b6c-7123-8abc-def012345654', '018f6c4a-5b6c-7123-8abc-def012345650', '2026-10-01 10:00:00', '2026-10-01 08:00:00', 'Học nhóm', 5, 'CONFIRMED', '018f6c4a-5b6c-7123-8abc-def012345652', 1);
                    """
                )
            )
            conn.commit()
        conn.rollback()

        # Downgrade 0007
        mod7.downgrade()
        conn.commit()

        tables_after = set(inspect(conn).get_table_names())
        assert not {"room", "room_booking"}.intersection(tables_after)
        assert "document_request" in tables_after
