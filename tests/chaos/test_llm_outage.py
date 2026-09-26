import pytest
from unittest.mock import AsyncMock
from campus247.application.ai.gateway import GatewayPolicyExecutor, ProviderError, GatewayTimeoutError


class MockFailingGateway:
    async def complete(self, *args, **kwargs):
        raise ProviderError("Upstream LLM provider 503 Service Unavailable (Outage simulated)")


class ResilientAgentService:
    def __init__(self, primary_gateway):
        self.primary_gateway = primary_gateway
        self.canned_fallback = (
            "Hệ thống trợ lý AI đang tạm thời gián đoạn kết nối tới nhà cung cấp mô hình. "
            "Vui lòng thử lại sau ít phút hoặc liên hệ trực tiếp Phòng Đào tạo HUCE qua hotline (024) 3869 1302."
        )

    async def answer_query(self, query: str):
        try:
            res = await self.primary_gateway.complete(query)
            return {"answer": res, "fallback": False}
        except (ProviderError, GatewayTimeoutError, Exception):
            # Graceful fallback on LLM provider outage
            return {
                "answer": self.canned_fallback,
                "fallback": True,
                "provider_status": "OUTAGE",
                "handover_recommended": True,
            }


@pytest.mark.asyncio
async def test_llm_outage_activates_graceful_fallback():
    # AC-01: LLM outage triggers polite fallback and hotline recommendation without crashing
    failing_gateway = MockFailingGateway()
    service = ResilientAgentService(primary_gateway=failing_gateway)

    result = await service.answer_query("Học phí kỳ này đóng khi nào?")
    assert result["fallback"] is True
    assert result["provider_status"] == "OUTAGE"
    assert result["handover_recommended"] is True
    assert "hotline" in result["answer"].lower()
    assert "gián đoạn" in result["answer"].lower()


@pytest.mark.asyncio
async def test_llm_healthy_provider_returns_normal_answer():
    # AC-02: Normal provider works as expected
    mock_gateway = AsyncMock()
    mock_gateway.complete.return_value = "Học phí học kỳ 1 đóng trước ngày 30/10."
    service = ResilientAgentService(primary_gateway=mock_gateway)

    result = await service.answer_query("Học phí kỳ này đóng khi nào?")
    assert result["fallback"] is False
    assert "30/10" in result["answer"]
