import pytest
from datetime import datetime, timedelta, timezone

from campus247.domain.policy.breakglass import BreakglassPolicyEngine, BreakglassGrant
from campus247.ports.identity import IdentityContext, IdentityRole, AccountState
from campus247.ports.policy import PolicyEvaluationRequest, PolicyDecision
from campus247.ports.contact import AlertPort

class MockAlertPort(AlertPort):
    def __init__(self):
        self.alerts = []

    def emit_operational_alert(self, code: str, message: str) -> None:
        self.alerts.append((code, message))
    
    def emit_security_alert(self, code: str, message: str) -> None:
        self.alerts.append((code, message))


def create_actor(role: IdentityRole, subject_id="01921a8d-1234-7000-8000-123456789abc") -> IdentityContext:
    return IdentityContext(
        subject_id=subject_id,
        external_subject="ext-123",
        issuer="test-issuer",
        roles=(role,),
        display_name="Test User",
        auth_time=datetime.now(timezone.utc) - timedelta(hours=1),
        expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
        student_code="STUD-123" if role == IdentityRole.STUDENT else None,
    )

def test_breakglass_denies_without_grant():
    actor = create_actor(IdentityRole.SYSTEM_ADMIN)
    engine = BreakglassPolicyEngine(MockAlertPort())
    req = PolicyEvaluationRequest(
        actor=actor,
        action="ticket.read",
        resource_type="ticket",
        correlation_id="corr-1",
        purpose="Emergency debug"
    )
    result = engine.evaluate(req, grant=None)
    assert result.decision == PolicyDecision.DENY
    assert result.reason_code == "NO_BREAKGLASS_GRANT"

def test_breakglass_denies_expired_grant():
    actor = create_actor(IdentityRole.SYSTEM_ADMIN)
    grant = BreakglassGrant("grant-1", actor.subject_id, "ticket.read", "prod issue", datetime.now(timezone.utc) - timedelta(minutes=1))
    engine = BreakglassPolicyEngine(MockAlertPort())
    req = PolicyEvaluationRequest(actor=actor, action="ticket.read", resource_type="ticket", correlation_id="corr-1", purpose="prod issue")
    result = engine.evaluate(req, grant=grant)
    assert result.decision == PolicyDecision.DENY
    assert result.reason_code == "GRANT_EXPIRED"

def test_breakglass_denies_mismatched_actor():
    actor = create_actor(IdentityRole.SYSTEM_ADMIN, subject_id="01921a8d-1234-7000-8000-123456789abc")
    grant = BreakglassGrant("grant-1", "01921a8d-9999-7000-8000-123456789abc", "ticket.read", "prod issue", datetime.now(timezone.utc) + timedelta(minutes=10))
    engine = BreakglassPolicyEngine(MockAlertPort())
    req = PolicyEvaluationRequest(actor=actor, action="ticket.read", resource_type="ticket", correlation_id="corr-1", purpose="prod issue")
    result = engine.evaluate(req, grant=grant)
    assert result.decision == PolicyDecision.DENY
    assert result.reason_code == "ACTOR_MISMATCH"

def test_breakglass_denies_mismatched_action():
    actor = create_actor(IdentityRole.SYSTEM_ADMIN)
    grant = BreakglassGrant("grant-1", actor.subject_id, "ticket.read", "prod issue", datetime.now(timezone.utc) + timedelta(minutes=10))
    engine = BreakglassPolicyEngine(MockAlertPort())
    req = PolicyEvaluationRequest(actor=actor, action="ticket.write", resource_type="ticket", correlation_id="corr-1", purpose="prod issue")
    result = engine.evaluate(req, grant=grant)
    assert result.decision == PolicyDecision.DENY
    assert result.reason_code == "ACTION_MISMATCH"

def test_breakglass_denies_missing_reason():
    actor = create_actor(IdentityRole.SYSTEM_ADMIN)
    grant = BreakglassGrant("grant-1", actor.subject_id, "ticket.read", "prod issue", datetime.now(timezone.utc) + timedelta(minutes=10))
    engine = BreakglassPolicyEngine(MockAlertPort())
    req = PolicyEvaluationRequest(actor=actor, action="ticket.read", resource_type="ticket", correlation_id="corr-1", purpose=None)
    result = engine.evaluate(req, grant=grant)
    assert result.decision == PolicyDecision.DENY
    assert result.reason_code == "MISSING_PURPOSE"

def test_breakglass_denies_student():
    actor = create_actor(IdentityRole.STUDENT)
    grant = BreakglassGrant("grant-1", actor.subject_id, "ticket.read", "prod issue", datetime.now(timezone.utc) + timedelta(minutes=10))
    engine = BreakglassPolicyEngine(MockAlertPort())
    req = PolicyEvaluationRequest(actor=actor, action="ticket.read", resource_type="ticket", correlation_id="corr-1", purpose="prod issue")
    result = engine.evaluate(req, grant=grant)
    assert result.decision == PolicyDecision.DENY
    assert result.reason_code == "NOT_STAFF"

def test_breakglass_allows_and_alerts():
    actor = create_actor(IdentityRole.SYSTEM_ADMIN)
    grant = BreakglassGrant("grant-1", actor.subject_id, "ticket.read", "prod issue", datetime.now(timezone.utc) + timedelta(minutes=10))
    port = MockAlertPort()
    engine = BreakglassPolicyEngine(port)
    req = PolicyEvaluationRequest(actor=actor, action="ticket.read", resource_type="ticket", correlation_id="corr-1", purpose="prod issue")
    result = engine.evaluate(req, grant=grant)
    
    assert result.decision == PolicyDecision.ALLOW
    assert result.policy_id == "SEC-AUTHZ-BREAKGLASS"
    assert result.reason_code == "BREAKGLASS_GRANTED"
    
    assert len(port.alerts) == 1
    assert port.alerts[0][0] == "SEC-BREAKGLASS-ACCESSED"
