from __future__ import annotations

import asyncio
import json
import re
from typing import Any, AsyncGenerator
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field
from starlette.responses import JSONResponse, StreamingResponse

from campus247.agent.state import NormalizedTurn
from campus247.application.conversation.messages import (
    ConversationMessageService,
    SenderType,
)
from campus247.domain.shared.values import generate_uuid7
from campus247.presentation.identity import get_current_identity


class CreateMessagePayload(BaseModel):
    content: str = Field(..., min_length=1, max_length=10000)


def create_chat_router(
    conv_service: ConversationMessageService,
    agent_runner: Any | None = None,
) -> APIRouter:
    router = APIRouter(tags=["Conversations"])

    @router.post("/v1/conversations")
    async def create_conversation_endpoint(request: Request) -> JSONResponse:
        identity = get_current_identity(request)
        conv = await conv_service.create_conversation(owner_user_id=identity.subject_id)
        return JSONResponse(
            status_code=201,
            content={
                "id": conv.id,
                "owner_user_id": conv.owner_user_id,
                "status": str(conv.status),
                "created_at": conv.created_at.isoformat(),
            },
        )

    @router.post("/v1/conversations/{conversation_id}/messages:stream")
    async def stream_message(
        conversation_id: str,
        payload: CreateMessagePayload,
        request: Request,
    ) -> StreamingResponse:
        identity = get_current_identity(request)

        conv = await conv_service.get_conversation(conversation_id)
        if not conv:
            raise HTTPException(status_code=404, detail="Conversation not found")

        if conv.owner_user_id != identity.subject_id:
            raise HTTPException(
                status_code=403, detail="Forbidden: conversation ownership required"
            )

        # 1. Save user message
        await conv_service.append_message(
            conversation_id=conversation_id,
            sender_type=SenderType.USER,
            content=payload.content,
            sender_user_id=identity.subject_id,
        )

        async def event_generator() -> AsyncGenerator[str, None]:
            assistant_msg_id = generate_uuid7()
            full_text = ""
            state: Any | None = None

            try:
                # Event 1: message.started
                start_data = json.dumps(
                    {
                        "conversation_id": conversation_id,
                        "message_id": assistant_msg_id,
                    }
                )
                yield f"id: {generate_uuid7()}\nevent: message.started\ndata: {start_data}\n\n"

                # Generate answer using agent workflow if available
                if agent_runner is not None:
                    turn = NormalizedTurn(
                        session_id=conversation_id,
                        turn_id=str(generate_uuid7()),
                        user_id=identity.subject_id,
                        query=payload.content,
                    )
                    state = agent_runner.run(turn)
                    answer_text = (
                        state.draft.text
                        if state.draft
                        else f"Campus 24/7 đã nhận được yêu cầu: {payload.content}"
                    )
                else:
                    answer_text = f"Xin chào! Campus 24/7 đã nhận được yêu cầu: {payload.content}"

                # Split words into streamable chunks
                words = re.findall(r"\S+|\s+", answer_text)
                chunk_buffer = []
                for w in words:
                    chunk_buffer.append(w)
                    if len(chunk_buffer) >= 3 or "\n" in w:
                        delta = "".join(chunk_buffer)
                        chunk_buffer = []
                        full_text += delta

                        if await request.is_disconnected():
                            return

                        delta_data = json.dumps({"delta": delta})
                        yield f"id: {generate_uuid7()}\nevent: message.delta\ndata: {delta_data}\n\n"
                        await asyncio.sleep(0.01)

                if chunk_buffer:
                    delta = "".join(chunk_buffer)
                    full_text += delta
                    if not await request.is_disconnected():
                        delta_data = json.dumps({"delta": delta})
                        yield f"id: {generate_uuid7()}\nevent: message.delta\ndata: {delta_data}\n\n"

                # Save completed assistant message
                saved_assistant = await conv_service.append_message(
                    conversation_id=conversation_id,
                    sender_type=SenderType.ASSISTANT,
                    content=full_text or answer_text,
                )

                citations_payload = []
                if state is not None and isinstance(getattr(state, "tool_flow", None), dict):
                    candidates = state.tool_flow.get("candidates", [])
                    for idx, c in enumerate(candidates[:5]):
                        citations_payload.append(
                            {
                                "id": f"cit-{idx + 1}",
                                "title": c.get("section_path") or c.get("title") or f"Tài liệu HUCE #{idx + 1}",
                                "document_ref": c.get("document_version_id") or c.get("chunk_id", f"DOC-{idx + 1}"),
                                "quote": c.get("content_text", ""),
                                "confidence": round(float(c.get("score", 0.95)), 4),
                            }
                        )

                # Event 3: message.completed
                complete_data = json.dumps(
                    {
                        "message_id": saved_assistant.id,
                        "conversation_id": conversation_id,
                        "status": "completed",
                        "citations": citations_payload,
                    }
                )
                yield f"id: {generate_uuid7()}\nevent: message.completed\ndata: {complete_data}\n\n"

            except asyncio.CancelledError:
                # Client disconnected mid-stream
                if full_text:
                    await conv_service.append_message(
                        conversation_id=conversation_id,
                        sender_type=SenderType.ASSISTANT,
                        content=full_text,
                    )
            except Exception as err:
                err_data = json.dumps({"error": str(err)})
                yield f"id: {generate_uuid7()}\nevent: message.error\ndata: {err_data}\n\n"

        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-store",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )

    return router
