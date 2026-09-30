from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
import sys
import pytest

ROOT = Path(__file__).resolve().parents[3]
API_SRC = ROOT / "services" / "api" / "src"
if str(API_SRC) not in sys.path:
    sys.path.insert(0, str(API_SRC))

from campus247.domain.action.confirmation import (
    ConfirmationTokenService,
    ConfirmationValidationResult,
)
from campus247.domain.action.preview import create_action_preview
from campus247.domain.shared.values import generate_uuid7


def test_mint_and_validate_confirmation_token():
    service = ConfirmationTokenService(signing_key="confirmation-secret-key-32-chars!!")
    actor_id = generate_uuid7()
    preview = create_action_preview(actor_id, "ticket.create", {"title": "Doc Request"})

    token = service.mint_token(preview)
    assert isinstance(token, str)
    assert len(token) > 20

    res = service.validate_token(
        token=token,
        expected_preview_id=preview.id,
        expected_actor_id=actor_id,
        expected_session_id="none",
        expected_conversation_id="none",
        expected_action_type="ticket.create",
        expected_tool_version="1.0",
        expected_policy_version="1.0",
        expected_payload_hash=preview.payload_hash,
    )
    assert res.is_valid is True
    assert res.preview_id == preview.id
    assert res.actor_user_id == actor_id


def test_reject_tampered_confirmation_token():
    service = ConfirmationTokenService(signing_key="confirmation-secret-key-32-chars!!")
    actor_id = generate_uuid7()
    preview = create_action_preview(actor_id, "ticket.create", {"title": "Doc Request"})
    token = service.mint_token(preview)
    tampered_token = token[:-4] + "abcd"

    res = service.validate_token(
        token=tampered_token,
        expected_preview_id=preview.id,
        expected_actor_id=actor_id,
        expected_session_id="none",
        expected_conversation_id="none",
        expected_action_type="ticket.create",
        expected_tool_version="1.0",
        expected_policy_version="1.0",
        expected_payload_hash=preview.payload_hash,
    )
    assert res.is_valid is False
    assert "SIGNATURE_INVALID" in res.error_code


def test_reject_expired_confirmation_token():
    service = ConfirmationTokenService(signing_key="confirmation-secret-key-32-chars!!")
    actor_id = generate_uuid7()
    # TTL 1 second
    preview = create_action_preview(actor_id, "ticket.create", {"title": "Doc Request"}, ttl_seconds=1)
    token = service.mint_token(preview)

    future_time = datetime.now(timezone.utc) + timedelta(seconds=10)
    res = service.validate_token(
        token=token,
        expected_preview_id=preview.id,
        expected_actor_id=actor_id,
        expected_session_id="none",
        expected_conversation_id="none",
        expected_action_type="ticket.create",
        expected_tool_version="1.0",
        expected_policy_version="1.0",
        expected_payload_hash=preview.payload_hash,
        at_time=future_time,
    )
    assert res.is_valid is False
    assert "EXPIRED" in res.error_code


def test_reject_actor_or_payload_mismatch():
    service = ConfirmationTokenService(signing_key="confirmation-secret-key-32-chars!!")
    actor_id = generate_uuid7()
    wrong_actor_id = generate_uuid7()
    preview = create_action_preview(actor_id, "ticket.create", {"title": "Doc Request"})
    token = service.mint_token(preview)

    res = service.validate_token(
        token=token,
        expected_preview_id=preview.id,
        expected_actor_id=wrong_actor_id,
        expected_session_id="none",
        expected_conversation_id="none",
        expected_action_type="ticket.create",
        expected_tool_version="1.0",
        expected_policy_version="1.0",
        expected_payload_hash=preview.payload_hash,
    )
    assert res.is_valid is False
    assert "ACTOR_MISMATCH" in res.error_code
