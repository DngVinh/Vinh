from __future__ import annotations

from pathlib import Path
import sys
import pytest

ROOT = Path(__file__).resolve().parents[3]
SYN_SRC = ROOT / "packages" / "synthetic" / "src"
if str(SYN_SRC) not in sys.path:
    sys.path.insert(0, str(SYN_SRC))

from knowledge import generate_knowledge_corpus


def test_generate_knowledge_corpus_deterministic() -> None:
    corpus1 = generate_knowledge_corpus(seed=2026)
    corpus2 = generate_knowledge_corpus(seed=2026)

    assert corpus1 == corpus2
    assert "sources" in corpus1
    assert "documents" in corpus1
    assert len(corpus1["sources"]) >= 3
    assert len(corpus1["documents"]) >= 3

    # Verify fields conform to knowledge schema
    for doc in corpus1["documents"]:
        assert doc["document_version_id"].startswith("01") or len(doc["document_version_id"]) == 36
        assert doc["title"]
        assert doc["raw_text"]
        assert doc["canonical_hash"].startswith("sha256:")
        assert "HUCE" in doc["raw_text"] or "Đại học Xây dựng" in doc["raw_text"]


def test_generate_knowledge_corpus_different_seed() -> None:
    c1 = generate_knowledge_corpus(seed=1)
    c2 = generate_knowledge_corpus(seed=2)
    assert c1["sources"][0]["source_id"] != c2["sources"][0]["source_id"]


def test_generate_knowledge_corpus_with_courses() -> None:
    corpus = generate_knowledge_corpus(seed=2026, include_courses=True)
    assert len(corpus["documents"]) >= 20
    assert any("course_" in s["source_id"] or "courses" in s["uri"] for s in corpus["sources"])

