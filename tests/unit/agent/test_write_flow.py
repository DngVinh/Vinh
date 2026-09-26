from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
import sys
import pytest

ROOT = Path(__file__).resolve().parents[3]
API_SRC = ROOT / "services" / "api" / "src"
if str(API_SRC) not in sys.path:
    sys.path.insert(0, str(API_SRC))

from campus247.agent.state import ToolPhase
from campus247.agent.tools.write_flow import WriteToolFlowBroker
from campus247.domain.shared.values import generate_uuid7


def test_build_preview_and_interrupt() -> None:
    broker = WriteToolFlowBroker()
    actor_id = generate_uuid7()

    args = {"category": "ACADEMIC", "title": "Phúc khảo điểm thi"}
    preview = broker.build_preview(actor_id=actor_id, tool_id="TOOL-TICKET-001", arguments=args)

    assert preview.action_type == "TOOL-TICKET-001"
    assert preview.actor_user_id == actor_id

    interrupt = broker.create_confirmation_interrupt(preview)
    assert interrupt["phase"] == ToolPhase.AWAITING_CONFIRMATION
    assert interrupt["preview_id"] == preview.id
    assert interrupt["expires_at"] is not None


def test_revalidate_confirmation_success() -> None:
    broker = WriteToolFlowBroker()
    actor_id = generate_uuid7()
    args = {"category": "ACADEMIC", "title": "Phúc khảo điểm thi"}
    preview = broker.build_preview(actor_id=actor_id, tool_id="TOOL-TICKET-001", arguments=args)

    now = datetime.now(timezone.utc)
    is_valid = broker.revalidate(preview, arguments=args, at_time=now)
    assert is_valid is True


def test_revalidate_confirmation_tampered_payload_fails() -> None:
    broker = WriteToolFlowBroker()
    actor_id = generate_uuid7()
    args = {"category": "ACADEMIC", "title": "Phúc khảo"}
    preview = broker.build_preview(actor_id=actor_id, tool_id="TOOL-TICKET-001", arguments=args)

    tampered = {"category": "ACADEMIC", "title": "Hacker title"}
    now = datetime.now(timezone.utc)
    is_valid = broker.revalidate(preview, arguments=tampered, at_time=now)
    assert is_valid is False


def test_revalidate_confirmation_expired_fails() -> None:
    broker = WriteToolFlowBroker()
    actor_id = generate_uuid7()
    args = {"category": "ACADEMIC", "title": "Phúc khảo"}
    preview = broker.build_preview(actor_id=actor_id, tool_id="TOOL-TICKET-001", arguments=args)

    expired_time = datetime.now(timezone.utc) + timedelta(hours=1)
    is_valid = broker.revalidate(preview, arguments=args, at_time=expired_time)
    assert is_valid is False
