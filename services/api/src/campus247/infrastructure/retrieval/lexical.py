from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
import re
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[6]
API_SRC = ROOT / "services" / "api" / "src"
if str(API_SRC) not in sys.path:
    sys.path.insert(0, str(API_SRC))

import asyncpg
from sqlalchemy import text as sa_text

from campus247.ports.retrieval import ChunkResult


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
class RetrievalCandidate:
    chunk_id: str
    document_version_id: str
    section_path: str | None
    content_text: str
    score: float


class AwaitableList(list):
    """List that can also be awaited in async contexts."""

    def __await__(self):
        async def _coro():
            return self

        return _coro().__await__()


class LexicalSearchAdapter:
    """Lexical full-text search adapter using ts_rank_cd and PostgreSQL tsvector across published chunks."""

    def __init__(
        self,
        db_pool: asyncpg.Pool | asyncpg.Connection | None = None,
        database_url: str | None = None,
    ) -> None:
        self._db_pool = db_pool
        self._database_url = database_url

    def search(
        self,
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        # Backward compatibility: sync search with db_conn as first argument (e.g. SQLite in test_lexical)
        if args and hasattr(args[0], "execute"):
            conn = args[0]
            query = args[1] if len(args) > 1 else kwargs.get("query", "")
            limit = args[2] if len(args) > 2 else kwargs.get("limit", 30)
            return AwaitableList(self._search_sqlite_sync(conn, query, limit))

        query_text = args[0] if args else kwargs.get("query_text", kwargs.get("query", ""))
        top_k = args[1] if len(args) > 1 else kwargs.get("top_k", kwargs.get("limit", 30))
        conn = kwargs.get("conn")
        return self._search_async(query_text, top_k, conn=conn)

    def _search_sqlite_sync(self, conn: Any, query: str, limit: int = 30) -> list[RetrievalCandidate]:
        cleaned = query.strip()
        if not cleaned:
            return []

        tokens = [t.lower() for t in re.findall(r"\w+", cleaned) if len(t) > 1]
        if not tokens:
            return []

        stmt = sa_text(
            """
            SELECT c.id, c.document_version_id, c.section_path, c.content_text
            FROM knowledge_chunk c
            JOIN document_version v ON c.document_version_id = v.id
            WHERE v.status = 'PUBLISHED'
            """
        )
        rows = conn.execute(stmt).fetchall()

        candidates: list[RetrievalCandidate] = []
        for r in rows:
            chunk_id, doc_ver_id, sec_path, content = r[0], r[1], r[2], r[3]
            lower_content = content.lower()
            lower_sec = (sec_path or "").lower()

            match_count = 0
            for token in tokens:
                if token in lower_content:
                    match_count += lower_content.count(token)
                if token in lower_sec:
                    match_count += 2

            if match_count > 0:
                score = round(float(match_count), 4)
                candidates.append(
                    RetrievalCandidate(
                        chunk_id=str(chunk_id),
                        document_version_id=str(doc_ver_id),
                        section_path=sec_path,
                        content_text=content,
                        score=score,
                    )
                )

        candidates.sort(key=lambda c: c.score, reverse=True)
        return candidates[:limit]

    async def _search_async(
        self,
        query_text: str,
        top_k: int = 30,
        conn: asyncpg.Connection | None = None,
    ) -> list[ChunkResult]:
        cleaned = query_text.strip()
        if not cleaned:
            return []

        if conn is not None:
            return await self._execute_db_search(conn, cleaned, top_k)

        target_pool = self._db_pool
        if target_pool is not None:
            if hasattr(target_pool, "acquire"):
                async with target_pool.acquire() as pooled_conn:
                    return await self._execute_db_search(pooled_conn, cleaned, top_k)
            else:
                return await self._execute_db_search(target_pool, cleaned, top_k)

        raw_url = self._database_url or load_database_url()
        conn_url = normalize_asyncpg_url(raw_url)
        temp_conn = await asyncpg.connect(conn_url)
        try:
            return await self._execute_db_search(temp_conn, cleaned, top_k)
        finally:
            await temp_conn.close()

    async def _execute_db_search(
        self,
        conn: asyncpg.Connection,
        query_text: str,
        top_k: int,
    ) -> list[ChunkResult]:
        rows = await conn.fetch(
            """
            SELECT
                c.id,
                c.document_version_id,
                c.content_text,
                c.section_path,
                ts_rank_cd(c.content_tsv, plainto_tsquery('simple', $1)) AS rank_score
            FROM knowledge_chunk c
            JOIN document_version v ON c.document_version_id = v.id
            WHERE v.status = 'PUBLISHED'
              AND c.content_tsv @@ plainto_tsquery('simple', $1)
            ORDER BY rank_score DESC
            LIMIT $2
            """,
            query_text,
            top_k,
        )

        if not rows:
            words = [w.lower() for w in re.findall(r"\w+", query_text) if len(w) > 1]
            if words:
                or_query = " | ".join(words)
                try:
                    rows = await conn.fetch(
                        """
                        SELECT
                            c.id,
                            c.document_version_id,
                            c.content_text,
                            c.section_path,
                            ts_rank_cd(c.content_tsv, to_tsquery('simple', $1)) AS rank_score
                        FROM knowledge_chunk c
                        JOIN document_version v ON c.document_version_id = v.id
                        WHERE v.status = 'PUBLISHED'
                          AND c.content_tsv @@ to_tsquery('simple', $1)
                        ORDER BY rank_score DESC
                        LIMIT $2
                        """,
                        or_query,
                        top_k,
                    )
                except Exception:
                    pass
        return [
            ChunkResult(
                chunk_id=str(r["id"]),
                document_version_id=str(r["document_version_id"]),
                content_text=r["content_text"],
                section_path=r["section_path"],
                score=round(float(r["rank_score"]), 6),
            )
            for r in rows
        ]
