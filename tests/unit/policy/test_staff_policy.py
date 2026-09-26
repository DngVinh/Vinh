from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
import sys
import pytest

ROOT = Path(__file__).resolve().parents[3]
API_SRC = ROOT / "services" / "api" / "src"
if str(API_SRC) not in sys.path:
    sys.path.insert(0, str(API_SRC))

from campus247.domain.policy.staff import StaffPolicyEngine
from campus247.domain.shared.values import generate_uuid7
from campus247.ports.identity import IdentityContext, IdentityRole
from campus247.ports.policy import (
    PolicyDecision,
    PolicyEvaluationRequest,
    PolicyResourceContext,
)


@pytest.fixture
def support_officer_actor():
    now = datetime.now(timezone.utc)
    uid = generate_uuid7()
    return IdentityContext(
        subject_id=uid,
        external_subject=f"syn_{uid}",
        issuer="urn:campus247:issuer:synthetic",
        roles=(IdentityRole.SUPPORT_OFFICER,),
        display_name="Can Bo Support",
        auth_time=now,
        expires_at=now + timedelta(hours=1),
        unit_ids=("FIT_QUEUE", "GENERAL_QUEUE"),
    )


def test_support_officer_can_access_ticket_in_assigned_queue(support_officer_actor):
    engine = StaffPolicyEngine()
    req = PolicyEvaluationRequest(
        actor=support_officer_actor,
        action="ticket.read",
        resource_type="ticket",
        resource=PolicyResourceContext(assigned_unit_id="FIT_QUEUE"),
        correlation_id=generate_uuid7(),
    )
    res = engine.evaluate(req)
    assert res.is_allowed is True
    assert res.decision == PolicyDecision.ALLOW
    assert res.reason_code == "QUEUE_SCOPE_MATCHED"


def test_support_officer_cannot_access_ticket_outside_assigned_queue(support_officer_actor):
    engine = StaffPolicyEngine()
    req = PolicyEvaluationRequest(
        actor=support_officer_actor,
        action="ticket.read",
        resource_type="ticket",
        resource=PolicyResourceContext(assigned_unit_id="FINANCE_QUEUE"),
        correlation_id=generate_uuid7(),
    )
    res = engine.evaluate(req)
    assert res.is_allowed is False
    assert res.decision == PolicyDecision.DENY
    assert res.reason_code == "QUEUE_SCOPE_MISMATCH"


def test_support_officer_cannot_manage_system_config(support_officer_actor):
    engine = StaffPolicyEngine()
    req = PolicyEvaluationRequest(
        actor=support_officer_actor,
        action="system.config.write",
        resource_type="config",
        correlation_id=generate_uuid7(),
    )
    res = engine.evaluate(req)
    assert res.is_allowed is False
    assert res.decision == PolicyDecision.DENY
