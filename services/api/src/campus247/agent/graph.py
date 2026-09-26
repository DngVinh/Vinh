from __future__ import annotations

from collections.abc import Callable
import dataclasses
from typing import Any

from langgraph.graph import END, START, StateGraph

from campus247.agent.nodes.definitions import (
    authorize_tool_node,
    await_confirmation_node,
    build_action_preview_node,
    compose_grounded_node,
    compose_tool_response_node,
    evidence_gate_node,
    execute_handover_node,
    execute_read_tool_node,
    execute_write_tool_node,
    finalize_node,
    merge_safety_node,
    normalize_input_node,
    output_guard_node,
    pre_safety_rules_node,
    prepare_handover_node,
    prepare_tool_candidate_node,
    rerank_evidence_node,
    retrieve_evidence_node,
    revalidate_confirmation_node,
    route_intent_node,
    sensitive_classifier_node,
)
from campus247.agent.state import (
    AgentState,
    DraftResponse,
    NormalizedTurn,
    Route,
    SafetySeverity,
    Terminal,
    ToolPhase,
)
from campus247.domain.shared.values import generate_uuid7
from campus247.infrastructure.llm.fake import DeterministicFakeProvider
from campus247.ports.llm import LlmGateway


def build_agent_graph(
    search_fn: Callable[[str], list[dict[str, Any]]] | None = None,
    gateway: LlmGateway | None = None,
    checkpointer: Any | None = None,
) -> Any:
    """Builds and compiles the 21-node LangGraph StateGraph with all conditional routes."""
    builder = StateGraph(AgentState)

    # 1. Register all 21 nodes
    builder.add_node("normalize_input", normalize_input_node)
    builder.add_node("pre_safety_rules", pre_safety_rules_node)
    builder.add_node(
        "sensitive_classifier",
        lambda state: sensitive_classifier_node(state, gateway=gateway),
    )
    builder.add_node("merge_safety", merge_safety_node)
    builder.add_node(
        "route_intent",
        lambda state: route_intent_node(state, gateway=gateway),
    )

    builder.add_node(
        "retrieve_evidence",
        lambda state: retrieve_evidence_node(state, search_fn=search_fn),
    )
    builder.add_node("rerank_evidence", rerank_evidence_node)
    builder.add_node(
        "compose_grounded",
        lambda state: compose_grounded_node(state, gateway=gateway),
    )
    builder.add_node("evidence_gate", evidence_gate_node)

    builder.add_node("prepare_tool_candidate", prepare_tool_candidate_node)
    builder.add_node("authorize_tool", authorize_tool_node)
    builder.add_node("execute_read_tool", execute_read_tool_node)
    builder.add_node("build_action_preview", build_action_preview_node)
    builder.add_node("await_confirmation", await_confirmation_node)
    builder.add_node("revalidate_confirmation", revalidate_confirmation_node)
    builder.add_node("execute_write_tool", execute_write_tool_node)
    builder.add_node("compose_tool_response", compose_tool_response_node)

    builder.add_node("prepare_handover", prepare_handover_node)
    builder.add_node("execute_handover", execute_handover_node)

    builder.add_node("output_guard", output_guard_node)
    builder.add_node("finalize", finalize_node)

    # 2. Linear Pipeline Edges
    builder.add_edge(START, "normalize_input")
    builder.add_edge("normalize_input", "pre_safety_rules")
    builder.add_edge("pre_safety_rules", "sensitive_classifier")
    builder.add_edge("sensitive_classifier", "merge_safety")

    # 3. Conditional Branch from merge_safety
    def _route_after_safety(state: AgentState) -> str:
        if (
            state.route == Route.SENSITIVE_CASE
            or state.safety.is_crisis
            or state.safety.severity in (SafetySeverity.CRITICAL, SafetySeverity.HIGH)
        ):
            return "prepare_handover"
        return "route_intent"

    builder.add_conditional_edges(
        "merge_safety",
        _route_after_safety,
        {
            "prepare_handover": "prepare_handover",
            "route_intent": "route_intent",
        },
    )

    # 4. Conditional Branch from route_intent (8 routes)
    def _route_intent_branch(state: AgentState) -> str:
        route = state.route
        if route == Route.GROUNDED_FAQ:
            return "retrieve_evidence"
        if route in (
            Route.PERSONAL_SCHEDULE,
            Route.TICKET_CREATE,
            Route.DOCUMENT_REQUEST,
            Route.ROOM_BOOKING,
        ):
            return "prepare_tool_candidate"
        if route in (Route.HUMAN_HANDOVER, Route.SENSITIVE_CASE):
            return "prepare_handover"
        if route == Route.UNSUPPORTED:
            return "compose_grounded"
        return "retrieve_evidence"

    builder.add_conditional_edges(
        "route_intent",
        _route_intent_branch,
        {
            "retrieve_evidence": "retrieve_evidence",
            "prepare_tool_candidate": "prepare_tool_candidate",
            "prepare_handover": "prepare_handover",
            "compose_grounded": "compose_grounded",
        },
    )

    # 5. Retrieval Conditional Edges
    def _route_after_retrieve(state: AgentState) -> str:
        if state.terminal == Terminal.ABSTAINED:
            return "output_guard"
        return "rerank_evidence"

    builder.add_conditional_edges(
        "retrieve_evidence",
        _route_after_retrieve,
        {
            "output_guard": "output_guard",
            "rerank_evidence": "rerank_evidence",
        },
    )

    builder.add_edge("rerank_evidence", "compose_grounded")
    builder.add_edge("compose_grounded", "evidence_gate")
    builder.add_edge("evidence_gate", "output_guard")

    # 6. Tool Flow Edges
    builder.add_edge("prepare_tool_candidate", "authorize_tool")

    def _route_after_authorize(state: AgentState) -> str:
        if state.tool_phase == ToolPhase.FAILED:
            return "compose_tool_response"
        if state.route == Route.PERSONAL_SCHEDULE:
            return "execute_read_tool"
        return "build_action_preview"

    builder.add_conditional_edges(
        "authorize_tool",
        _route_after_authorize,
        {
            "compose_tool_response": "compose_tool_response",
            "execute_read_tool": "execute_read_tool",
            "build_action_preview": "build_action_preview",
        },
    )

    builder.add_edge("execute_read_tool", "compose_tool_response")
    builder.add_edge("build_action_preview", "await_confirmation")
    builder.add_edge("await_confirmation", "revalidate_confirmation")

    def _route_after_revalidate(state: AgentState) -> str:
        if state.tool_phase == ToolPhase.CONFIRMED:
            return "execute_write_tool"
        return "compose_tool_response"

    builder.add_conditional_edges(
        "revalidate_confirmation",
        _route_after_revalidate,
        {
            "execute_write_tool": "execute_write_tool",
            "compose_tool_response": "compose_tool_response",
        },
    )

    builder.add_edge("execute_write_tool", "compose_tool_response")
    builder.add_edge("compose_tool_response", "output_guard")

    # 7. Handover Flow Edges
    builder.add_edge("prepare_handover", "execute_handover")
    builder.add_edge("execute_handover", "output_guard")

    # 8. Output Guard to Finalize to END
    builder.add_edge("output_guard", "finalize")
    builder.add_edge("finalize", END)

    interrupt_nodes = ["await_confirmation"] if checkpointer is not None else None
    return builder.compile(checkpointer=checkpointer, interrupt_before=interrupt_nodes)


