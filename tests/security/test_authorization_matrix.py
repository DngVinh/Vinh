from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
import sys
import pytest

ROOT = Path(__file__).resolve().parents[2]
API_SRC = ROOT / "services" / "api" / "src"
if str(API_SRC) not in sys.path:
    sys.path.insert(0, str(API_SRC))

from campus247.domain.policy.staff import StaffPolicyEngine
from campus247.domain.policy.student import StudentPolicyEngine
from campus247.domain.shared.values import generate_uuid7
from campus247.ports.identity import IdentityContext, IdentityRole
from campus247.ports.policy import PolicyEvaluationRequest, PolicyResourceContext


def make_actor(role: IdentityRole, unit_ids: tuple[str, ...] = ()):
    now = datetime.now(timezone.utc)
    uid = generate_uuid7()
    return IdentityContext(
        subject_id=uid,
        external_subject=f"syn_{uid}",
        issuer="urn:campus247:issuer:synthetic",
        roles=(role,),
        display_name=f"User {role.value}",
        auth_time=now,
        expires_at=now + timedelta(hours=1),
        unit_ids=unit_ids,
        student_code="SYN12345678" if role == IdentityRole.STUDENT else None,
    )


def test_cross_user_student_isolation():
    student_a = make_actor(IdentityRole.STUDENT)
    student_b_id = generate_uuid7()

    engine = StudentPolicyEngine()

    # Student A cannot read Student B ticket
    req = PolicyEvaluationRequest(
        actor=student_a,
        action="ticket.read",
        resource_type="ticket",
        resource=PolicyResourceContext(owner_subject_id=student_b_id),
        correlation_id=generate_uuid7(),
    )
    res = engine.evaluate(req)
    assert res.is_allowed is False
    assert res.reason_code == "OWNERSHIP_REQUIRED"

    # Student A cannot read Student B conversation
    req_conv = PolicyEvaluationRequest(
        actor=student_a,
        action="conversation.read",
        resource_type="conversation",
        resource=PolicyResourceContext(owner_subject_id=student_b_id),
        correlation_id=generate_uuid7(),
    )
    assert engine.evaluate(req_conv).is_allowed is False


def test_wrong_role_student_cannot_act_as_staff_or_admin():
    student = make_actor(IdentityRole.STUDENT)
    student_engine = StudentPolicyEngine()

    for forbidden_action in [
        "ticket.update",
        "booking.approve",
        "knowledge.publish",
        "system.config.manage",
    ]:
        req = PolicyEvaluationRequest(
            actor=student,
            action=forbidden_action,
            resource_type="generic",
            correlation_id=generate_uuid7(),
        )
        res = student_engine.evaluate(req)
        assert res.is_allowed is False


def test_wrong_role_staff_cross_boundaries():
    staff_engine = StaffPolicyEngine()

    officer = make_actor(IdentityRole.SUPPORT_OFFICER, unit_ids=("QUEUE_A",))
    know_admin = make_actor(IdentityRole.KNOWLEDGE_ADMIN)
    sys_admin = make_actor(IdentityRole.SYSTEM_ADMIN)

    # Officer cannot publish knowledge
    req_pub = PolicyEvaluationRequest(actor=officer, action="knowledge.publish", resource_type="knowledge", correlation_id=generate_uuid7())
    assert staff_engine.evaluate(req_pub).is_allowed is False

    # Knowledge admin cannot read tickets
    req_ticket = PolicyEvaluationRequest(actor=know_admin, action="ticket.read", resource_type="ticket", resource=PolicyResourceContext(assigned_unit_id="QUEUE_A"), correlation_id=generate_uuid7())
    assert staff_engine.evaluate(req_ticket).is_allowed is False

    # System admin cannot view student private ticket/conversation content
    req_sys = PolicyEvaluationRequest(actor=sys_admin, action="ticket.read", resource_type="ticket", correlation_id=generate_uuid7())
    assert staff_engine.evaluate(req_sys).is_allowed is False
