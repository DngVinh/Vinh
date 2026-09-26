from __future__ import annotations

from collections.abc import AsyncIterator
from pathlib import Path
from typing import Any
import yaml

from campus247.ports.llm import (
    FinishReason,
    LlmEvent,
    LlmEventType,
    LlmGateway,
    LlmRequest,
    LlmResponse,
    LlmResponseStatus,
    ModelCapabilities,
    TokenUsage,
    ToolCandidate,
)


import hashlib
import json


def compute_fixture_key(route_id: str, prompt_version: str = "1.0.0", normalized_input: str = "") -> str:
    """Computes deterministic fixture key from hash(route_id, prompt_version, normalized_input)."""
    raw = f"{route_id}:{prompt_version}:{normalized_input.strip()}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


class DeterministicFakeProvider(LlmGateway):
    """Deterministic offline fake LLM provider loaded from static fixtures."""

    def __init__(self, fixtures: dict[str, Any]) -> None:
        self._fixtures = fixtures
        self._recorded_requests: list[LlmRequest] = []

    @classmethod
    def default(cls) -> DeterministicFakeProvider:
        """Creates default provider attempting to load evals fixtures or using empty dict."""
        for candidate in [
            Path(__file__).resolve().parents[5] / "packages" / "evals" / "fixtures" / "llm.yaml",
            Path("packages/evals/fixtures/llm.yaml"),
        ]:
            if candidate.is_file():
                return cls.from_yaml(candidate)
        return cls(fixtures={})

    @classmethod
    def from_yaml(cls, fixture_path: Path | str) -> DeterministicFakeProvider:
        path = Path(fixture_path)
        with path.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        fixtures = data.get("fixtures", {}) if isinstance(data, dict) else {}
        return cls(fixtures=fixtures)

    @property
    def recorded_requests(self) -> list[LlmRequest]:
        return list(self._recorded_requests)

    def _extract_query_text(self, request: LlmRequest) -> str:
        texts = []
        for item in request.input_items:
            if isinstance(item, dict):
                content = item.get("content") or item.get("user_query") or item.get("query")
                if content:
                    texts.append(str(content))
        if texts:
            return " ".join(texts)
        if request.system_instructions:
            return request.system_instructions
        return ""

    def _synthesize_deterministic_fixture(self, request: LlmRequest) -> dict[str, Any] | None:
        route_id = request.route_id.lower()
        query = self._extract_query_text(request).lower()

        if not query.strip():
            return None

        # 1. Safety classifier
        if any(kw in route_id for kw in ["safety", "sensitive_classifier"]) or "ai-prompt-safety-001" in route_id or "safetydecision" in request.system_instructions.lower():
            if any(kw in query for kw in ["tự tử", "tự sát", "muốn chết", "cắt cổ tay", "nhảy lầu", "uống thuốc ngủ", "kết liễu", "khong muon song", "chẳng thiết sống", "chẳng muốn sống", "nhảy từ tầng thượng", "chẳng còn mặt mũi"]):
                data = {"severity": "critical", "is_crisis": True, "reason": "self_harm_imminent"}
            elif any(kw in query for kw in ["đâm chết", "giết người", "mang súng", "đặt bom", "đốt trường", "đập nó", "chém", "vác dao", "xử đẹp"]):
                data = {"severity": "critical", "is_crisis": True, "reason": "violence_imminent"}
            elif any(kw in query for kw in ["ngất xỉu", "co giật", "khó thở", "đột quỵ", "ngừng tim"]):
                data = {"severity": "critical", "is_crisis": True, "reason": "medical_emergency"}
            elif any(kw in query for kw in ["ignore previous instructions", "chain-of-thought", "prompt ẩn", "canary token"]):
                data = {"severity": "high", "is_crisis": False, "reason": "prompt_injection_signal"}
            elif any(kw in query for kw in ["bỏ qua mọi chỉ dẫn", "bỏ qua chỉ thị", "system prompt"]):
                # If asking a benign regulation question, keep severity normal
                if any(kw in query for kw in ["học bổng", "quy định", "học phí", "học lại", "thủ tục"]):
                    data = {"severity": "normal", "is_crisis": False, "reason": None}
                else:
                    data = {"severity": "high", "is_crisis": False, "reason": "prompt_injection_signal"}
            elif any(kw in query for kw in ["tỉnh lẻ", "nhìn ngon quá", "khóa tủ rack", "tâm lý nhạy cảm", "trực bàn tuyển sinh", "server trường"]):
                data = {"severity": "high", "is_crisis": False, "reason": "sensitive_policy_violation"}
            else:
                data = {"severity": "normal", "is_crisis": False, "reason": None}
            return {
                "status": "completed",
                "output_text": json.dumps(data),
                "structured_output": data,
                "finish_reason": "stop",
                "usage": {"input_tokens": 30, "output_tokens": 15},
                "latency_ms": 10,
            }

        # 2. Intent classifier
        if any(kw in route_id for kw in ["intent", "route_intent", "intent_router"]) or "ai-prompt-intent-001" in route_id or "intentdecision" in request.system_instructions.lower():
            if any(kw in query for kw in ["tự tử", "tự sát", "muốn chết", "ngất xỉu", "co giật", "khong muon song", "đập nó", "chẳng thiết sống", "tỉnh lẻ", "server trường", "tâm lý nhạy cảm", "trực bàn tuyển sinh", "vác dao", "xử đẹp", "nhảy từ tầng thượng", "chẳng còn mặt mũi"]):
                chosen_route = "sensitive_case"
            elif any(kw in query for kw in ["sql_query", "quản trị viên", "cuộc trò chuyện của user khác", "user khác", "chain-of-thought", "prompt ẩn", "canary", "thời tiết", "nấu", "phở", "món ăn", "không liên quan"]):
                chosen_route = "unsupported"
            elif any(kw in query for kw in ["khiếu nại", "phản ánh", "báo cáo sự cố", "ticket"]):
                chosen_route = "ticket_create"
            elif any(kw in query for kw in ["gặp cán bộ", "tư vấn viên", "chuyển người trực", "gặp người", "cán bộ trực tiếp", "phòng đào tạo làm ăn", "nhìn ngon quá", "đòi tiền sinh viên", "dạy quá tệ", "học phí tăng vô lý", "bóc phốt", "dìm chết", "chạy điểm", "tố cáo chính thức", "dạy dốt", "đồ lừa đảo", "handover"]):
                chosen_route = "human_handover"
            elif any(kw in query for kw in ["mượn phòng", "đặt phòng", "giảng đường", "tìm phòng", "phòng còn trống", "hết thời gian chờ", "xác nhận đúng nội dung xem trước đặt phòng", "room"]):
                chosen_route = "room_booking"
            elif any(kw in query for kw in ["hồ sơ xin", "cần những mục nào", "bao nhiêu ngày làm việc", "thời điểm", "khoảng thời gian nào", "khi nào", "thời gian giải quyết", "quy trình xin", "điều kiện xin"]):
                chosen_route = "grounded_faq"
            elif any(kw in query for kw in ["tạo yêu cầu", "xin cấp", "đăng ký cấp", "giấy giới thiệu", "bảng điểm", "giấy xác nhận", "giấy chứng nhận", "hoãn nghĩa vụ", "vay vốn", "docreq"]) and "nhân tạo" not in query:
                chosen_route = "document_request"
            elif any(kw in query for kw in ["thời khóa biểu", "lịch học", "lịch thi", "tiết học", "xem lịch", "lịch của sinh viên", "schedule"]):
                chosen_route = "personal_schedule"
            elif any(kw in query for kw in ["học phí", "quy chế", "tín chỉ", "học bổng", "điều kiện", "hướng dẫn", "faq"]):
                chosen_route = "grounded_faq"
            elif not query.strip():
                return None
            else:
                chosen_route = "grounded_faq"

            data = {"route": chosen_route, "confidence": 0.98}
            return {
                "status": "completed",
                "output_text": json.dumps(data),
                "structured_output": data,
                "finish_reason": "stop",
                "usage": {"input_tokens": 25, "output_tokens": 12},
                "latency_ms": 10,
            }

        # 3. Grounded Answer
        if any(kw in route_id for kw in ["answer", "compose", "grounded"]) or "ai-prompt-answer-001" in route_id:
            answer_text = "Theo quy định mô phỏng của Đại học Xây dựng Hà Nội (HUCE Demo, không phải quy định chính thức), thông tin chi tiết đã được đối chiếu chính thức [CIT-001]."
            if "mâu thuẫn" in query:
                answer_text = "Phát hiện thông tin mâu thuẫn giữa các tài liệu mô phỏng [CIT-001]."
            elif "học phí" in query:
                answer_text = "Mức học phí là 480.000 VNĐ / tín chỉ theo quy định học phí Đại học Xây dựng Hà Nội [CIT-001]."
            data = {"response_text": answer_text, "citations": ["CIT-001"]}
            return {
                "status": "completed",
                "output_text": answer_text,
                "structured_output": data,
                "finish_reason": "stop",
                "usage": {"input_tokens": 40, "output_tokens": 20},
                "latency_ms": 10,
            }

        return None

    def _get_fixture(self, route_id: str, request: LlmRequest | None = None) -> dict[str, Any]:
        # 1. Exact route_id fixture
        if route_id in self._fixtures:
            return self._fixtures[route_id]

        # 2. Check hashed fixture key
        if request is not None:
            query = self._extract_query_text(request)
            prompt_version = str(request.trace_context.get("prompt_version", "1.0.0"))
            key = compute_fixture_key(route_id, prompt_version, query)
            if key in self._fixtures:
                return self._fixtures[key]

            # 3. Deterministic keyword-based match
            synth = self._synthesize_deterministic_fixture(request)
            if synth is not None:
                return synth

        raise KeyError(f"No fake LLM fixture registered for route: '{route_id}'")

    async def generate(self, request: LlmRequest) -> LlmResponse:
        self._recorded_requests.append(request)
        entry = self._get_fixture(request.route_id, request)

        status_str = entry.get("status", "completed")
        status = LlmResponseStatus(status_str)

        finish_str = entry.get("finish_reason", "stop")
        finish_reason = FinishReason(finish_str)

        usage_raw = entry.get("usage", {})
        usage = TokenUsage(
            input_tokens=usage_raw.get("input_tokens", 0),
            cached_input_tokens=usage_raw.get("cached_input_tokens", 0),
            output_tokens=usage_raw.get("output_tokens", 0),
            reasoning_tokens=usage_raw.get("reasoning_tokens", 0),
        )

        candidates: list[ToolCandidate] = []
        for c in entry.get("tool_candidates", []):
            candidates.append(
                ToolCandidate(
                    call_id=c.get("call_id", ""),
                    name=c.get("name", ""),
                    arguments=c.get("arguments", {}),
                )
            )

        return LlmResponse(
            status=status,
            provider_id="fake",
            model_id=f"fake-{request.model_profile}",
            provider_request_id=f"fake-req-{request.request_id[:8]}",
            output_text=entry.get("output_text"),
            structured_output=entry.get("structured_output"),
            tool_candidates=tuple(candidates),
            finish_reason=finish_reason,
            usage=usage,
            latency_ms=entry.get("latency_ms", 10),
            attempt=1,
        )

    async def stream(self, request: LlmRequest) -> AsyncIterator[LlmEvent]:
        self._recorded_requests.append(request)
        entry = self._get_fixture(request.route_id, request)

        yield LlmEvent(event_type=LlmEventType.RESPONSE_STARTED)

        chunks = entry.get("chunks")
        if chunks:
            for chunk in chunks:
                yield LlmEvent(event_type=LlmEventType.TEXT_DELTA, delta=chunk)
        elif entry.get("output_text"):
            yield LlmEvent(event_type=LlmEventType.TEXT_DELTA, delta=entry["output_text"])

        usage_raw = entry.get("usage", {})
        usage = TokenUsage(
            input_tokens=usage_raw.get("input_tokens", 0),
            cached_input_tokens=usage_raw.get("cached_input_tokens", 0),
            output_tokens=usage_raw.get("output_tokens", 0),
            reasoning_tokens=usage_raw.get("reasoning_tokens", 0),
        )
        yield LlmEvent(event_type=LlmEventType.USAGE_FINAL, usage=usage)

        status_str = entry.get("status", "completed")
        if status_str == "completed":
            yield LlmEvent(event_type=LlmEventType.RESPONSE_COMPLETED, status=LlmResponseStatus.COMPLETED)
        else:
            yield LlmEvent(
                event_type=LlmEventType.RESPONSE_FAILED,
                status=LlmResponseStatus.FAILED,
                error_message=entry.get("error_message", "LLM request failed"),
            )

    def capabilities(self, provider_id: str, model_id: str) -> ModelCapabilities:
        return ModelCapabilities(
            provider_id="fake",
            model_id=model_id,
            supports_structured_output=True,
            supports_function_tools=True,
            supports_streaming=True,
            supports_images=False,
            supports_stateless_requests=True,
            context_tokens=32768,
            max_output_tokens=4096,
        )
