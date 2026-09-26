from __future__ import annotations

from pathlib import Path
from typing import Any
import hashlib
import json
import yaml


class SeedValidationError(ValueError):
    """Raised when non-synthetic data or real identifiers are detected."""


class DemoSeedPacker:
    SYNTHETIC_DOMAIN = "@synthetic.huce.edu.vn"

    def __init__(self, manifest_path: str = "scripts/demo/manifest.yaml") -> None:
        self.manifest_path = Path(manifest_path)

    def load_manifest(self) -> dict[str, Any]:
        if not self.manifest_path.exists():
            raise FileNotFoundError(f"Manifest not found at {self.manifest_path}")
        return yaml.safe_load(self.manifest_path.read_text(encoding="utf-8"))

    def validate_record(self, record: dict[str, Any]) -> None:
        if not record.get("is_synthetic"):
            raise SeedValidationError(
                f"Non-synthetic or real PII detected: record {record.get('id')} lacks is_synthetic=True"
            )
        email = record.get("email", "")
        if not email.endswith(self.SYNTHETIC_DOMAIN):
            raise SeedValidationError(
                f"Non-synthetic or real PII detected: email '{email}' does not end with {self.SYNTHETIC_DOMAIN}"
            )

    def generate_pack(self, seed: int = 42) -> dict[str, Any]:
        manifest = self.load_manifest()

        identities: list[dict[str, Any]] = []
        for i in range(10):
            record = {
                "id": f"USR-SYNTH-{seed}-{i:03d}",
                "full_name": f"Sinh Vien Demo {i+1}",
                "student_code": f"SV24{i:04d}",
                "email": f"demo.sv{i+1}{self.SYNTHETIC_DOMAIN}",
                "role": "student",
                "is_synthetic": True,
                "disclaimer": "MÔ PHỎNG NỘI BỘ — DỮ LIỆU TỔNG HỢP KHÔNG CÓ THỰC",
            }
            self.validate_record(record)
            identities.append(record)

        services: list[dict[str, Any]] = [
            {
                "id": "SRV-SYNTH-001",
                "name": "Cấp giấy xác nhận sinh viên",
                "processing_days": 2,
                "fee_vnd": 0,
                "is_synthetic": True,
            },
            {
                "id": "SRV-SYNTH-002",
                "name": "Mượn phòng học nhóm H1",
                "processing_days": 1,
                "fee_vnd": 0,
                "is_synthetic": True,
            },
        ]

        knowledge_items: list[dict[str, Any]] = [
            {
                "id": "DOC-SYNTH-001",
                "title": "Quy chế đào tạo đại học chính quy HUCE (Demo)",
                "content_hash": hashlib.sha256(b"HUCE_REGULATIONS_SYNTHETIC").hexdigest(),
                "is_synthetic": True,
            },
            {
                "id": "DOC-SYNTH-002",
                "title": "Hướng dẫn sử dụng thư viện và mượn phòng (Demo)",
                "content_hash": hashlib.sha256(b"HUCE_LIBRARY_SYNTHETIC").hexdigest(),
                "is_synthetic": True,
            },
        ]

        pack = {
            "manifest": manifest,
            "identities": identities,
            "services": services,
            "knowledge_items": knowledge_items,
            "pack_checksum": hashlib.sha256(
                json.dumps(identities, sort_keys=True).encode("utf-8")
            ).hexdigest(),
        }
        return pack
