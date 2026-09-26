from __future__ import annotations

from pathlib import Path
import sys
import pytest

ROOT = Path(__file__).resolve().parents[3]
WORKER_SRC = ROOT / "services" / "worker" / "src"
if str(WORKER_SRC) not in sys.path:
    sys.path.insert(0, str(WORKER_SRC))

from campus247_worker.ingestion.chunk import ChunkRecord, SemanticChunker
from campus247_worker.ingestion.parse import DocumentParser


def test_chunk_document_deterministic() -> None:
    parser = DocumentParser()
    raw = (
        "# Quy chế Đào tạo\n\n"
        "## Điều 1. Đăng ký tín chỉ\n\n"
        "Sinh viên đăng ký tối thiểu 14 tín chỉ mỗi học kỳ.\n\n"
        "## Điều 2. Học lại\n\n"
        "Sinh viên bị điểm F phải đăng ký học lại."
    )
    doc = parser.parse(raw)
    chunker = SemanticChunker(max_chars=500, overlap_chars=50)

    doc_version_id = "018f0000-0000-7000-8000-000000000001"
    chunks1 = chunker.chunk(doc, document_version_id=doc_version_id)
    chunks2 = chunker.chunk(doc, document_version_id=doc_version_id)

    assert len(chunks1) == len(chunks2)
    assert chunks1 == chunks2

    for c in chunks1:
        assert isinstance(c, ChunkRecord)
        assert c.document_version_id == doc_version_id
        assert c.chunk_id
        assert c.text_sha256.startswith("sha256:")
        assert c.char_end > c.char_start


def test_chunk_large_section_splits() -> None:
    parser = DocumentParser()
    long_para = "HUCE " * 100  # 500 chars
    raw = f"# Test Document\n\n## Section Long\n\n{long_para}\n\n{long_para}"
    doc = parser.parse(raw)

    chunker = SemanticChunker(max_chars=400, overlap_chars=50)
    chunks = chunker.chunk(doc, document_version_id="018f0000-0000-7000-8000-000000000002")
    assert len(chunks) >= 2
    assert all(len(c.content) <= 550 for c in chunks)


def test_chunk_empty_document_returns_empty() -> None:
    chunker = SemanticChunker()
    # Create empty mock
    from campus247_worker.ingestion.parse import ParsedDocument
    empty_doc = ParsedDocument(
        title="Empty",
        canonical_text="",
        canonical_hash="sha256:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        sections=(),
    )
    chunks = chunker.chunk(empty_doc, document_version_id="018f0000-0000-7000-8000-000000000003")
    assert chunks == ()
