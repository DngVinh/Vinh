from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
import sys
import pytest

ROOT = Path(__file__).resolve().parents[3]
API_SRC = ROOT / "services" / "api" / "src"
if str(API_SRC) not in sys.path:
    sys.path.insert(0, str(API_SRC))

from campus247.domain.shared.values import generate_uuid7
from campus247.ports.identity import IdentityContext, IdentityRole
from campus247.ports.policy import (
    AuthorizationPolicyPort,
    PolicyDecision,
    PolicyDecisionResult,
    PolicyEvaluationRequest,
    PolicyResourceContext,
)


def test_policy_decision_result_attributes() -> None:
    res = PolicyDecisionResult(
        decision=PolicyDecision.ALLOW,
        policy_id="SEC-AUTHZ-001",
        reason_code="OWNER_ALLOWED",
        obligations=("audit:high",),
    )
    assert res.is_allowed is True
    assert res.decision == PolicyDecision.ALLOW
    assert "audit:high" in res.obligations


def test_deny_by_default_policy() -> None:
    now = datetime.now(timezone.utc)
    actor = IdentityContext(
        subject_id=generate_uuid7(),
        external_subject="syn_01",
        issuer="urn:campus247:issuer:synthetic",
        roles=(IdentityRole.STUDENT,),
        display_name="Student A",
        auth_time=now,
        expires_at=now + timedelta(hours=1),
        student_code="SYN12345678",
    )
    req = PolicyEvaluationRequest(
        actor=actor,
        action="ticket.read",
        resource_type="ticket",
        resource=PolicyResourceContext(owner_subject_id=generate_uuid7()),
        correlation_id=generate_uuid7(),
    )

    # Simple mock policy port conforming to protocol
    class DefaultDenyPolicyEngine(AuthorizationPolicyPort):
        def evaluate(self, request: PolicyEvaluationRequest) -> PolicyDecisionResult:
            if request.resource and request.resource.owner_subject_id == request.actor.subject_id:
                return PolicyDecisionResult(
                    decision=PolicyDecision.ALLOW,
                    policy_id="SEC-AUTHZ-OWNER",
                    reason_code="OWNER_ACCESS",
                )
            return PolicyDecisionResult(
                decision=PolicyDecision.DENY,
                policy_id="SEC-AUTHZ-DEFAULT",
                reason_code="DEFAULT_DENY",
            )

    engine = DefaultDenyPolicyEngine()
    decision = engine.evaluate(req)
    assert decision.is_allowed is False
    assert decision.decision == PolicyDecision.DENY
    assert decision.reason_code == "DEFAULT_DENY"
