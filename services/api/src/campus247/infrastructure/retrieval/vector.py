from __future__ import annotations

from dataclasses import dataclass
import math
import os
from pathlib import Path
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[6]
WORKER_SRC = ROOT / "services" / "worker" / "src"
API_SRC = ROOT / "services" / "api" / "src"
for p in (str(WORKER_SRC), str(API_SRC)):
    if p not in sys.path:
        sys.path.insert(0, p)

import asyncpg
from pgvector.asyncpg import register_vector

from campus247.ports.retrieval import ChunkResult
from campus247_worker.ingestion.embed_fake import DeterministicEmbeddingAdapter


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


@dataclass(frozen=True)
class VectorIndexEntry:
    chunk_id: str
    document_version_id: str
    section_path: str | None
    content_text: str
    embedding: list[float]


@dataclass(frozen=True)
class VectorCandidate:
    chunk_id: str
    document_version_id: str
    section_path: str | None
    content_text: str
    similarity: float


def _cosine_similarity(vec_a: list[float], vec_b: list[float]) -> float:
    if len(vec_a) != len(vec_b):
        return 0.0
    dot = sum(a * b for a, b in zip(vec_a, vec_b))
    norm_a = math.sqrt(sum(a * a for a in vec_a))
    norm_b = math.sqrt(sum(b * b for b in vec_b))
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return dot / (norm_a * norm_b)


class AwaitableList(list):
    """List that can also be awaited in async contexts."""

    def __await__(self):
        async def _coro():
            return self

        return _coro().__await__()


class VectorSearchAdapter:
    """Vector similarity search adapter using pgvector cosine distance across published chunks."""

    def __init__(
        self,
        db_pool: asyncpg.Pool | asyncpg.Connection | None = None,
        database_url: str | None = None,
        dimension: int = 1536,
    ) -> None:
        self._db_pool = db_pool
        self._database_url = database_url
        self._dimension = dimension
        self._embedder = DeterministicEmbeddingAdapter(dimension=dimension)
        self._entries: list[VectorIndexEntry] = []

    def add_entry(self, entry: VectorIndexEntry) -> None:
        self._entries.append(entry)

    def search(
        self,
        query_text: str = "",
        top_k: int = 30,
        *,
        query_vector: list[float] | None = None,
        limit: int | None = None,
        conn: asyncpg.Connection | None = None,
    ) -> Any:
        # In-memory sync search backward compatibility
        if query_vector is not None or (not query_text and self._entries):
            effective_limit = limit if limit is not None else top_k
            q_vec = query_vector if query_vector is not None else []
            if not q_vec:
                raise ValueError("Query vector cannot be empty")
            scored: list[VectorCandidate] = []
            for entry in self._entries:
                sim = _cosine_similarity(q_vec, entry.embedding)
                scored.append(
                    VectorCandidate(
                        chunk_id=entry.chunk_id,
                        document_version_id=entry.document_version_id,
                        section_path=entry.section_path,
                        content_text=entry.content_text,
                        similarity=round(sim, 4),
                    )
                )
            scored.sort(key=lambda c: c.similarity, reverse=True)
            return AwaitableList(scored[:effective_limit])

        # Async pgvector search
        effective_k = limit if limit is not None else top_k
        return self._search_async(query_text, effective_k, conn=conn)

    async def _search_async(
        self,
        query_text: str,
        top_k: int = 30,
        conn: asyncpg.Connection | None = None,
    ) -> list[ChunkResult]:
        cleaned = query_text.strip()
        if not cleaned:
            return []

        query_embedding = self._embedder.embed_text(cleaned)

        if conn is not None:
            return await self._execute_db_search(conn, query_embedding, top_k)

        target_pool = self._db_pool
        if target_pool is not None:
            if hasattr(target_pool, "acquire"):
                async with target_pool.acquire() as pooled_conn:
                    return await self._execute_db_search(pooled_conn, query_embedding, top_k)
            else:
                return await self._execute_db_search(target_pool, query_embedding, top_k)

        raw_url = self._database_url or load_database_url()
        conn_url = normalize_asyncpg_url(raw_url)
        temp_conn = await asyncpg.connect(conn_url)
        try:
            return await self._execute_db_search(temp_conn, query_embedding, top_k)
        finally:
            await temp_conn.close()

    async def _execute_db_search(
        self,
        conn: asyncpg.Connection,
        query_embedding: list[float],
        top_k: int,
    ) -> list[ChunkResult]:
        await register_vector(conn)
        rows = await conn.fetch(
            """
            SELECT
                c.id,
                c.document_version_id,
                c.content_text,
                c.section_path,
                (c.embedding <=> $1) AS distance
            FROM knowledge_chunk c
            JOIN document_version v ON c.document_version_id = v.id
            WHERE v.status = 'PUBLISHED'
              AND c.embedding IS NOT NULL
            ORDER BY distance ASC
            LIMIT $2
            """,
            query_embedding,
            top_k,
        )
        return [
            ChunkResult(
                chunk_id=str(r["id"]),
                document_version_id=str(r["document_version_id"]),
                content_text=r["content_text"],
                section_path=r["section_path"],
                score=round(1.0 - float(r["distance"]), 6),
            )
            for r in rows
        ]
