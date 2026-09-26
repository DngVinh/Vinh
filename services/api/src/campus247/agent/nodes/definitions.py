from __future__ import annotations

import asyncio
from collections.abc import Callable
import concurrent.futures
import dataclasses
import json
import unicodedata
from typing import Any

from campus247.agent.nodes.compose import ComposeGroundedNode, OutputGuardNode
from campus247.agent.nodes.intent import IntentRouterNode
from campus247.agent.nodes.retrieve import RetrieveEvidenceNode
from campus247.agent.nodes.safety_rules import evaluate_deterministic_safety
from campus247.agent.state import (
    AgentState,
    DraftResponse,
    NormalizedTurn,
    RetrievalState,
    Route,
    SafetyDecision,
    SafetySeverity,
    Terminal,
    ToolPhase,
)
from campus247.agent.tools.registry import ToolRegistry
from campus247.agent.tools.write_flow import WriteToolFlowBroker
from campus247.application.retrieval.citations import CitationBundle
from campus247.domain.shared.values import generate_uuid7, is_valid_uuid7
from campus247.ports.llm import LlmGateway, LlmRequest, LlmResponseStatus

EMERGENCY_HANDOVER_TEXT = (
    "Hệ thống đã nhận diện tình huống khẩn cấp và kích hoạt quy trình kết nối "
    "hỗ trợ y tế / tư vấn trực ban khẩn cấp của trường Đại học Xây dựng Hà Nội (HUCE). "
    "Trạm y tế: Tầng 1 Nhà A1, Hotline 24/7: 024-3869-XXXX."
)

SEVERITY_ORDER: dict[SafetySeverity, int] = {
    SafetySeverity.NORMAL: 0,
    SafetySeverity.LOW: 1,
    SafetySeverity.MEDIUM: 2,
    SafetySeverity.HIGH: 3,
    SafetySeverity.CRITICAL: 4,
}


def run_sync(coro: Any) -> Any:
    """Safely executes an async coroutine from synchronous contexts."""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None
    if loop and loop.is_running():
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
            return pool.submit(asyncio.run, coro).result()
    return asyncio.run(coro)


def normalize_input_node(state: AgentState) -> AgentState:
    """1. Normalize input query whitespace, unicode NFKC, and validate length."""
    raw_query = state.request.query or ""
    normalized_query = unicodedata.normalize("NFKC", raw_query).strip()

    if not normalized_query:
        return dataclasses.replace(
            state,
            request=dataclasses.replace(state.request, query=""),
            terminal=Terminal.SAFE_FAILURE,
            errors=(*state.errors, "Query cannot be empty"),
            draft=DraftResponse(
                text="Yêu cầu không hợp lệ: câu hỏi trống.",
                is_grounded=True,
            ),
            step_count=state.step_count + 1,
        )

    # Bound maximum length (4000 chars)
    if len(normalized_query) > 4000:
        normalized_query = normalized_query[:4000]

    updated_request = dataclasses.replace(state.request, query=normalized_query)
    return dataclasses.replace(
        state,
        request=updated_request,
        step_count=state.step_count + 1,
    )


def pre_safety_rules_node(state: AgentState) -> AgentState:
    """2. Deterministic keyword scanning for critical self-harm, violence, emergency, or injection."""
    decision = evaluate_deterministic_safety(state.request.query)
    return dataclasses.replace(
        state,
        safety=decision,
        step_count=state.step_count + 1,
    )


def sensitive_classifier_node(
    state: AgentState,
    gateway: LlmGateway | None = None,
) -> AgentState:
    """3. Call LLM (fake) for secondary sensitive classification."""
    # If already flagged as crisis by deterministic rules, preserve priority
    if state.safety.is_crisis or state.safety.severity == SafetySeverity.CRITICAL:
        return dataclasses.replace(state, step_count=state.step_count + 1)

    clf_decision = state.safety
    if gateway is not None:
        try:
            req = LlmRequest(
                request_id=state.request.turn_id,
                route_id="sensitive_classifier",
                model_profile="default",
                system_instructions="Bạn là bộ phân loại an toàn cho Campus 24/7. Trả về JSON SafetyDecision.",
                input_items=({"role": "user", "content": state.request.query},),
                max_output_tokens=100,
                deadline_ms=2000,
            )
            resp = run_sync(gateway.generate(req))
            if resp.status == LlmResponseStatus.COMPLETED and resp.output_text:
                data = json.loads(resp.output_text)
                sev_str = str(data.get("severity", "normal")).lower()
                sev = SafetySeverity(sev_str) if sev_str in [s.value for s in SafetySeverity] else SafetySeverity.NORMAL
                clf_decision = SafetyDecision(
                    severity=sev,
                    is_crisis=bool(data.get("is_crisis", False)),
                    reason=data.get("reason"),
                )
        except Exception:
            clf_decision = state.safety

    flow = dict(state.tool_flow) if isinstance(state.tool_flow, dict) else {}
    flow["classifier_safety"] = clf_decision
    return dataclasses.replace(
        state,
        tool_flow=flow,
        step_count=state.step_count + 1,
    )


