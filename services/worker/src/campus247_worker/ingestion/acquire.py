from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
from typing import Literal
import uuid

ALLOWED_CONTENT_TYPES = {
    "text/plain",
    "text/markdown",
    "application/json",
    "application/pdf",
}


class AcquisitionError(Exception):
    """Raised when source acquisition fails quarantine validation."""
    pass


@dataclass(frozen=True)
class AcquisitionRecord:
    source_id: str
    acquisition_id: str
    filename: str
    content_type: str
    content_sha256: str
    size_bytes: int
    origin: str
    uploader_id: str
    quarantine_status: Literal["quarantined", "scanning", "released", "rejected"]
    acquired_at: datetime


class SourceAcquisitionService:
    """Acquires untrusted sources into quarantined storage records."""

    def __init__(self, max_size_bytes: int = 10 * 1024 * 1024) -> None:
        self._max_size_bytes = max_size_bytes

    def acquire(
        self,
        raw_bytes: bytes,
        filename: str,
        content_type: str,
        origin: str,
        uploader_id: str,
    ) -> AcquisitionRecord:
        if not raw_bytes:
            raise AcquisitionError("Payload is empty")

        if len(raw_bytes) > self._max_size_bytes:
            raise AcquisitionError(
                f"Payload exceeds maximum permitted size: {len(raw_bytes)} > {self._max_size_bytes} bytes"
            )

        if content_type.lower() not in ALLOWED_CONTENT_TYPES:
            raise AcquisitionError(
                f"Unsupported content type '{content_type}'. Allowed: {sorted(ALLOWED_CONTENT_TYPES)}"
            )

        sha256_hash = f"sha256:{hashlib.sha256(raw_bytes).hexdigest()}"
        source_id = str(uuid.uuid4())
        acquisition_id = str(uuid.uuid4())

        return AcquisitionRecord(
            source_id=source_id,
            acquisition_id=acquisition_id,
            filename=filename,
            content_type=content_type.lower(),
            content_sha256=sha256_hash,
            size_bytes=len(raw_bytes),
            origin=origin,
            uploader_id=uploader_id,
            quarantine_status="quarantined",
            acquired_at=datetime.now(timezone.utc),
        )
