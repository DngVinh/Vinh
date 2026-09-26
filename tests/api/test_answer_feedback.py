from __future__ import annotations

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

from campus247.application.conversation.messages import ConversationMessageService, SenderType
from campus247.application.conversations.feedback import FeedbackService, FeedbackStorageError
from campus247.infrastructure.identity.mock import SyntheticIdentityAdapter
from campus247.presentation.feedback import create_feedback_router
from campus247.presentation.identity import IdentityMiddleware


@pytest.fixture
def setup_env():
    app = FastAPI()
    identity_adapter = SyntheticIdentityAdapter(secret_key="secret-test-key-247")
    app.add_middleware(IdentityMiddleware, adapter=identity_adapter)

    conv_service = ConversationMessageService()
    feedback_service = FeedbackService(conv_service=conv_service)
    feedback_router = create_feedback_router(feedback_service)
    app.include_router(feedback_router)

    client = TestClient(app)
    return client, identity_adapter, conv_service, feedback_service


def test_feedback_unauthenticated(setup_env):
    client, _, _, _ = setup_env
    resp = client.post(
        "/v1/conversations/01923456-789a-7def-8123-456789abcdef/messages/01923456-789a-7def-8123-456789abcde0/feedback",
        json={"rating": "HELPFUL"},
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_feedback_conversation_not_found(setup_env):
    client, identity_adapter, _, _ = setup_env
    student_id = "4b419a1b-6d41-7dfb-8943-2edd9f071385"
    token = identity_adapter.mint_token(student_id)

    resp = client.post(
        "/v1/conversations/01923456-789a-7def-8123-456789abcdef/messages/01923456-789a-7def-8123-456789abcde0/feedback",
        headers={"Authorization": f"Bearer {token}"},
        json={"rating": "HELPFUL"},
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_feedback_forbidden_not_owner(setup_env):
    client, identity_adapter, conv_service, _ = setup_env
    student_1 = "4b419a1b-6d41-7dfb-8943-2edd9f071385"
    student_2 = "97c5ab40-6399-7ad3-9838-eab50f267b2d"

    conv = await conv_service.create_conversation(owner_user_id=student_1)
    msg = await conv_service.append_message(
        conversation_id=conv.id,
        sender_type=SenderType.ASSISTANT,
        content="Trả lời demo",
    )

    token_2 = identity_adapter.mint_token(student_2)
    resp = client.post(
        f"/v1/conversations/{conv.id}/messages/{msg.id}/feedback",
        headers={"Authorization": f"Bearer {token_2}"},
        json={"rating": "HELPFUL"},
    )
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_feedback_success(setup_env):
    client, identity_adapter, conv_service, _ = setup_env
    student_id = "4b419a1b-6d41-7dfb-8943-2edd9f071385"
    token = identity_adapter.mint_token(student_id)

    conv = await conv_service.create_conversation(owner_user_id=student_id)
    msg = await conv_service.append_message(
        conversation_id=conv.id,
        sender_type=SenderType.ASSISTANT,
        content="Nội dung tư vấn",
    )

    resp = client.post(
        f"/v1/conversations/{conv.id}/messages/{msg.id}/feedback",
        headers={"Authorization": f"Bearer {token}"},
        json={"rating": "HELPFUL", "comment": "Giải thích rất rõ ràng"},
    )
    assert resp.status_code == 201
    assert resp.headers.get("cache-control") == "no-store"
    assert "location" in resp.headers

    data = resp.json()
    assert data["conversation_id"] == conv.id
    assert data["rating"] == "HELPFUL"
    assert data["comment_recorded"] is True
    assert "answer_reference" in data
    assert data["answer_reference"]["answer_id"] == msg.id
    assert "model_version" in data["answer_reference"]
    assert "prompt_version" in data["answer_reference"]


@pytest.mark.asyncio
async def test_feedback_storage_failure_does_not_mutate_conversation(setup_env):
    client, identity_adapter, conv_service, feedback_service = setup_env
    student_id = "4b419a1b-6d41-7dfb-8943-2edd9f071385"
    token = identity_adapter.mint_token(student_id)

    conv = await conv_service.create_conversation(owner_user_id=student_id)
    msg = await conv_service.append_message(
        conversation_id=conv.id,
        sender_type=SenderType.ASSISTANT,
        content="Trả lời",
    )

    # Simulate storage failure
    feedback_service.simulate_storage_failure = True

    resp = client.post(
        f"/v1/conversations/{conv.id}/messages/{msg.id}/feedback",
        headers={"Authorization": f"Bearer {token}"},
        json={"rating": "NOT_HELPFUL"},
    )
    assert resp.status_code == 503

    # Conversation messages remain intact
    msgs = await conv_service.list_messages(conv.id)
    assert len(msgs) == 1
    assert msgs[0].id == msg.id