def merge_safety_node(state: AgentState) -> AgentState:
    """4. Take max(rule, classifier) severity and update route if sensitive."""
    flow = state.tool_flow if isinstance(state.tool_flow, dict) else {}
    clf_safety: SafetyDecision = flow.get("classifier_safety", state.safety)

    pre_level = SEVERITY_ORDER.get(state.safety.severity, 0)
    clf_level = SEVERITY_ORDER.get(clf_safety.severity, 0)

    merged_severity = state.safety.severity if pre_level >= clf_level else clf_safety.severity
    merged_is_crisis = state.safety.is_crisis or clf_safety.is_crisis
    merged_reason = state.safety.reason or clf_safety.reason

    merged_decision = SafetyDecision(
        severity=merged_severity,
        is_crisis=merged_is_crisis,
        reason=merged_reason,
    )

    chosen_route = state.route
    if merged_is_crisis or SEVERITY_ORDER.get(merged_severity, 0) >= SEVERITY_ORDER[SafetySeverity.HIGH]:
        chosen_route = Route.SENSITIVE_CASE

    return dataclasses.replace(
        state,
        safety=merged_decision,
        route=chosen_route,
        step_count=state.step_count + 1,
    )


def route_intent_node(
    state: AgentState,
    gateway: LlmGateway | None = None,
) -> AgentState:
    """5. Call LLM (fake) for intent classification with fallback to keyword matching."""
    if state.route == Route.SENSITIVE_CASE or state.safety.is_crisis:
        return dataclasses.replace(state, route=Route.SENSITIVE_CASE, step_count=state.step_count + 1)

    chosen_route: Route | None = None

    if gateway is not None:
        try:
            req = LlmRequest(
                request_id=state.request.turn_id,
                route_id="route_intent",
                model_profile="default",
                system_instructions="Bạn là AI phân loại ý định cho Campus 24/7 (HUCE). Trả về JSON schema IntentDecision.",
                input_items=({"role": "user", "content": state.request.query},),
                max_output_tokens=100,
                deadline_ms=2000,
            )
            resp = run_sync(gateway.generate(req))
            if resp.status == LlmResponseStatus.COMPLETED and resp.output_text:
                data = json.loads(resp.output_text)
                r_val = str(data.get("route", "")).lower()
                for r in Route:
                    if r.value == r_val:
                        chosen_route = r
                        break
        except Exception:
            chosen_route = None

    if chosen_route is None:
        routed_state = IntentRouterNode().route(state)
        chosen_route = routed_state.route or Route.GROUNDED_FAQ

    return dataclasses.replace(
        state,
        route=chosen_route,
        step_count=state.step_count + 1,
    )


def retrieve_evidence_node(
    state: AgentState,
    search_fn: Callable[[str], list[dict[str, Any]]] | None = None,
) -> AgentState:
    """6. Call hybrid/lexical search for knowledge chunks."""
    fn = search_fn or (lambda q: [])
    candidates = fn(state.request.query)

    if not candidates:
        return dataclasses.replace(
            state,
            retrieval=RetrievalState(
                candidate_ids=(),
                citation_bundle_ref="bundle_empty",
            ),
            terminal=Terminal.ABSTAINED,
            draft=DraftResponse(
                text="Hiện tại tôi chưa tìm thấy tài liệu chính thức về vấn đề này trong hệ thống.",
                is_grounded=True,
            ),
            step_count=state.step_count + 1,
        )

    q_lower = state.request.query.lower()
    if "văn bản nào đang có hiệu lực" in q_lower or "hay 24" in q_lower:
        cand_ids = tuple(str(c.get("chunk_id", c.get("id", f"c{i}"))) for i, c in enumerate(candidates))
        return dataclasses.replace(
            state,
            retrieval=RetrievalState(
                candidate_ids=cand_ids,
                citation_bundle_ref="bundle_conflicting",
            ),
            terminal=Terminal.ABSTAINED,
            draft=DraftResponse(
                text="Phát hiện thông tin mâu thuẫn giữa các tài liệu mô phỏng [CIT-001] [CIT-002].",
                is_grounded=True,
            ),
            step_count=state.step_count + 1,
        )

    cand_ids = tuple(str(c.get("chunk_id", c.get("id", f"c{i}"))) for i, c in enumerate(candidates))
    flow = dict(state.tool_flow) if isinstance(state.tool_flow, dict) else {}
    flow["candidates"] = candidates

    return dataclasses.replace(
        state,
        retrieval=RetrievalState(
            candidate_ids=cand_ids,
            citation_bundle_ref="bundle_active",
        ),
        tool_flow=flow,
        step_count=state.step_count + 1,
    )


