from __future__ import annotations

from pathlib import Path
import sys
import unicodedata
import pytest

ROOT = Path(__file__).resolve().parents[3]
WORKER_SRC = ROOT / "services" / "worker" / "src"
if str(WORKER_SRC) not in sys.path:
    sys.path.insert(0, str(WORKER_SRC))

from campus247_worker.ingestion.parse import DocumentParser, ParsedDocument


def test_parse_markdown_with_headings_and_provenance() -> None:
    parser = DocumentParser()
    raw_md = (
        "# Quy chế Đào tạo\n\n"
        "Quy chế áp dụng cho toàn thể sinh viên HUCE.\n\n"
        "## Điều 1. Đăng ký tín chỉ\n\n"
        "Sinh viên đăng ký tối thiểu 14 tín chỉ mỗi học kỳ.\n\n"
        "## Điều 2. Học lại\n\n"
        "Sinh viên bị điểm F phải đăng ký học lại."
    )

    doc = parser.parse(raw_md, metadata={"source_id": "src_123"})
    assert isinstance(doc, ParsedDocument)
    assert doc.title == "Quy chế Đào tạo"
    assert len(doc.sections) == 3
    assert doc.sections[0].section_title == "Quy chế Đào tạo"
    assert doc.sections[1].section_title == "Điều 1. Đăng ký tín chỉ"
    assert doc.sections[1].section_path == "Quy chế Đào tạo > Điều 1. Đăng ký tín chỉ"
    assert "tối thiểu 14 tín chỉ" in doc.sections[1].content
    assert doc.sections[1].char_start >= 0
    assert doc.sections[1].char_end > doc.sections[1].char_start
    assert doc.canonical_hash.startswith("sha256:")


def test_parse_unicode_nfc_normalization() -> None:
    parser = DocumentParser()
    decomposed = unicodedata.normalize("NFD", "Trường Đại học Xây dựng Hà Nội")
    doc = parser.parse(decomposed)
    assert doc.canonical_text == unicodedata.normalize("NFC", decomposed)


def test_parse_empty_content_fails() -> None:
    parser = DocumentParser()
    with pytest.raises(ValueError, match="Input text is empty"):
        parser.parse("   \n\n   ")
