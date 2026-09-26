from __future__ import annotations

from pathlib import Path
import sys
import pytest

ROOT = Path(__file__).resolve().parents[3]
WORKER_SRC = ROOT / "services" / "worker" / "src"
if str(WORKER_SRC) not in sys.path:
    sys.path.insert(0, str(WORKER_SRC))

from campus247_worker.ingestion.acquire import (
    AcquisitionError,
    SourceAcquisitionService,
)


def test_acquire_valid_source() -> None:
    service = SourceAcquisitionService(max_size_bytes=1024 * 1024)
    content = b"# HUCE Quy che hoc vu\nNoi dung chi tiet..."
    record = service.acquire(
        raw_bytes=content,
        filename="quy_che.md",
        content_type="text/markdown",
        origin="admin_portal",
        uploader_id="user_admin_01",
    )
    assert record.filename == "quy_che.md"
    assert record.size_bytes == len(content)
    assert record.content_sha256.startswith("sha256:")
    assert record.quarantine_status == "quarantined"


def test_acquire_empty_payload_fails() -> None:
    service = SourceAcquisitionService()
    with pytest.raises(AcquisitionError, match="Payload is empty"):
        service.acquire(
            raw_bytes=b"",
            filename="empty.txt",
            content_type="text/plain",
            origin="test",
            uploader_id="user_1",
        )


def test_acquire_oversized_payload_fails() -> None:
    service = SourceAcquisitionService(max_size_bytes=100)
    with pytest.raises(AcquisitionError, match="Payload exceeds maximum permitted size"):
        service.acquire(
            raw_bytes=b"a" * 150,
            filename="big.txt",
            content_type="text/plain",
            origin="test",
            uploader_id="user_1",
        )


def test_acquire_unsupported_content_type_fails() -> None:
    service = SourceAcquisitionService()
    with pytest.raises(AcquisitionError, match="Unsupported content type"):
        service.acquire(
            raw_bytes=b"MZ\x90\x00",
            filename="evil.exe",
            content_type="application/x-msdownload",
            origin="test",
            uploader_id="user_1",
        )
