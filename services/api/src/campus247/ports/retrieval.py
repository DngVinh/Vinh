from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class ChunkResult:
    chunk_id: str
    document_version_id: str
    content_text: str
    section_path: str | None = None
    score: float = 0.0


class RetrievalPort(Protocol):
    """Port interface for knowledge chunk retrieval."""

    async def search(self, query_text: str, top_k: int = 30) -> list[ChunkResult]:
        ...
