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


def test_migration_0002_upgrade_and_downgrade(sqlite_engine):
    """Verify upgrade creates all knowledge tables with proper constraints and downgrade drops them."""
    mod1 = load_module("migration_0001", MIGRATION_0001)
    mod2 = load_module("migration_0002", MIGRATION_0002)

    assert mod2.revision == "0002"
    assert mod2.down_revision == "0001"

    with sqlite_engine.connect() as conn:
        ctx = MigrationContext.configure(conn)
        op = Operations(ctx)

        mod1.op = op
        mod1.upgrade()

        mod2.op = op
        mod2.upgrade()
        conn.commit()

        tables = set(inspect(conn).get_table_names())
        expected_tables = {"knowledge_source", "document_version", "knowledge_chunk", "retrieval_run"}
        assert expected_tables.issubset(tables)

        # Positive test: insert valid knowledge hierarchy
        conn.execute(
            text(
                """
                INSERT INTO knowledge_source (id, source_type, canonical_uri, title, owner_unit, authority_level, approval_status, is_synthetic, version)
                VALUES ('018f6c4a-5b6c-7123-8abc-def012345601', 'OFFICIAL_DOCUMENT', 'https://huce.edu.vn/doc/qd-100', 'Quy chế đào tạo HUCE', 'Phòng Đào tạo', 90, 'APPROVED', 1, 1);
                """
            )
        )
        conn.execute(
            text(
                """
                INSERT INTO document_version (id, knowledge_source_id, version_label, content_checksum, status, storage_object_key, version)
                VALUES ('018f6c4a-5b6c-7123-8abc-def012345602', '018f6c4a-5b6c-7123-8abc-def012345601', 'v1.0', 'sha256:abcdef0123456789abcdef0123456789abcdef0123456789abcdef0123456789', 'PUBLISHED', 'docs/qd-100-v1.pdf', 1);
                """
            )
        )
        conn.execute(
            text(
                """
                INSERT INTO knowledge_chunk (id, document_version_id, ordinal, section_path, page_start, page_end, content_text, content_checksum, version)
                VALUES ('018f6c4a-5b6c-7123-8abc-def012345603', '018f6c4a-5b6c-7123-8abc-def012345602', 1, 'Dieu 1', 1, 2, 'Noi dung dieu 1', 'sha256:chunk123', 1);
                """
            )
        )
        conn.commit()

        # Negative test 1: invalid authority level (> 100)
        with pytest.raises(IntegrityError):
            conn.execute(
                text(
                    """
                    INSERT INTO knowledge_source (id, source_type, canonical_uri, title, owner_unit, authority_level, approval_status, is_synthetic, version)
                    VALUES ('018f6c4a-5b6c-7123-8abc-def012345604', 'OFFICIAL_DOCUMENT', 'https://huce.edu.vn/doc/bad', 'Bad', 'Unit', 150, 'APPROVED', 1, 1);
                    """
                )
            )
            conn.commit()
        conn.rollback()

        # Negative test 2: duplicate canonical_uri
        with pytest.raises(IntegrityError):
            conn.execute(
                text(
                    """
                    INSERT INTO knowledge_source (id, source_type, canonical_uri, title, owner_unit, authority_level, approval_status, is_synthetic, version)
                    VALUES ('018f6c4a-5b6c-7123-8abc-def012345605', 'OFFICIAL_DOCUMENT', 'https://huce.edu.vn/doc/qd-100', 'Duplicate', 'Unit', 50, 'APPROVED', 1, 1);
                    """
                )
            )
            conn.commit()
        conn.rollback()

        # Downgrade 0002
        mod2.downgrade()
        conn.commit()

        tables_after = set(inspect(conn).get_table_names())
        assert not expected_tables.intersection(tables_after)
        # Identity tables should still exist
        assert "user_identity" in tables_after