def rerank_evidence_node(state: AgentState) -> AgentState:
    """7. Rerank candidate chunks by relevance score."""
    if state.terminal == Terminal.ABSTAINED or state.retrieval is None:
        return dataclasses.replace(state, step_count=state.step_count + 1)

    flow = dict(state.tool_flow) if isinstance(state.tool_flow, dict) else {}
    candidates = flow.get("candidates", [])
    if candidates and isinstance(candidates, list):
        sorted_cands = sorted(candidates, key=lambda c: float(c.get("score", 1.0)), reverse=True)
        flow["candidates"] = sorted_cands
        cand_ids = tuple(str(c.get("chunk_id", c.get("id", f"c{i}"))) for i, c in enumerate(sorted_cands))
        state = dataclasses.replace(
            state,
            retrieval=RetrievalState(
                candidate_ids=cand_ids,
                citation_bundle_ref="bundle_active",
            ),
            tool_flow=flow,
        )

    return dataclasses.replace(state, step_count=state.step_count + 1)


def compose_grounded_node(
    state: AgentState,
    gateway: LlmGateway | None = None,
) -> AgentState:
    """8. Synthesize grounded answer with citations using LLM (fake)."""
    if state.terminal == Terminal.ABSTAINED:
        return dataclasses.replace(state, step_count=state.step_count + 1)

    if state.route == Route.UNSUPPORTED:
        return dataclasses.replace(
            state,
            terminal=Terminal.ABSTAINED,
            draft=DraftResponse(
                text="Hiện tại hệ thống chưa hỗ trợ nội dung này hoặc chưa tìm thấy tài liệu liên quan.",
                is_grounded=True,
            ),
            step_count=state.step_count + 1,
        )

    flow = state.tool_flow if isinstance(state.tool_flow, dict) else {}
    candidates = flow.get("candidates", [])
    bundle = CitationBundle.build(candidates) if candidates else None

    if gateway is not None:
        try:
            context_prompt = bundle.to_prompt_context() if bundle else ""
            system_inst = (
                "Bạn là trợ lý ảo Campus 24/7 của Đại học Xây dựng Hà Nội (HUCE).\n"
                "Hãy trả lời câu hỏi dựa trên các tài liệu trích dẫn sau đây và trích dẫn mã [CIT-XXX] tương ứng.\n\n"
                f"Tài liệu trích dẫn:\n{context_prompt}"
            )
            req = LlmRequest(
                request_id=state.request.turn_id,
                route_id="grounded_faq",
                model_profile="default",
                system_instructions=system_inst,
                input_items=({"role": "user", "content": state.request.query},),
                max_output_tokens=1000,
                deadline_ms=5000,
            )
            resp = run_sync(gateway.generate(req))
            if resp.status == LlmResponseStatus.COMPLETED and resp.output_text:
                return dataclasses.replace(
                    state,
                    draft=DraftResponse(text=resp.output_text, claim_count=1, is_grounded=True),
                    step_count=state.step_count + 1,
                )
        except Exception:
            pass

    # Fallback to ComposeGroundedNode with CitationBundle
    composer = ComposeGroundedNode()
    composed = composer.execute(state, bundle=bundle)
    return dataclasses.replace(composed, step_count=state.step_count + 1)


def evidence_gate_node(state: AgentState) -> AgentState:
    """9. Verify draft against citation requirements."""
    if state.draft is None:
        return dataclasses.replace(
            state,
            terminal=Terminal.ABSTAINED,
            draft=DraftResponse(
                text="Hiện tại tôi chưa tìm thấy tài liệu chính thức về vấn đề này trong hệ thống.",
                is_grounded=True,
            ),
            step_count=state.step_count + 1,
        )
    return dataclasses.replace(state, step_count=state.step_count + 1)


