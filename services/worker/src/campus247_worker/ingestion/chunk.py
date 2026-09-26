from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
from typing import Any
import uuid

from campus247_worker.ingestion.parse import ParsedDocument


@dataclass(frozen=True)
class ChunkRecord:
    chunk_id: str
    document_version_id: str
    section_path: str
    chunk_index: int
    content: str
    text_sha256: str
    char_start: int
    char_end: int
    metadata: dict[str, Any] = field(default_factory=dict)


def _deterministic_uuid7(seed: str) -> str:
    h = hashlib.sha256(seed.encode("utf-8")).digest()
    raw = bytearray(h[:16])
    raw[6] = (raw[6] & 0x0F) | 0x70  # Version 7
    raw[8] = (raw[8] & 0x3F) | 0x80  # Variant
    return str(uuid.UUID(bytes=bytes(raw)))


class SemanticChunker:
    """Structure-aware deterministic text chunking engine."""

    def __init__(self, max_chars: int = 1200, overlap_chars: int = 150) -> None:
        self._max_chars = max_chars
        self._overlap_chars = overlap_chars

    def _split_text_by_window(self, text: str) -> list[str]:
        if len(text) <= self._max_chars:
            return [text]
        step = max(1, self._max_chars - self._overlap_chars)
        parts: list[str] = []
        for i in range(0, len(text), step):
            part = text[i : i + self._max_chars]
            if part.strip():
                parts.append(part.strip())
            if i + self._max_chars >= len(text):
                break
        return parts

    def chunk(self, doc: ParsedDocument, document_version_id: str) -> tuple[ChunkRecord, ...]:
        if not doc.sections or not doc.canonical_text:
            return ()

        chunks: list[ChunkRecord] = []
        chunk_idx = 0

        for sec in doc.sections:
            text = sec.content.strip()
            if not text:
                continue

            windows = self._split_text_by_window(text)
            sec_offset = sec.char_start

            for win in windows:
                cid = _deterministic_uuid7(f"{document_version_id}-chunk-{chunk_idx}")
                c_hash = f"sha256:{hashlib.sha256(win.encode('utf-8')).hexdigest()}"
                chunks.append(
                    ChunkRecord(
                        chunk_id=cid,
                        document_version_id=document_version_id,
                        section_path=sec.section_path,
                        chunk_index=chunk_idx,
                        content=win,
                        text_sha256=c_hash,
                        char_start=sec_offset,
                        char_end=sec_offset + len(win),
                        metadata=dict(doc.metadata),
                    )
                )
                chunk_idx += 1
                sec_offset += max(1, len(win) - self._overlap_chars)

        return tuple(chunks)
