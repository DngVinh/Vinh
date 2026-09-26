from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
import sys
import pytest

ROOT = Path(__file__).resolve().parents[3]
API_SRC = ROOT / "services" / "api" / "src"
if str(API_SRC) not in sys.path:
    sys.path.insert(0, str(API_SRC))

from campus247.domain.action.preview import ActionPreviewValue, create_action_preview
from campus247.domain.shared.values import generate_uuid7


def test_create_action_preview_success():
    actor_id = generate_uuid7()
    payload = {"room_id": "ROOM-101", "slot": "MORNING"}

    preview = create_action_preview(
        actor_user_id=actor_id,
        action_type="room.booking.create",
        payload=payload,
        ttl_seconds=300,
    )

    assert preview.actor_user_id == actor_id
    assert preview.action_type == "room.booking.create"
    assert preview.payload_hash != ""
    assert preview.is_expired(datetime.now(timezone.utc)) is False
    assert preview.is_active(datetime.now(timezone.utc)) is True


def test_action_preview_immutable():
    actor_id = generate_uuid7()
    preview = create_action_preview(
        actor_user_id=actor_id,
        action_type="room.booking.create",
        payload={"ticket_id": "T-1"},
    )
    with pytest.raises(Exception):
        preview.action_type = "something_else"  # type: ignore[misc]


def test_action_preview_expiry():
    actor_id = generate_uuid7()
    preview = create_action_preview(
        actor_user_id=actor_id,
        action_type="ticket.create",
        payload={"title": "Help"},
        ttl_seconds=10,
    )

    future_time = preview.expires_at + timedelta(seconds=1)
    assert preview.is_expired(future_time) is True
    assert preview.is_active(future_time) is False


def test_action_preview_payload_hash_tamper_detected():
    actor_id = generate_uuid7()
    preview = create_action_preview(
        actor_user_id=actor_id,
        action_type="ticket.create",
        payload={"title": "Help"},
    )

    with pytest.raises(ValueError, match="payload_hash"):
        ActionPreviewValue(
            id=preview.id,
            actor_user_id=preview.actor_user_id,
            action_type=preview.action_type,
            normalized_payload=preview.normalized_payload,
            payload_hash="invalid_hash_value",
            policy_decision=preview.policy_decision,
            confirmation_secret_hash=preview.confirmation_secret_hash,
            created_at=preview.created_at,
            expires_at=preview.expires_at,
        )