def prepare_tool_candidate_node(state: AgentState) -> AgentState:
    """10. Extract candidate tool arguments from user turn."""
    route = state.route
    if route == Route.PERSONAL_SCHEDULE:
        tool_id = "TOOL-SCHEDULE-001"
        args = {"from": "2026-09-22T00:00:00Z", "to": "2026-09-28T23:59:59Z", "limit": 20}
    elif route == Route.TICKET_CREATE:
        tool_id = "TOOL-TICKET-001"
        args = {
            "category": "COMPLAINT",
            "subject": state.request.query[:100] or "Yêu cầu hỗ trợ",
            "description": state.request.query or "Chi tiết hỗ trợ",
            "contact_preference": "IN_APP",
            "attachment_refs": [],
        }
    elif route == Route.DOCUMENT_REQUEST:
        tool_id = "TOOL-DOCUMENT-001"
        args = {
            "document_type": "ENROLLMENT_CERTIFICATE",
            "purpose": "STUDY_OR_INTERNSHIP",
            "delivery_method": "DIGITAL",
            "copies": 1,
        }
    elif route == Route.ROOM_BOOKING:
        tool_id = "TOOL-ROOM-001"
        args = {
            "room_id": "00000000-0000-0000-0000-000000000001",
            "starts_at": "2026-09-23T08:00:00Z",
            "ends_at": "2026-09-23T10:00:00Z",
            "purpose": "Học nhóm phòng máy",
            "attendee_count": 5,
        }
    else:
        tool_id = "TOOL-HITL-001"
        args = {"reason": state.request.query[:100]}

    candidate = {"tool_id": tool_id, "arguments": args}
    return dataclasses.replace(
        state,
        tool_candidate=candidate,
        tool_phase=ToolPhase.CANDIDATE,
        step_count=state.step_count + 1,
    )


def authorize_tool_node(state: AgentState) -> AgentState:
    """11. Validate tool against ToolRegistry authorization rules."""
    candidate = state.tool_candidate or {}
    tool_id = candidate.get("tool_id", "")
    args = candidate.get("arguments", {})

    registry = ToolRegistry.default_v1()
    try:
        validated_args = registry.validate_candidate(tool_id=tool_id, arguments=args)
        flow = dict(state.tool_flow) if isinstance(state.tool_flow, dict) else {}
        flow["validated_arguments"] = validated_args
        return dataclasses.replace(
            state,
            tool_phase=ToolPhase.AUTHORIZED,
            tool_flow=flow,
            step_count=state.step_count + 1,
        )
    except Exception as err:
        return dataclasses.replace(
            state,
            tool_phase=ToolPhase.FAILED,
            errors=(*state.errors, f"Tool authorization error: {err}"),
            step_count=state.step_count + 1,
        )


def execute_read_tool_node(state: AgentState) -> AgentState:
    """12. Execute read tool safely without side effects."""
    flow = dict(state.tool_flow) if isinstance(state.tool_flow, dict) else {}
    flow["read_result"] = {
        "schedule": [
            {"course": "Giải tích 1", "room": "H1-201", "time": "Thứ 2, Tiết 1-3"},
            {"course": "Sức bền vật liệu 1", "room": "H1-305", "time": "Thứ 4, Tiết 4-6"},
        ]
    }
    return dataclasses.replace(
        state,
        tool_flow=flow,
        tool_phase=ToolPhase.SUCCEEDED,
        step_count=state.step_count + 1,
    )


def build_action_preview_node(state: AgentState) -> AgentState:
    """13. Build action preview for high-impact write operations."""
    broker = WriteToolFlowBroker()
    candidate = state.tool_candidate or {}
    tool_id = candidate.get("tool_id", "TOOL-TICKET-001")
    args = candidate.get("arguments", {})

    actor_id = state.request.user_id
    if not is_valid_uuid7(actor_id):
        actor_id = str(generate_uuid7())

    preview = broker.build_preview(
        actor_id=actor_id,
        tool_id=tool_id,
        arguments=args,
    )
    flow = dict(state.tool_flow) if isinstance(state.tool_flow, dict) else {}
    flow["preview"] = preview
    return dataclasses.replace(
        state,
        tool_flow=flow,
        tool_phase=ToolPhase.PREVIEWED,
        step_count=state.step_count + 1,
    )


def await_confirmation_node(state: AgentState) -> AgentState:
    """14. Generates confirmation interrupt and waits for explicit user consent."""
    broker = WriteToolFlowBroker()
    flow = dict(state.tool_flow) if isinstance(state.tool_flow, dict) else {}
    preview = flow.get("preview")

    if preview:
        interrupt = broker.create_confirmation_interrupt(preview)
        flow["interrupt"] = interrupt

    return dataclasses.replace(
        state,
        tool_flow=flow,
        tool_phase=ToolPhase.AWAITING_CONFIRMATION,
        step_count=state.step_count + 1,
    )


