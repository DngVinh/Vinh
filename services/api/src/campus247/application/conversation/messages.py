from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime, timedelta, timezone
from enum import StrEnum
from typing import Protocol

from campus247.domain.shared.values import generate_uuid7, is_valid_uuid7


class ConversationStatus(StrEnum):
    ACTIVE = "ACTIVE"
    HANDED_OVER = "HANDED_OVER"
    CLOSED = "CLOSED"
    ARCHIVED = "ARCHIVED"


class SenderType(StrEnum):
    USER = "USER"
    ASSISTANT = "ASSISTANT"
    STAFF = "STAFF"
    SYSTEM = "SYSTEM"


class ContentFormat(StrEnum):
    PLAIN_TEXT = "PLAIN_TEXT"
    MARKDOWN_SAFE = "MARKDOWN_SAFE"


@dataclass(frozen=True)
class ConversationRecord:
    id: str
    owner_user_id: str
    status: ConversationStatus
    channel: str
    created_at: datetime
    updated_at: datetime
    retention_expires_at: datetime
    version: int = 1
    last_message_at: datetime | None = None


@dataclass(frozen=True)
class MessageRecord:
    id: str
    conversation_id: str
    sequence_no: int
    sender_type: SenderType
    content_redacted: str
    content_format: ContentFormat
    created_at: datetime
    sender_user_id: str | None = None
    citation_set_id: str | None = None
    redacted_at: datetime | None = None


class ConversationRepository(Protocol):
    async def save_conversation(self, conv: ConversationRecord) -> None:
        ...

    async def get_conversation(self, conv_id: str) -> ConversationRecord | None:
        ...

    async def save_message(self, msg: MessageRecord) -> None:
        ...

    async def list_messages(self, conv_id: str) -> list[MessageRecord]:
        ...

    async def get_next_sequence_no(self, conv_id: str) -> int:
        ...


class InMemoryConversationRepository:
    def __init__(self) -> None:
        self._conversations: dict[str, ConversationRecord] = {}
        self._messages: dict[str, list[MessageRecord]] = {}

    async def save_conversation(self, conv: ConversationRecord) -> None:
        self._conversations[conv.id] = conv
        if conv.id not in self._messages:
            self._messages[conv.id] = []

    async def get_conversation(self, conv_id: str) -> ConversationRecord | None:
        return self._conversations.get(conv_id)

    async def save_message(self, msg: MessageRecord) -> None:
        if msg.conversation_id not in self._messages:
            self._messages[msg.conversation_id] = []
        self._messages[msg.conversation_id].append(msg)

    async def list_messages(self, conv_id: str) -> list[MessageRecord]:
        return list(self._messages.get(conv_id, []))

    async def get_next_sequence_no(self, conv_id: str) -> int:
        msgs = self._messages.get(conv_id, [])
        if not msgs:
            return 1
        return max(m.sequence_no for m in msgs) + 1


class ConversationMessageService:
    def __init__(self, repository: ConversationRepository | None = None) -> None:
        self._repo = repository or InMemoryConversationRepository()

    async def create_conversation(
        self,
        owner_user_id: str,
        channel: str = "WEB",
        retention_days: int = 30,
    ) -> ConversationRecord:
        if not is_valid_uuid7(owner_user_id):
            raise ValueError(f"owner_user_id must be a valid UUIDv7 string, got: {owner_user_id}")
        if channel != "WEB":
            raise ValueError(f"Unsupported channel: {channel}")

        now = datetime.now(timezone.utc)
        record = ConversationRecord(
            id=generate_uuid7(),
            owner_user_id=owner_user_id,
            status=ConversationStatus.ACTIVE,
            channel=channel,
            created_at=now,
            updated_at=now,
            retention_expires_at=now + timedelta(days=retention_days),
            version=1,
            last_message_at=None,
        )
        await self._repo.save_conversation(record)
        return record

    async def append_message(
        self,
        conversation_id: str,
        sender_type: SenderType | str,
        content: str,
        sender_user_id: str | None = None,
        content_format: ContentFormat | str = ContentFormat.MARKDOWN_SAFE,
        citation_set_id: str | None = None,
    ) -> MessageRecord:
        conv = await self._repo.get_conversation(conversation_id)
        if not conv:
            raise ValueError(f"Conversation not found: {conversation_id}")

        if conv.status in (ConversationStatus.CLOSED, ConversationStatus.ARCHIVED):
            raise ValueError(f"Cannot append message to {conv.status} conversation")

        if not content or not content.strip():
            raise ValueError("Message content cannot be empty")

        now = datetime.now(timezone.utc)
        seq_no = await self._repo.get_next_sequence_no(conversation_id)
        stype = SenderType(sender_type)
        cformat = ContentFormat(content_format)

        msg = MessageRecord(
            id=generate_uuid7(),
            conversation_id=conversation_id,
            sequence_no=seq_no,
            sender_type=stype,
            content_redacted=content,
            content_format=cformat,
            created_at=now,
            sender_user_id=sender_user_id,
            citation_set_id=citation_set_id,
        )
        await self._repo.save_message(msg)

        updated_conv = replace(
            conv,
            last_message_at=now,
            updated_at=now,
            version=conv.version + 1,
        )
        await self._repo.save_conversation(updated_conv)
        return msg

    async def get_conversation(self, conversation_id: str) -> ConversationRecord | None:
        return await self._repo.get_conversation(conversation_id)

    async def list_messages(self, conversation_id: str) -> list[MessageRecord]:
        return await self._repo.list_messages(conversation_id)
