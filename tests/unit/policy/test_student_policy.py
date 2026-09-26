from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
import sys
import pytest

ROOT = Path(__file__).resolve().parents[3]
API_SRC = ROOT / "services" / "api" / "src"
if str(API_SRC) not in sys.path:
    sys.path.insert(0, str(API_SRC))

from campus247.domain.policy.student import StudentPolicyEngine
from campus247.domain.shared.values import generate_uuid7
from campus247.ports.identity import IdentityContext, IdentityRole
from campus247.ports.policy import (
    PolicyDecision,
    PolicyEvaluationRequest,
    PolicyResourceContext,
)


@pytest.fixture
def student_actor():
    now = datetime.now(timezone.utc)
    uid = generate_uuid7()
    return IdentityContext(
        subject_id=uid,
        external_subject=f"syn_{uid}",
        issuer="urn:campus247:issuer:synthetic",
        roles=(IdentityRole.STUDENT,),
        display_name="Nguyen Van Student",
        auth_time=now,
        expires_at=now + timedelta(hours=1),
        student_code="SYN240001",
    )


def test_student_can_read_own_ticket(student_actor):
    engine = StudentPolicyEngine()
    req = PolicyEvaluationRequest(
        actor=student_actor,
        action="ticket.read",
        resource_type="ticket",
        resource=PolicyResourceContext(owner_subject_id=student_actor.subject_id),
        correlation_id=generate_uuid7(),
    )
    res = engine.evaluate(req)
    assert res.is_allowed is True
    assert res.decision == PolicyDecision.ALLOW
    assert res.reason_code == "OWNER_ALLOWED"


def test_student_cannot_read_other_student_ticket(student_actor):
    engine = StudentPolicyEngine()
    req = PolicyEvaluationRequest(
        actor=student_actor,
        action="ticket.read",
        resource_type="ticket",
        resource=PolicyResourceContext(owner_subject_id=generate_uuid7()),
        correlation_id=generate_uuid7(),
    )
    res = engine.evaluate(req)
    assert res.is_allowed is False
    assert res.decision == PolicyDecision.DENY
    assert res.reason_code == "OWNERSHIP_REQUIRED"


def test_student_cannot_perform_admin_action(student_actor):
    engine = StudentPolicyEngine()
    req = PolicyEvaluationRequest(
        actor=student_actor,
        action="app.config.manage",
        resource_type="system_config",
        correlation_id=generate_uuid7(),
    )
    res = engine.evaluate(req)
    assert res.is_allowed is False
    assert res.decision == PolicyDecision.DENY