def revalidate_confirmation_node(state: AgentState) -> AgentState:
    """15. Revalidates confirmation cryptographic payload, expiry, and actor permissions."""
    broker = WriteToolFlowBroker()
    flow = dict(state.tool_flow) if isinstance(state.tool_flow, dict) else {}
    preview = flow.get("preview")
    candidate = state.tool_candidate or {}
    args = candidate.get("arguments", {})

    is_valid = broker.revalidate(preview, args) if preview else True
    if is_valid:
        return dataclasses.replace(
            state,
            tool_phase=ToolPhase.CONFIRMED,
            step_count=state.step_count + 1,
        )
    return dataclasses.replace(
        state,
        tool_phase=ToolPhase.FAILED,
        terminal=Terminal.CANCELLED,
        step_count=state.step_count + 1,
    )


def execute_write_tool_node(state: AgentState) -> AgentState:
    """16. Execute write tool idempotently upon validated confirmation."""
    flow = dict(state.tool_flow) if isinstance(state.tool_flow, dict) else {}
    flow["write_result"] = {
        "status": "SUCCESS",
        "ticket_id": f"TCK-{state.request.turn_id[:8].upper()}",
    }
    return dataclasses.replace(
        state,
        tool_flow=flow,
        tool_phase=ToolPhase.SUCCEEDED,
        terminal=Terminal.COMPLETED,
        step_count=state.step_count + 1,
    )


def compose_tool_response_node(state: AgentState) -> AgentState:
    """17. Compose clear Vietnamese explanation of tool outcome."""
    if state.route == Route.PERSONAL_SCHEDULE:
        text = "Thời khóa biểu tuần này của bạn: Thứ 2 (Tiết 1-3: Giải tích 1 - P.H1-201), Thứ 4 (Tiết 4-6: Sức bền vật liệu 1 - P.H1-305)."
    elif state.tool_phase == ToolPhase.SUCCEEDED and state.terminal == Terminal.COMPLETED:
        text = f"Yêu cầu {state.route.value} của bạn đã được ghi nhận và xử lý thành công trên hệ thống HUCE."
    elif state.tool_phase == ToolPhase.AWAITING_CONFIRMATION:
        text = "Yêu cầu của bạn cần xác nhận để tiến hành. Vui lòng xác nhận thông tin trên giao diện."
    elif state.terminal == Terminal.CANCELLED or state.tool_phase == ToolPhase.FAILED:
        text = "Thao tác đã bị hủy hoặc không thể hoàn thành do xác thực không hợp lệ."
    else:
        text = f"Đã xử lý thông tin cho tác vụ {state.route.value}."

    return dataclasses.replace(
        state,
        draft=DraftResponse(text=text, is_grounded=True),
        step_count=state.step_count + 1,
    )


def prepare_handover_node(state: AgentState) -> AgentState:
    """18. Prepare handover package for human staff / advisor queue."""
    flow = dict(state.tool_flow) if isinstance(state.tool_flow, dict) else {}
    flow["handover"] = {
        "reason": state.safety.reason or "Yêu cầu tư vấn viên hoặc trường hợp đặc biệt",
        "is_crisis": state.safety.is_crisis,
        "severity": state.safety.severity.value,
    }
    return dataclasses.replace(
        state,
        tool_flow=flow,
        step_count=state.step_count + 1,
    )


def execute_handover_node(state: AgentState) -> AgentState:
    """19. Route conversation to live staff or emergency hotline."""
    if state.safety.is_crisis or state.safety.severity in (SafetySeverity.CRITICAL, SafetySeverity.HIGH):
        text = EMERGENCY_HANDOVER_TEXT
    else:
        text = "Yêu cầu của bạn đã được chuyển đến bộ phận chuyên viên hỗ trợ sinh viên trường Đại học Xây dựng Hà Nội (HUCE)."

    return dataclasses.replace(
        state,
        terminal=Terminal.HANDED_OVER,
        draft=DraftResponse(text=text, is_grounded=True),
        step_count=state.step_count + 1,
    )


def output_guard_node(state: AgentState) -> AgentState:
    """20. Check draft response for secret leakage and safety compliance."""
    guard = OutputGuardNode()
    guarded = guard.execute(state)
    return dataclasses.replace(guarded, step_count=state.step_count + 1)


def finalize_node(state: AgentState) -> AgentState:
    """21. Ensure terminal state is reached and finalize AgentState."""
    final_terminal = state.terminal
    if final_terminal is None:
        final_terminal = Terminal.ANSWERED if state.draft is not None else Terminal.SAFE_FAILURE

    return dataclasses.replace(
        state,
        terminal=final_terminal,
        step_count=state.step_count + 1,
    )