class CampusAgentWorkflow:
    """Compiled, controlled state machine workflow coordinating 21 agent nodes across 8 routes."""

    def __init__(
        self,
        search_fn: Callable[[str], list[dict[str, Any]]] | None = None,
        llm_gateway: LlmGateway | None = None,
        checkpointer: Any | None = None,
        max_steps: int = 24,
    ) -> None:
        self._search_fn = search_fn or (lambda q: [])
        self._gateway = llm_gateway or DeterministicFakeProvider.default()
        self._checkpointer = checkpointer
        self._max_steps = max_steps
        self._app = build_agent_graph(
            search_fn=self._search_fn,
            gateway=self._gateway,
            checkpointer=self._checkpointer,
        )

    def run(self, input_val: NormalizedTurn | str) -> AgentState:
        """Executes the full agent graph with NormalizedTurn or user query string."""
        if isinstance(input_val, str):
            turn = NormalizedTurn(
                session_id=str(generate_uuid7()),
                turn_id=str(generate_uuid7()),
                user_id=str(generate_uuid7()),
                query=input_val,
            )
        else:
            turn = input_val

        initial_state = AgentState(request=turn)

        try:
            raw_res = self._app.invoke(
                initial_state,
                config={"recursion_limit": self._max_steps},
            )
            if isinstance(raw_res, dict):
                final_state = AgentState(**raw_res)
            elif isinstance(raw_res, AgentState):
                final_state = raw_res
            else:
                final_state = initial_state

            # If steps exceeded limit
            if final_state.step_count >= self._max_steps:
                return dataclasses.replace(
                    final_state,
                    terminal=Terminal.SAFE_FAILURE,
                    errors=(*final_state.errors, "Max step limit reached"),
                )

            return final_state
        except Exception as err:
            return dataclasses.replace(
                initial_state,
                terminal=Terminal.SAFE_FAILURE,
                errors=(*initial_state.errors, f"Workflow execution error: {err}"),
                draft=DraftResponse(
                    text="Đã xảy ra sự cố trong quá trình xử lý yêu cầu.",
                    is_grounded=True,
                ),
            )
