from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
import pytest
from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy import create_engine, text

ROOT = Path(__file__).resolve().parents[3]
WORKER_SRC = ROOT / "services" / "worker" / "src"
if str(WORKER_SRC) not in sys.path:
    sys.path.insert(0, str(WORKER_SRC))

from campus247_worker.ingestion.index import ChunkIndexPayload, KnowledgeIndexer

MIGRATION_0001 = ROOT / "services" / "api" / "migrations" / "versions" / "0001_identity.py"
MIGRATION_0002 = ROOT / "services" / "api" / "migrations" / "versions" / "0002_knowledge.py"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture
def db_conn():
    engine = create_engine("sqlite:///:memory:", echo=False)
    mod1 = load_module("migration_0001", MIGRATION_0001)
    mod2 = load_module("migration_0002", MIGRATION_0002)

    with engine.connect() as conn:
        ctx = MigrationContext.configure(conn)
        op = Operations(ctx)
        mod1.op = op
        mod1.upgrade()
        mod2.op = op
        mod2.upgrade()
        conn.commit()

        # Seed source and document_version
        conn.execute(
            text(
                """
                INSERT INTO knowledge_source (id, source_type, canonical_uri, title, owner_unit, authority_level, approval_status, is_synthetic, version)
                VALUES ('018f6c4a-5b6c-7123-8abc-def012345601', 'OFFICIAL_DOCUMENT', 'https://huce.edu.vn/doc/qd-index', 'Quy chế HUCE', 'Phòng Đào tạo', 90, 'APPROVED', 1, 1);
                """
            )
        )
        conn.execute(
            text(
                """
                INSERT INTO document_version (id, knowledge_source_id, version_label, content_checksum, status, storage_object_key, version)
                VALUES ('018f6c4a-5b6c-7123-8abc-def012345602', '018f6c4a-5b6c-7123-8abc-def012345601', 'v1.0', 'sha256:abc', 'PUBLISHED', 'docs/qd.pdf', 1);
                """
            )
        )
        conn.commit()
        yield conn


def test_persist_chunks_success(db_conn) -> None:
    indexer = KnowledgeIndexer()
    doc_ver_id = "018f6c4a-5b6c-7123-8abc-def012345602"

    payloads = [
        ChunkIndexPayload(
            chunk_id="018f6c4a-5b6c-7123-8abc-def012345603",
            document_version_id=doc_ver_id,
            ordinal=1,
            section_path="Dieu 1",
            content_text="Noi dung dieu 1",
            content_checksum="sha256:chunk1",
            page_start=1,
            page_end=1,
        ),
        ChunkIndexPayload(
            chunk_id="018f6c4a-5b6c-7123-8abc-def012345604",
            document_version_id=doc_ver_id,
            ordinal=2,
            section_path="Dieu 2",
            content_text="Noi dung dieu 2",
            content_checksum="sha256:chunk2",
            page_start=2,
            page_end=2,
        ),
    ]

    count = indexer.persist_chunks(db_conn, payloads)
    assert count == 2

    # Verify rows persisted
    rows = db_conn.execute(text("SELECT id, ordinal, content_text FROM knowledge_chunk ORDER BY ordinal")).fetchall()
    assert len(rows) == 2
    assert rows[0][1] == 1
    assert rows[1][2] == "Noi dung dieu 2"


def test_persist_empty_chunks_returns_zero(db_conn) -> None:
    indexer = KnowledgeIndexer()
    count = indexer.persist_chunks(db_conn, [])
    assert count == 0
