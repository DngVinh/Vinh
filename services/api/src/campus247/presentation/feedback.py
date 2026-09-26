from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field
from starlette.responses import JSONResponse

from campus247.application.conversations.feedback import (
    FeedbackRating,
    FeedbackService,
    FeedbackStorageError,
)
from campus247.presentation.identity import get_current_identity


class CreateAnswerFeedbackPayload(BaseModel):
    rating: FeedbackRating
    comment: str | None = Field(default=None, min_length=1, max_length=2000)


def create_feedback_router(feedback_service: FeedbackService) -> APIRouter:
    router = APIRouter(tags=["Feedback"])

    @router.post("/v1/conversations/{conversation_id}/messages/{message_id}/feedback")
    async def create_answer_feedback(
        conversation_id: str,
        message_id: str,
        payload: CreateAnswerFeedbackPayload,
        request: Request,
    ) -> JSONResponse:
        identity = get_current_identity(request)

        try:
            receipt = await feedback_service.record_feedback(
                actor_id=identity.subject_id,
                conversation_id=conversation_id,
                message_id=message_id,
                rating=payload.rating,
                comment=payload.comment,
            )
        except KeyError as e:
            raise HTTPException(status_code=404, detail=str(e))
        except PermissionError as e:
            raise HTTPException(status_code=403, detail=str(e))
        except FeedbackStorageError as e:
            raise HTTPException(status_code=503, detail=str(e))

        content = {
            "id": receipt.id,
            "conversation_id": receipt.conversation_id,
            "rating": receipt.rating.value,
            "comment_recorded": receipt.comment_recorded,
            "answer_reference": {
                "answer_id": receipt.answer_reference.answer_id,
                "source_document_version_ids": receipt.answer_reference.source_document_version_ids,
                "model_version": receipt.answer_reference.model_version,
                "prompt_version": receipt.answer_reference.prompt_version,
            },
            "recorded_at": receipt.recorded_at.isoformat(),
        }

        location = f"/v1/conversations/{conversation_id}/messages/{message_id}/feedback/{receipt.id}"
        return JSONResponse(
            status_code=201,
            content=content,
            headers={
                "Location": location,
                "Cache-Control": "no-store",
            },
        )

    return router
