from __future__ import annotations

from dataclasses import dataclass
import hashlib
from typing import Any, Sequence


@dataclass(frozen=True)
class CitationRecord:
    citation_id: str
    source_id: str
    document_version_id: str
    chunk_id: str
    title: str
    issuer: str
    canonical_uri: str
    section_path: str | None
    content_text: str
    quote_span_hash: str
    document_number: str | None = None
    page_start: int | None = None
    page_end: int | None = None
    effective_from: str | None = None
    effective_until: str | None = None
    simulation_label: bool = True


class CitationBundle:
    """Server-side turn-scoped citation bundle mapping local IDs (CIT-001) to immutable chunks."""

    def __init__(self, citations: dict[str, CitationRecord]) -> None:
        self._citations = citations

    @property
    def citations(self) -> dict[str, CitationRecord]:
        return dict(self._citations)

    @classmethod
    def build(cls, chunks: Sequence[dict[str, Any]]) -> CitationBundle:
        citations: dict[str, CitationRecord] = {}
        for idx, item in enumerate(chunks):
            cit_id = f"CIT-{idx + 1:03d}"
            content = item.get("content_text", "")
            span_hash = f"sha256:{hashlib.sha256(content.encode('utf-8')).hexdigest()}"

            rec = CitationRecord(
                citation_id=cit_id,
                source_id=item.get("source_id", ""),
                document_version_id=item.get("document_version_id", ""),
                chunk_id=item.get("chunk_id", ""),
                title=item.get("title", "Untitled Document"),
                issuer=item.get("issuer", "HUCE"),
                canonical_uri=item.get("canonical_uri", ""),
                section_path=item.get("section_path"),
                content_text=content,
                quote_span_hash=span_hash,
                document_number=item.get("document_number"),
                page_start=item.get("page_start"),
                page_end=item.get("page_end"),
                effective_from=item.get("effective_from"),
                effective_until=item.get("effective_until"),
                simulation_label=True,
            )
            citations[cit_id] = rec

        return cls(citations=citations)

    def resolve(self, citation_id: str) -> CitationRecord | None:
        return self._citations.get(citation_id)

    def to_prompt_context(self) -> str:
        blocks: list[str] = []
        for cit_id, rec in sorted(self._citations.items()):
            sec_info = f" ({rec.section_path})" if rec.section_path else ""
            blocks.append(
                f"[{cit_id}] Nguồn: {rec.title}{sec_info}\n"
                f"Nội dung: {rec.content_text}"
            )
        return "\n\n".join(blocks)
