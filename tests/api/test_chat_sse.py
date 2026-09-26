from __future__ import annotations

import json
from pathlib import Path
import sys
from fastapi import FastAPI
from fastapi.testclient import TestClient
import pytest

ROOT = Path(__file__).resolve().parents[2]
API_SRC = ROOT / "services" / "api" / "src"
SYNTH_SRC = ROOT / "packages" / "synthetic" / "src"
if str(API_SRC) not in sys.path:
    sys.path.insert(0, str(API_SRC))
if str(SYNTH_SRC) not in sys.path:
    sys.path.insert(0, str(SYNTH_SRC))

from campus247.application.conversation.messages import ConversationMessageService
from campus247.infrastructure.identity.mock import SyntheticIdentityAdapter
from campus247.presentation.chat import create_chat_router
from campus247.presentation.identity import IdentityMiddleware


@pytest.fixture
def setup_app():
    app = FastAPI()
    identity_adapter = SyntheticIdentityAdapter(secret_key="secret-test-key-247")
    app.add_middleware(IdentityMiddleware, adapter=identity_adapter)

    conv_service = ConversationMessageService()
    chat_router = create_chat_router(conv_service)
    app.include_router(chat_router)

    client = TestClient(app)
    return client, identity_adapter, conv_service


def test_chat_sse_unauthenticated(setup_app):
    client, _, _ = setup_app
    resp = client.post(
        "/v1/conversations/01923456-789a-7def-8123-456789abcdef/messages:stream",
        json={"content": "Xin chào"},
    )
    assert resp.status_code == 401


def test_chat_sse_conversation_not_found(setup_app):
    client, identity_adapter, _ = setup_app
    student_id = "4b419a1b-6d41-7dfb-8943-2edd9f071385"
    token = identity_adapter.mint_token(student_id)

    resp = client.post(
        "/v1/conversations/01923456-789a-7def-8123-456789abcdef/messages:stream",
        headers={"Authorization": f"Bearer {token}"},
        json={"content": "Xin chào"},
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_chat_sse_conversation_forbidden(setup_app):
    client, identity_adapter, conv_service = setup_app
    student_1 = "4b419a1b-6d41-7dfb-8943-2edd9f071385"
    student_2 = "97c5ab40-6399-7ad3-9838-eab50f267b2d"

    conv = await conv_service.create_conversation(owner_user_id=student_1)
    token_2 = identity_adapter.mint_token(student_2)

    resp = client.post(
        f"/v1/conversations/{conv.id}/messages:stream",
        headers={"Authorization": f"Bearer {token_2}"},
        json={"content": "Xin chào"},
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_chat_sse_streaming_success(setup_app):
    client, identity_adapter, conv_service = setup_app
    student_id = "4b419a1b-6d41-7dfb-8943-2edd9f071385"
    token = identity_adapter.mint_token(student_id)

    conv = await conv_service.create_conversation(owner_user_id=student_id)

    resp = client.post(
        f"/v1/conversations/{conv.id}/messages:stream",
        headers={"Authorization": f"Bearer {token}"},
        json={"content": "Lịch học của tôi tuần này?"},
    )
    assert resp.status_code == 200
    assert "text/event-stream" in resp.headers.get("content-type", "")

    body = resp.text
    assert "event: message.started" in body
    assert "event: message.delta" in body
    assert "event: message.completed" in body

    # Verify conversation stored both user and assistant messages
    msgs = await conv_service.list_messages(conv.id)
    assert len(msgs) == 2
    assert msgs[0].sender_type == "USER"
    assert msgs[1].sender_type == "ASSISTANT"


@pytest.mark.asyncio
async def test_chat_sse_with_agent_workflow():
    from campus247.agent.graph import CampusAgentWorkflow

    app = FastAPI()
    identity_adapter = SyntheticIdentityAdapter(secret_key="secret-test-key-247")
    app.add_middleware(IdentityMiddleware, adapter=identity_adapter)

    conv_service = ConversationMessageService()
    workflow = CampusAgentWorkflow()
    chat_router = create_chat_router(conv_service, agent_runner=workflow)
    app.include_router(chat_router)

    client = TestClient(app)
    student_id = "4b419a1b-6d41-7dfb-8943-2edd9f071385"
    token = identity_adapter.mint_token(student_id)

    conv = await conv_service.create_conversation(owner_user_id=student_id)
    resp = client.post(
        f"/v1/conversations/{conv.id}/messages:stream",
        headers={"Authorization": f"Bearer {token}"},
        json={"content": "Thời khóa biểu tuần này của tôi?"},
    )
    assert resp.status_code == 200
    assert "event: message.started" in resp.text
    assert "event: message.delta" in resp.text
    assert "event: message.completed" in resp.text

    msgs = await conv_service.list_messages(conv.id)
    assert len(msgs) == 2
    assert "Thời khóa biểu" in msgs[1].content_redacted

