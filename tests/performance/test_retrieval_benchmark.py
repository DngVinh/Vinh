import os
import time
from dataclasses import dataclass
import yaml
import pytest
from campus247.application.retrieval.fusion import reciprocal_rank_fusion
from campus247.application.retrieval.filters import RetrievalFilter


@dataclass
class MockCandidate:
    chunk_id: str
    document_version_id: str
    section_path: str | None
    content_text: str


def load_profile():
    profile_path = os.path.join(os.path.dirname(__file__), "profiles", "retrieval.yaml")
    with open(profile_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def test_retrieval_benchmark_slo_pass():
    profile = load_profile()
    assert profile["benchmark_name"] == "rag_retrieval_latency"
    assert profile["target_slo_p95_ms"] <= 500.0

    # Build mock candidate sets
    lexical_candidates = [
        MockCandidate(f"chunk_{i}", f"doc_{i}", f"sec_{i}", f"Content {i}")
        for i in range(20)
    ]
    vector_candidates = [
        MockCandidate(f"chunk_{i}", f"doc_{i}", f"sec_{i}", f"Content {i}")
        for i in range(10, 30)
    ]

    latencies = []
    for _ in range(profile.get("sample_size", 50)):
        t0 = time.perf_counter()
        fused = reciprocal_rank_fusion(lexical_candidates, vector_candidates, k=60, top_n=10)
        t1 = time.perf_counter()
        latencies.append((t1 - t0) * 1000)

    assert len(fused) == 10
    latencies.sort()
    p95 = latencies[int(len(latencies) * 0.95)]
    assert p95 < profile["target_slo_p95_ms"]


def test_retrieval_benchmark_profile_structure_and_filters():
    profile = load_profile()
    assert "target_slo_p95_ms" in profile
    assert len(profile.get("sample_queries", [])) >= 3

    rf = RetrievalFilter(status="PUBLISHED")
    assert rf.matches({"status": "PUBLISHED", "is_synthetic": True}) is True
    assert rf.matches({"status": "DRAFT"}) is False
