from __future__ import annotations

from pathlib import Path
import socket
import sys
import pytest

ROOT = Path(__file__).resolve().parents[2]
API_SRC = ROOT / "services" / "api" / "src"
WORKER_SRC = ROOT / "services" / "worker" / "src"

for p in (str(API_SRC), str(WORKER_SRC)):
    if p not in sys.path:
        sys.path.insert(0, p)

from campus247.infrastructure.retrieval.hybrid import (
    HybridSearchAdapter,
    hybrid_search,
)
from campus247.infrastructure.retrieval.lexical import LexicalSearchAdapter
from campus247.infrastructure.retrieval.vector import VectorSearchAdapter
from campus247.ports.retrieval import ChunkResult


def _is_postgres_available(host: str = "localhost", port: int = 5433) -> bool:
    try:
        with socket.create_connection((host, port), timeout=0.5):
            return True
    except (OSError, ConnectionRefusedError):
        return False


def test_rrf_fusion_logic() -> None:
    """Verify RRF score calculation: sum(1 / (60 + rank)) for 1-based ranks."""
    vec_results = [
        ChunkResult(
            chunk_id="chunk-1",
            document_version_id="ver-1",
            content_text="Quy định học phí tín chỉ",
            section_path="Học phí",
            score=0.9,
        ),
        ChunkResult(
            chunk_id="chunk-2",
            document_version_id="ver-1",
            content_text="Học bổng khuyến khích",
            section_path="Học bổng",
            score=0.8,
        ),
    ]

    lex_results = [
        ChunkResult(
            chunk_id="chunk-2",
            document_version_id="ver-1",
            content_text="Học bổng khuyến khích",
            section_path="Học bổng",
            score=5.0,
        ),
        ChunkResult(
            chunk_id="chunk-3",
            document_version_id="ver-2",
            content_text="Ký túc xá sinh viên",
            section_path="Ký túc xá",
            score=3.0,
        ),
    ]

    fused = hybrid_search(vec_results, lex_results, fusion_k=20, k=60)

    # chunk-2 appears at rank 2 in vector (1/62) and rank 1 in lexical (1/61)
    expected_chunk_2 = round(1.0 / 62 + 1.0 / 61, 6)
    # chunk-1 appears at rank 1 in vector (1/61)
    expected_chunk_1 = round(1.0 / 61, 6)
    # chunk-3 appears at rank 2 in lexical (1/62)
    expected_chunk_3 = round(1.0 / 62, 6)

    assert len(fused) == 3
    assert fused[0].chunk_id == "chunk-2"
    assert pytest.approx(fused[0].score, 1e-6) == expected_chunk_2
    assert fused[1].chunk_id == "chunk-1"
    assert pytest.approx(fused[1].score, 1e-6) == expected_chunk_1
    assert fused[2].chunk_id == "chunk-3"
    assert pytest.approx(fused[2].score, 1e-6) == expected_chunk_3


def test_hybrid_search_deduplicates_correctly() -> None:
    """Verify hybrid search deduplicates candidates on chunk_id."""
    vec_results = [
        ChunkResult(chunk_id=f"c-{i}", document_version_id="v1", content_text=f"Text {i}")
        for i in range(10)
    ]
    lex_results = [
        ChunkResult(chunk_id=f"c-{i}", document_version_id="v1", content_text=f"Text {i}")
        for i in range(5, 15)
    ]

    fused = hybrid_search(vec_results, lex_results, fusion_k=30)
    chunk_ids = [c.chunk_id for c in fused]

    # Should have exactly 15 unique chunks (0..14)
    assert len(chunk_ids) == 15
    assert len(set(chunk_ids)) == 15

    # Chunks 5..9 appeared in both lists, so they must rank higher than single-source chunks
    for i in range(5, 10):
        cid = f"c-{i}"
        chunk = next(c for c in fused if c.chunk_id == cid)
        # Two appearances: 1/(60+rank1) + 1/(60+rank2) > single appearance 1/61
        assert chunk.score > (1.0 / 61)


def test_score_ordering() -> None:
    """Verify results are strictly ordered descending by score."""
    vec_results = [
        ChunkResult(chunk_id=f"vec-{i}", document_version_id="v1", content_text=f"Vec {i}")
        for i in range(15)
    ]
    lex_results = [
        ChunkResult(chunk_id=f"lex-{i}", document_version_id="v1", content_text=f"Lex {i}")
        for i in range(15)
    ]

    fused = hybrid_search(vec_results, lex_results, fusion_k=20)

    scores = [c.score for c in fused]
    assert scores == sorted(scores, reverse=True)
    assert len(fused) == 20


def test_empty_lists() -> None:
    """Verify handling of empty inputs."""
    assert hybrid_search([], []) == []

    single = [ChunkResult(chunk_id="c1", document_version_id="v1", content_text="Hi")]
    fused_vec = hybrid_search(single, [])
    assert len(fused_vec) == 1
    assert fused_vec[0].score == round(1.0 / 61, 6)

    fused_lex = hybrid_search([], single)
    assert len(fused_lex) == 1
    assert fused_lex[0].score == round(1.0 / 61, 6)


@pytest.mark.asyncio
async def test_database_retrieval_integration() -> None:
    """Integration test against actual PostgreSQL instance seeded with knowledge chunks."""
    if not _is_postgres_available():
        pytest.skip("PostgreSQL instance not reachable on port 5433 (live environment only)")

    vec_adapter = VectorSearchAdapter()
    lex_adapter = LexicalSearchAdapter()

    # Search with lexical
    lex_results = await lex_adapter.search("học phí", top_k=5)
    assert isinstance(lex_results, list)
    assert len(lex_results) > 0
    assert any("học phí" in r.content_text.lower() for r in lex_results)

    # Search with vector
    vec_results = await vec_adapter.search("học phí", top_k=5)
    assert isinstance(vec_results, list)
    assert len(vec_results) > 0
    assert all(r.score is not None for r in vec_results)

    # Hybrid fusion
    hybrid_adapter = HybridSearchAdapter(vec_adapter, lex_adapter, fusion_k=10)
    hybrid_results = await hybrid_adapter.search("học phí", top_k=10)

    assert len(hybrid_results) > 0
    assert len(hybrid_results) <= 10
    scores = [r.score for r in hybrid_results]
    assert scores == sorted(scores, reverse=True)
