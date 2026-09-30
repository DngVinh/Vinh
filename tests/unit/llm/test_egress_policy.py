from __future__ import annotations

from pathlib import Path
import sys
import pytest

ROOT = Path(__file__).resolve().parents[3]
API_SRC = ROOT / "services" / "api" / "src"
if str(API_SRC) not in sys.path:
    sys.path.insert(0, str(API_SRC))

from campus247.infrastructure.llm.egress_policy import (
    EgressPolicy,
    EgressViolationError,
)
from campus247.infrastructure.llm.gateway import EgressGuardedLlmGateway, EgressProviderError


class FakeProvider:
    def __init__(self):
        self.dispatched_payloads: list[dict] = []

    async def generate(self, payload: dict) -> dict:
        self.dispatched_payloads.append(payload)
        return {"text": "Model answer", "model": "gemini-pro"}


class FailingProvider:
    async def generate(self, payload: dict) -> dict:
        raise RuntimeError("provider rejected secret sk-live-999988887777666655554444")


@pytest.fixture
def policy():
    return EgressPolicy()


@pytest.fixture
def guarded_gateway(policy):
    provider = FakeProvider()
    gateway = EgressGuardedLlmGateway(provider=provider, policy=policy)
    return gateway, provider


@pytest.mark.asyncio
async def test_egress_payload_minimized_to_approved_fields(guarded_gateway):
    """AC-TASK-AGENT-EGRESS-001-01: Provider payloads contain only fields required for approved purpose."""
    gateway, provider = guarded_gateway

    incoming_payload = {
        "purpose": "FAQ_ANSWERING",
        "messages": [{"role": "user", "content": "Lịch thi học kỳ khi nào có?"}],
        "temperature": 0.2,
        # Internal fields that MUST NOT leak to external provider
        "internal_user_id": "usr-123456",
        "session_id": "sess-secret-999",
        "ip_address": "192.168.1.50",
        "internal_debug_trace": {"hop": 1},
    }

    resp = await gateway.generate(incoming_payload)
    assert resp["text"] == "Model answer"

    assert len(provider.dispatched_payloads) == 1
    sent = provider.dispatched_payloads[0]

    # Approved inference fields present
    assert "messages" in sent
    assert "temperature" in sent

    # Leaked metadata fields stripped
    assert "internal_user_id" not in sent
    assert "session_id" not in sent
    assert "ip_address" not in sent
    assert "internal_debug_trace" not in sent


@pytest.mark.asyncio
async def test_denied_payload_reaches_no_provider(guarded_gateway):
    """AC-TASK-AGENT-EGRESS-001-02: A denied payload reaches no provider adapter and emits safe auditable reason."""
    gateway, provider = guarded_gateway

    secret_token = "sk-live-999988887777666655554444"
    toxic_payload = {
        "purpose": "FAQ_ANSWERING",
        "messages": [
            {"role": "user", "content": f"Here is my secret token: {secret_token}. What is it?"}
        ],
    }

    with pytest.raises(EgressViolationError) as exc_info:
        await gateway.generate(toxic_payload)

    # Provider MUST NOT have been called
    assert len(provider.dispatched_payloads) == 0

    # Safe auditable reason
    assert exc_info.value.safe_reason is not None
    assert "sensitive credential" in exc_info.value.safe_reason.lower() or "secret" in exc_info.value.safe_reason.lower()


def test_exception_never_contains_raw_prohibited_content(policy):
    """AC-TASK-AGENT-EGRESS-001-03: Logs, metrics, traces, and exceptions never contain raw prohibited content."""
    raw_secret = "ghp_111122223333444455556666777788889999"
    payload = {
        "purpose": "FAQ_ANSWERING",
        "messages": [{"role": "user", "content": f"Private token {raw_secret}"}],
    }

    with pytest.raises(EgressViolationError) as exc_info:
        policy.validate_and_minimize(payload)

    exc_str = str(exc_info.value)
    # The actual secret must NOT appear in the exception text
    assert raw_secret not in exc_str
    assert "ghp_" not in exc_str


@pytest.mark.asyncio
async def test_embedding_payload_uses_only_embedding_fields(guarded_gateway):
    """Embedding egress excludes conversation, memory, attachment, and routing metadata."""
    gateway, provider = guarded_gateway
    payload = {
        "purpose": "EMBEDDING",
        "input": ["Published library opening hours"],
        "model": "embedding-test",
        "dimensions": 256,
        "messages": [{"role": "user", "content": "must not be forwarded"}],
        "memory": [{"content": "old context"}],
        "attachments": [{"url": "https://internal.invalid/file"}],
        "provider": "caller-selected-provider",
        "region": "caller-selected-region",
    }

    await gateway.generate(payload)

    assert provider.dispatched_payloads == [
        {"input": ["Published library opening hours"], "model": "embedding-test", "dimensions": 256}
    ]


@pytest.mark.asyncio
async def test_message_attachments_are_dropped_but_text_is_preserved(guarded_gateway):
    gateway, provider = guarded_gateway
    await gateway.generate(
        {
            "purpose": "FAQ_ANSWERING",
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "What time does the library open?"},
                        {"type": "image_url", "image_url": {"url": "https://private.invalid/file"}},
                    ],
                }
            ],
        }
    )

    assert provider.dispatched_payloads[0] == {
        "messages": [
            {"role": "user", "content": [{"type": "text", "text": "What time does the library open?"}]}
        ]
    }


@pytest.mark.asyncio
async def test_direct_identifier_in_nested_memory_is_denied_before_provider(guarded_gateway):
    gateway, provider = guarded_gateway
    with pytest.raises(EgressViolationError) as exc_info:
        await gateway.generate(
            {
                "purpose": "FAQ_ANSWERING",
                "messages": [{"role": "user", "content": "Help with enrollment"}],
                "memory": [{"student_id": "SV123456"}],
            }
        )

    assert provider.dispatched_payloads == []
    assert "SV123456" not in str(exc_info.value)
    assert "personal" in exc_info.value.safe_reason.lower()


def test_unsupported_purpose_does_not_echo_caller_value(policy):
    caller_value = "PRIVATE_STUDENT_EXPORT_email@example.edu"
    with pytest.raises(EgressViolationError) as exc_info:
        policy.validate_and_minimize({"purpose": caller_value, "messages": []})

    assert caller_value not in str(exc_info.value)
    assert "example.edu" not in str(exc_info.value)


@pytest.mark.asyncio
async def test_policy_does_not_mutate_input_and_is_deterministic(policy):
    payload = {
        "purpose": "FAQ_ANSWERING",
        "messages": [{"role": "user", "content": "Explain the exam schedule"}],
        "temperature": 0.2,
        "memory": [{"content": "ignored"}],
    }
    original = {
        "purpose": "FAQ_ANSWERING",
        "messages": [{"role": "user", "content": "Explain the exam schedule"}],
        "temperature": 0.2,
        "memory": [{"content": "ignored"}],
    }

    first = policy.validate_and_minimize(payload)
    second = policy.validate_and_minimize(payload)

    assert payload == original
    assert first == second


@pytest.mark.asyncio
async def test_provider_failure_is_sanitized_and_has_no_raw_secret():
    gateway = EgressGuardedLlmGateway(provider=FailingProvider())
    with pytest.raises(EgressProviderError) as exc_info:
        await gateway.generate(
            {
                "purpose": "FAQ_ANSWERING",
                "messages": [{"role": "user", "content": "safe question"}],
            }
        )

    assert "sk-live-999988887777666655554444" not in str(exc_info.value)
    assert "secret" not in str(exc_info.value).lower()
