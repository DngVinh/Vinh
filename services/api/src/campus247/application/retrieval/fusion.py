from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol, Sequence


class RankedCandidate(Protocol):
    chunk_id: str
    document_version_id: str
    section_path: str | None
    content_text: str


@dataclass(frozen=True)
class FusedCandidate:
    chunk_id: str
    document_version_id: str
    section_path: str | None
    content_text: str
    rrf_score: float
    lexical_rank: int | None = None
    vector_rank: int | None = None


def reciprocal_rank_fusion(
    lexical_candidates: Sequence[Any],
    vector_candidates: Sequence[Any],
    k: int = 60,
    top_n: int = 20,
) -> list[FusedCandidate]:
    """Combines lexical and vector retrieval candidates using Reciprocal Rank Fusion (RRF)."""
    scores: dict[str, float] = {}
    lex_ranks: dict[str, int] = {}
    vec_ranks: dict[str, int] = {}
    meta: dict[str, tuple[str, str | None, str]] = {}

    for idx, cand in enumerate(lexical_candidates):
        rank = idx + 1
        cid = cand.chunk_id
        lex_ranks[cid] = rank
        scores[cid] = scores.get(cid, 0.0) + (1.0 / (k + rank))
        meta[cid] = (cand.document_version_id, cand.section_path, cand.content_text)

    for idx, cand in enumerate(vector_candidates):
        rank = idx + 1
        cid = cand.chunk_id
        vec_ranks[cid] = rank
        scores[cid] = scores.get(cid, 0.0) + (1.0 / (k + rank))
        if cid not in meta:
            meta[cid] = (cand.document_version_id, cand.section_path, cand.content_text)

    fused_list: list[FusedCandidate] = []
    for cid, score in scores.items():
        doc_ver_id, sec_path, text = meta[cid]
        fused_list.append(
            FusedCandidate(
                chunk_id=cid,
                document_version_id=doc_ver_id,
                section_path=sec_path,
                content_text=text,
                rrf_score=round(score, 6),
                lexical_rank=lex_ranks.get(cid),
                vector_rank=vec_ranks.get(cid),
            )
        )

    # Sort descending by rrf_score, tie break with chunk_id ascending
    fused_list.sort(key=lambda c: (-c.rrf_score, c.chunk_id))
    return fused_list[:top_n]
