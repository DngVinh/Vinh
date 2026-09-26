from __future__ import annotations

import asyncio
from typing import Any, Sequence

from campus247.ports.retrieval import ChunkResult


def hybrid_search(
    vector_results: Sequence[ChunkResult],
    lexical_results: Sequence[ChunkResult],
    fusion_k: int = 20,
    k: int = 60,
) -> list[ChunkResult]:
    """Combines vector and lexical retrieval results using Reciprocal Rank Fusion (RRF).

    Formula: rrf_score = sum(1 / (k + rank)) where rank is 1-indexed.
    Deduplicates on chunk_id and returns top fusion_k results ordered by rrf_score DESC.
    """
    scores: dict[str, float] = {}
    meta: dict[str, tuple[str, str | None, str]] = {}

    for idx, cand in enumerate(vector_results):
        rank = idx + 1
        cid = cand.chunk_id
        scores[cid] = scores.get(cid, 0.0) + (1.0 / (k + rank))
        if cid not in meta:
            meta[cid] = (cand.document_version_id, cand.section_path, cand.content_text)

    for idx, cand in enumerate(lexical_results):
        rank = idx + 1
        cid = cand.chunk_id
        scores[cid] = scores.get(cid, 0.0) + (1.0 / (k + rank))
        if cid not in meta:
            meta[cid] = (cand.document_version_id, cand.section_path, cand.content_text)

    fused_results: list[ChunkResult] = []
    for cid, score in scores.items():
        doc_ver_id, sec_path, text = meta[cid]
        fused_results.append(
            ChunkResult(
                chunk_id=cid,
                document_version_id=doc_ver_id,
                content_text=text,
                section_path=sec_path,
                score=round(score, 6),
            )
        )

    # Sort descending by rrf_score, tie-break by chunk_id ascending
    fused_results.sort(key=lambda c: (-c.score, c.chunk_id))
    return fused_results[:fusion_k]


reciprocal_rank_fusion = hybrid_search


class HybridSearchAdapter:
    """Orchestrates vector and lexical adapters followed by RRF fusion."""

    def __init__(
        self,
        vector_adapter: Any,
        lexical_adapter: Any,
        fusion_k: int = 20,
        k: int = 60,
    ) -> None:
        self._vector_adapter = vector_adapter
        self._lexical_adapter = lexical_adapter
        self._fusion_k = fusion_k
        self._k = k

    async def search(self, query_text: str, top_k: int = 30) -> list[ChunkResult]:
        vec_res, lex_res = await asyncio.gather(
            self._vector_adapter.search(query_text, top_k=top_k),
            self._lexical_adapter.search(query_text, top_k=top_k),
        )
        return hybrid_search(vec_res, lex_res, fusion_k=self._fusion_k, k=self._k)
