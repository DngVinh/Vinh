from __future__ import annotations

from pathlib import Path
import sys
import pytest

ROOT = Path(__file__).resolve().parents[3]
API_SRC = ROOT / "services" / "api" / "src"
if str(API_SRC) not in sys.path:
    sys.path.insert(0, str(API_SRC))

from campus247.application.retrieval.fusion import FusedCandidate, reciprocal_rank_fusion
from campus247.infrastructure.retrieval.lexical import RetrievalCandidate
from campus247.infrastructure.retrieval.vector import VectorCandidate


def test_reciprocal_rank_fusion_combines_and_ranks() -> None:
    # Candidate appearing rank 1 in lexical and rank 2 in vector
    lexical_candidates = [
        RetrievalCandidate("chunk_A", "ver_1", "Sec 1", "Noi dung A", 10.0),
        RetrievalCandidate("chunk_B", "ver_1", "Sec 2", "Noi dung B", 5.0),
    ]

    vector_candidates = [
        VectorCandidate("chunk_C", "ver_1", "Sec 3", "Noi dung C", 0.95),
        VectorCandidate("chunk_A", "ver_1", "Sec 1", "Noi dung A", 0.90),
    ]

    # k=60
    # chunk_A: 1/(60+1) + 1/(60+2) = 1/61 + 1/62 = 0.016393 + 0.016129 = 0.032522
    # chunk_C: 1/(60+1) = 1/61 = 0.016393
    # chunk_B: 1/(60+2) = 1/62 = 0.016129
    fused = reciprocal_rank_fusion(
        lexical_candidates=lexical_candidates,
        vector_candidates=vector_candidates,
        k=60,
        top_n=20,
    )

    assert len(fused) == 3
    assert isinstance(fused[0], FusedCandidate)
    assert fused[0].chunk_id == "chunk_A"
    assert fused[1].chunk_id == "chunk_C"
    assert fused[2].chunk_id == "chunk_B"
    assert fused[0].rrf_score > fused[1].rrf_score > fused[2].rrf_score


def test_reciprocal_rank_fusion_empty_inputs() -> None:
    fused = reciprocal_rank_fusion(lexical_candidates=[], vector_candidates=[], top_n=10)
    assert fused == []


def test_reciprocal_rank_fusion_top_n_truncation() -> None:
    lexical = [
        RetrievalCandidate(f"chunk_{i}", "ver_1", f"Sec {i}", f"Content {i}", float(100 - i))
        for i in range(10)
    ]
    fused = reciprocal_rank_fusion(lexical_candidates=lexical, vector_candidates=[], top_n=3)
    assert len(fused) == 3
    assert [c.chunk_id for c in fused] == ["chunk_0", "chunk_1", "chunk_2"]
