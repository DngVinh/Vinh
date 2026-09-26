from __future__ import annotations

from pathlib import Path
import sys
import pytest

ROOT = Path(__file__).resolve().parents[3]
API_SRC = ROOT / "services" / "api" / "src"
if str(API_SRC) not in sys.path:
    sys.path.insert(0, str(API_SRC))

from campus247.agent.nodes.intent import IntentRouterNode
from campus247.agent.state import (
    AgentState,
    NormalizedTurn,
    Route,
    SafetyDecision,
    SafetySeverity,
)


def make_state(query: str, safety: SafetyDecision | None = None) -> AgentState:
    return AgentState(
        request=NormalizedTurn(
            session_id="s1",
            turn_id="t1",
            user_id="u1",
            query=query,
        ),
        safety=safety or SafetyDecision(severity=SafetySeverity.NORMAL),
    )


def test_intent_router_crisis_priority() -> None:
    router = IntentRouterNode()
    state = make_state(
        "Học phí bao nhiêu",
        safety=SafetyDecision(severity=SafetySeverity.CRITICAL, is_crisis=True, reason="emergency"),
    )
    next_state = router.route(state)
    assert next_state.route == Route.SENSITIVE_CASE


def test_intent_router_classifies_faq() -> None:
    router = IntentRouterNode()
    state = make_state("Mức học phí năm học 2026-2027 là bao nhiêu?")
    next_state = router.route(state)
    assert next_state.route == Route.GROUNDED_FAQ


def test_intent_router_classifies_schedule() -> None:
    router = IntentRouterNode()
    state = make_state("Xem thời khóa biểu tuần này của tôi")
    next_state = router.route(state)
    assert next_state.route == Route.PERSONAL_SCHEDULE


def test_intent_router_classifies_docreq() -> None:
    router = IntentRouterNode()
    state = make_state("Tôi muốn xin cấp giấy xác nhận sinh viên và bảng điểm")
    next_state = router.route(state)
    assert next_state.route == Route.DOCUMENT_REQUEST


def test_intent_router_classifies_room_booking() -> None:
    router = IntentRouterNode()
    state = make_state("Đăng ký mượn phòng học H1 để sinh hoạt CLB")
    next_state = router.route(state)
    assert next_state.route == Route.ROOM_BOOKING
