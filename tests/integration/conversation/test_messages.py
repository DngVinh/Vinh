from __future__ import annotations

from datetime import datetime, timezone, timedelta
from pathlib import Path
import sys
import pytest

ROOT = Path(__file__).resolve().parents[3]
API_SRC = ROOT / "services" / "api" / "src"
if str(API_SRC) not in sys.path:
    sys.path.insert(0, str(API_SRC))

from campus247.application.conversation.messages import (
    ConversationMessageService,
    ConversationRecord,
    ConversationStatus,
    MessageRecord,
    SenderType,
    ContentFormat,
)


@pytest.fixture
def service() -> ConversationMessageService:
    return ConversationMessageService()


@pytest.mark.asyncio
async def test_create_conversation_success(service: ConversationMessageService):
    owner_id = "01923456-789a-7def-8123-456789abcdef"
    conv = await service.create_conversation(owner_user_id=owner_id)

    assert conv.owner_user_id == owner_id
    assert conv.status == ConversationStatus.ACTIVE
    assert conv.channel == "WEB"
    assert conv.version == 1
    assert conv.last_message_at is None
    assert conv.retention_expires_at > datetime.now(timezone.utc) + timedelta(days=29)


@pytest.mark.asyncio
async def test_create_conversation_invalid_owner(service: ConversationMessageService):
    with pytest.raises(ValueError, match="owner_user_id must be a valid UUIDv7"):
        await service.create_conversation(owner_user_id="invalid-uuid")


@pytest.mark.asyncio
async def test_append_message_sequence_and_version(service: ConversationMessageService):
    owner_id = "01923456-789a-7def-8123-456789abcdef"
    conv = await service.create_conversation(owner_user_id=owner_id)

    msg1 = await service.append_message(
        conversation_id=conv.id,
        sender_type=SenderType.USER,
        content="Xin chào Campus 24/7",
        sender_user_id=owner_id,
    )
    assert msg1.sequence_no == 1
    assert msg1.sender_type == SenderType.USER
    assert msg1.content_redacted == "Xin chào Campus 24/7"

    updated_conv = await service.get_conversation(conv.id)
    assert updated_conv is not None
    assert updated_conv.version == 2
    assert updated_conv.last_message_at == msg1.created_at

    msg2 = await service.append_message(
        conversation_id=conv.id,
        sender_type=SenderType.ASSISTANT,
        content="Chào bạn! Tôi có thể giúp gì cho bạn hôm nay?",
    )
    assert msg2.sequence_no == 2
    assert msg2.sender_type == SenderType.ASSISTANT

    msgs = await service.list_messages(conv.id)
    assert len(msgs) == 2
    assert [m.sequence_no for m in msgs] == [1, 2]


@pytest.mark.asyncio
async def test_append_message_nonexistent_conversation(service: ConversationMessageService):
    with pytest.raises(ValueError, match="Conversation not found"):
        await service.append_message(
            conversation_id="01923456-789a-7def-8123-456789abcdef",
            sender_type=SenderType.USER,
            content="Hello",
        )


@pytest.mark.asyncio
async def test_append_message_empty_content(service: ConversationMessageService):
    owner_id = "01923456-789a-7def-8123-456789abcdef"
    conv = await service.create_conversation(owner_user_id=owner_id)

    with pytest.raises(ValueError, match="Message content cannot be empty"):
        await service.append_message(
            conversation_id=conv.id,
            sender_type=SenderType.USER,
            content="   ",
        )
