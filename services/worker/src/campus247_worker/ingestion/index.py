from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from sqlalchemy import Connection, text


@dataclass(frozen=True)
class ChunkIndexPayload:
    chunk_id: str
    document_version_id: str
    ordinal: int
    section_path: str | None
    content_text: str
    content_checksum: str
    page_start: int | None = None
    page_end: int | None = None
    embedding_vector: list[float] | None = None


class KnowledgeIndexer:
    """Persists version-bound knowledge chunk index records."""

    def persist_chunks(self, conn: Connection, chunks: list[ChunkIndexPayload]) -> int:
        if not chunks:
            return 0

        stmt = text(
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
                version
            ) VALUES (
                :id,
                :document_version_id,
                :ordinal,
                :section_path,
                :page_start,
                :page_end,
                :content_text,
                :content_checksum,
                1
            )
            """
        )

        params = [
            {
                "id": c.chunk_id,
                "document_version_id": c.document_version_id,
                "ordinal": c.ordinal,
                "section_path": c.section_path,
                "page_start": c.page_start,
                "page_end": c.page_end,
                "content_text": c.content_text,
                "content_checksum": c.content_checksum,
            }
            for c in chunks
        ]

        conn.execute(stmt, params)
        conn.commit()
        return len(chunks)
