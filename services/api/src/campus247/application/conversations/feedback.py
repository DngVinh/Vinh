from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import StrEnum

from campus247.application.conversation.messages import ConversationMessageService
from campus247.domain.shared.values import generate_uuid7


class FeedbackRating(StrEnum):
    HELPFUL = "HELPFUL"
    NOT_HELPFUL = "NOT_HELPFUL"


class FeedbackStorageError(Exception):
    pass


@dataclass(frozen=True)
class AnswerFeedbackReference:
    answer_id: str
    source_document_version_ids: list[str]
    model_version: str
    prompt_version: str


@dataclass(frozen=True)
class AnswerFeedbackReceipt:
    id: str
    conversation_id: str
    rating: FeedbackRating
    comment_recorded: bool
    answer_reference: AnswerFeedbackReference
    recorded_at: datetime


class FeedbackService:
    def __init__(self, conv_service: ConversationMessageService) -> None:
        self._conv_service = conv_service
        self._feedbacks: dict[str, AnswerFeedbackReceipt] = {}
        self.simulate_storage_failure = False

    async def record_feedback(
        self,
        actor_id: str,
        conversation_id: str,
        message_id: str,
        rating: FeedbackRating | str,
        comment: str | None = None,
    ) -> AnswerFeedbackReceipt:
        conv = await self._conv_service.get_conversation(conversation_id)
        if not conv:
            raise KeyError("Conversation not found")

        if conv.owner_user_id != actor_id:
            raise PermissionError("Forbidden: not conversation owner")

        messages = await self._conv_service.list_messages(conversation_id)
        target_msg = next((m for m in messages if m.id == message_id), None)
        if not target_msg:
            raise KeyError("Message not found")

        if self.simulate_storage_failure:
            raise FeedbackStorageError("Storage subsystem temporarily unavailable")

        receipt_id = generate_uuid7()
        now = datetime.now(timezone.utc)
        frating = FeedbackRating(rating)

        receipt = AnswerFeedbackReceipt(
            id=receipt_id,
            conversation_id=conversation_id,
            rating=frating,
            comment_recorded=bool(comment and comment.strip()),
            answer_reference=AnswerFeedbackReference(
                answer_id=message_id,
                source_document_version_ids=[],
                model_version="provider-fake-llm-v1",
                prompt_version="campus247-chat-system-v1",
            ),
            recorded_at=now,
        )

        self._feedbacks[receipt_id] = receipt
        return receipt
