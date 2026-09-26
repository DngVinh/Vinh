from __future__ import annotations

import asyncio
import os
from pathlib import Path
import sys
import uuid
from typing import Any

# Ensure path resolution
ROOT = Path(__file__).resolve().parents[1]
WORKER_SRC = ROOT / "services" / "worker" / "src"
API_SRC = ROOT / "services" / "api" / "src"
SYNTH_SRC = ROOT / "packages" / "synthetic" / "src"

for p in (str(WORKER_SRC), str(API_SRC), str(SYNTH_SRC)):
    if p not in sys.path:
        sys.path.insert(0, p)

import asyncpg
from pgvector.asyncpg import register_vector

from campus247_worker.ingestion.chunk import SemanticChunker
from campus247_worker.ingestion.embed_fake import DeterministicEmbeddingAdapter
from campus247_worker.ingestion.index import ChunkIndexPayload
from campus247_worker.ingestion.parse import DocumentParser
from knowledge import generate_knowledge_corpus


def load_database_url() -> str:
    """Load DATABASE_URL from .env file or environment."""
    env_file = ROOT / ".env"
    if env_file.is_file():
        for line in env_file.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if line.startswith("DATABASE_URL="):
                val = line.split("=", 1)[1].strip()
                if (val.startswith('"') and val.endswith('"')) or (val.startswith("'") and val.endswith("'")):
                    val = val[1:-1]
                return val
    return os.getenv("DATABASE_URL", "postgresql://campus247:campus247_local_dev@localhost:5433/campus247_local")


def normalize_asyncpg_url(url: str) -> str:
    """Convert SQLAlchemy async URL to standard asyncpg connection URL."""
    prefix = "postgresql+asyncpg://"
    if url.startswith(prefix):
        return "postgresql://" + url[len(prefix):]
    return url


async def run_ingestion() -> int:
    raw_url = load_database_url()
    conn_url = normalize_asyncpg_url(raw_url)
    print(f"Connecting to database: {conn_url.split('@')[-1] if '@' in conn_url else conn_url}")

    conn = await asyncpg.connect(conn_url)
    try:
        await register_vector(conn)

        # 1. Fetch published document versions joined with knowledge sources
        rows = await conn.fetch(
            """
            SELECT
                v.id AS document_version_id,
                v.knowledge_source_id,
                v.version_label,
                s.title,
                s.canonical_uri
            FROM document_version v
            JOIN knowledge_source s ON v.knowledge_source_id = s.id
            WHERE v.status = 'PUBLISHED'
            ORDER BY v.id
            """
        )
        print(f"Found {len(rows)} published document versions in database")

        # 2. Reconstruct knowledge corpus from deterministic generator
        knowledge_data = generate_knowledge_corpus(seed=2026, include_courses=True)
        doc_by_id: dict[str, dict[str, Any]] = {
            str(doc["document_version_id"]): doc for doc in knowledge_data["documents"]
        }

        parser = DocumentParser()
        chunker = SemanticChunker(max_chars=1200, overlap_chars=150)
        embedder = DeterministicEmbeddingAdapter(dimension=1536)

        chunk_payloads: list[ChunkIndexPayload] = []

        for row in rows:
            doc_ver_id = str(row["document_version_id"])
            doc_gen = doc_by_id.get(doc_ver_id)
            if not doc_gen:
                continue

            raw_text = doc_gen["raw_text"]
            metadata = {
                "title": row["title"],
                "source_id": str(row["knowledge_source_id"]),
                "canonical_uri": row["canonical_uri"],
            }

            parsed_doc = parser.parse(raw_text, metadata=metadata)
            chunks = chunker.chunk(parsed_doc, doc_ver_id)
            if not chunks:
                continue

            chunk_texts = [c.content for c in chunks]
            embeddings = embedder.embed_batch(chunk_texts)

            for c, emb in zip(chunks, embeddings):
                chunk_payloads.append(
                    ChunkIndexPayload(
                        chunk_id=c.chunk_id,
                        document_version_id=c.document_version_id,
                        ordinal=c.chunk_index,
                        section_path=c.section_path,
                        content_text=c.content,
                        content_checksum=c.text_sha256[:64],
                        embedding_vector=emb,
                    )
                )

        print(f"Prepared {len(chunk_payloads)} chunks for ingestion")

        # 3. Batch INSERT with ON CONFLICT DO UPDATE
        insert_records = [
            (
                uuid.UUID(p.chunk_id),
                uuid.UUID(p.document_version_id),
                p.ordinal,
                p.section_path,
                p.page_start,
                p.page_end,
                p.content_text,
                p.content_checksum,
                p.embedding_vector,
            )
            for p in chunk_payloads
        ]

        if insert_records:
            batch_size = 500
            for i in range(0, len(insert_records), batch_size):
                batch = insert_records[i : i + batch_size]
                await conn.executemany(
                    """
                    INSERT INTO knowledge_chunk (
                        id,
                        document_version_id,
                        ordinal,
                        section_path,
                        page_start,
                        page_end,
                        content_text,
                        content_checksum,
                        embedding,
                        content_tsv,
                        version
                    ) VALUES (
                        $1, $2, $3, $4, $5, $6, $7, $8, $9, to_tsvector('simple', $7), 1
                    )
                    ON CONFLICT (document_version_id, ordinal)
                    DO UPDATE SET
                        embedding = EXCLUDED.embedding,
                        content_tsv = to_tsvector('simple', EXCLUDED.content_text)
                    """,
                    batch,
                )

        # 4. Update content_tsv for any chunks where content_tsv IS NULL
        await conn.execute(
            """
            UPDATE knowledge_chunk
            SET content_tsv = to_tsvector('simple', content_text)
            WHERE content_tsv IS NULL
            """
        )

        # Verify count
        total_chunks = await conn.fetchval("SELECT COUNT(*) FROM knowledge_chunk")
        print(f"Total knowledge_chunk records in DB: {total_chunks}")
        print(f"Ingestion completed successfully. Chunks inserted: {len(insert_records)}")
        return len(insert_records)

    finally:
        await conn.close()


def main() -> None:
    asyncio.run(run_ingestion())


if __name__ == "__main__":
    main()
