from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timezone
from enum import StrEnum
import os
import re
import time
from typing import Any
import uuid

UUIDV7_REGEX = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-7[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$"
)


def generate_uuid7() -> str:
    if hasattr(uuid, "uuid7"):
        return str(uuid.uuid7())
    ms = int(time.time() * 1000)
    rand_a = int.from_bytes(os.urandom(2), "big") & 0x0FFF
    rand_b = int.from_bytes(os.urandom(8), "big") & 0x3FFFFFFFFFFFFFFF
    u = (ms << 80) | (0x7 << 76) | (rand_a << 64) | (0x2 << 62) | rand_b
    return str(uuid.UUID(int=u))


def is_valid_uuid7(value: str) -> bool:
    return bool(UUIDV7_REGEX.fullmatch(value.lower()))


def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def format_rfc3339(dt: datetime) -> str:
    utc_dt = dt.astimezone(timezone.utc)
    # Output YYYY-MM-DDTHH:MM:SSZ or with microseconds if non-zero
    if utc_dt.microsecond:
        return utc_dt.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
    return utc_dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def parse_rfc3339(value: str) -> datetime:
    if not value.endswith("Z"):
        raise ValueError("RFC 3339 timestamp must end with Z")
    dt = datetime.fromisoformat(value[:-1] + "+00:00")
    return dt.astimezone(timezone.utc)


def format_date(d: date) -> str:
    return d.isoformat()


def parse_date(value: str) -> date:
    return date.fromisoformat(value)


class ErrorCode(StrEnum):
    AUTHENTICATION_REQUIRED = "AUTHENTICATION_REQUIRED"
    IDENTITY_PROVIDER_NOT_ALLOWED = "IDENTITY_PROVIDER_NOT_ALLOWED"
    ROLE_MAPPING_FAILED = "ROLE_MAPPING_FAILED"
    FORBIDDEN = "FORBIDDEN"
    RESOURCE_NOT_FOUND = "RESOURCE_NOT_FOUND"
    VALIDATION_FAILED = "VALIDATION_FAILED"
    UNSUPPORTED_MEDIA_TYPE = "UNSUPPORTED_MEDIA_TYPE"
    PAYLOAD_TOO_LARGE = "PAYLOAD_TOO_LARGE"
    VERSION_CONFLICT = "VERSION_CONFLICT"
    INVALID_STATE_TRANSITION = "INVALID_STATE_TRANSITION"
    IDEMPOTENCY_KEY_REQUIRED = "IDEMPOTENCY_KEY_REQUIRED"
    IDEMPOTENCY_KEY_REUSED = "IDEMPOTENCY_KEY_REUSED"
    IDEMPOTENCY_IN_PROGRESS = "IDEMPOTENCY_IN_PROGRESS"
    ACTION_PREVIEW_EXPIRED = "ACTION_PREVIEW_EXPIRED"
    ACTION_PREVIEW_ALREADY_USED = "ACTION_PREVIEW_ALREADY_USED"
    ACTION_CONFIRMATION_INVALID = "ACTION_CONFIRMATION_INVALID"
    POLICY_DENIED = "POLICY_DENIED"
    ROOM_SLOT_UNAVAILABLE = "ROOM_SLOT_UNAVAILABLE"
    CITATION_UNRESOLVABLE = "CITATION_UNRESOLVABLE"
    RATE_LIMITED = "RATE_LIMITED"
    DEPENDENCY_UNAVAILABLE = "DEPENDENCY_UNAVAILABLE"
    INTEGRATION_NOT_ENABLED = "INTEGRATION_NOT_ENABLED"
    EVENT_PUBLISH_FAILED = "EVENT_PUBLISH_FAILED"
    INTERNAL_ERROR = "INTERNAL_ERROR"


@dataclass(frozen=True)
class FieldError:
    code: str
    pointer: str
    detail: str

    def to_dict(self) -> dict[str, str]:
        return {"code": self.code, "pointer": self.pointer, "detail": self.detail}


@dataclass(frozen=True)
class ProblemDetails:
    type: str
    title: str
    status: int
    detail: str
    instance: str
    code: ErrorCode
    request_id: str
    retryable: bool
    errors: list[FieldError] | None = None

    def __post_init__(self) -> None:
        if not (400 <= self.status <= 599):
            raise ValueError(f"HTTP status code must be between 400 and 599, got {self.status}")
        if not is_valid_uuid7(self.request_id):
            raise ValueError(f"request_id must be valid UUIDv7, got {self.request_id}")

    def to_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {
            "type": self.type,
            "title": self.title,
            "status": self.status,
            "detail": self.detail,
            "instance": self.instance,
            "code": str(self.code),
            "request_id": self.request_id,
            "retryable": self.retryable,
        }
        if self.errors is not None:
            data["errors"] = [e.to_dict() for e in self.errors]
        return data
