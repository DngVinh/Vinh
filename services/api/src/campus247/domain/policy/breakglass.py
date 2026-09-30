from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from campus247.ports.identity import IdentityRole
from campus247.ports.policy import (
    AuthorizationPolicyPort,
    PolicyDecision,
    PolicyDecisionResult,
    PolicyEvaluationRequest,
)
from campus247.ports.contact import AlertPort

@dataclass(frozen=True)
class BreakglassGrant:
    grant_id: str
    subject_id: str
    action: str
    reason: str
    expires_at: datetime
    
    @property
    def is_expired(self) -> bool:
        return datetime.now(timezone.utc) > self.expires_at

class BreakglassPolicyEngine:
    def __init__(self, alert_port: AlertPort):
        self.alert_port = alert_port

    def evaluate(
        self, request: PolicyEvaluationRequest, grant: BreakglassGrant | None = None
    ) -> PolicyDecisionResult:
        if not grant:
            return PolicyDecisionResult(
                decision=PolicyDecision.DENY,
                policy_id="SEC-AUTHZ-BREAKGLASS",
                reason_code="NO_BREAKGLASS_GRANT"
            )
            
        if IdentityRole.STUDENT in request.actor.roles and len(request.actor.roles) == 1:
            # We deny student, but let's check properly: if not staff.
            pass
        
        # Proper check for not staff
        staff_roles = {IdentityRole.SYSTEM_ADMIN, IdentityRole.SUPPORT_OFFICER, IdentityRole.KNOWLEDGE_ADMIN}
        if not any(r in staff_roles for r in request.actor.roles):
            return PolicyDecisionResult(
                decision=PolicyDecision.DENY,
                policy_id="SEC-AUTHZ-BREAKGLASS",
                reason_code="NOT_STAFF"
            )

        if not request.purpose:
            return PolicyDecisionResult(
                decision=PolicyDecision.DENY,
                policy_id="SEC-AUTHZ-BREAKGLASS",
                reason_code="MISSING_PURPOSE"
            )

        if grant.is_expired:
            return PolicyDecisionResult(
                decision=PolicyDecision.DENY,
                policy_id="SEC-AUTHZ-BREAKGLASS",
                reason_code="GRANT_EXPIRED"
            )
            
        if grant.subject_id != request.actor.subject_id:
            return PolicyDecisionResult(
                decision=PolicyDecision.DENY,
                policy_id="SEC-AUTHZ-BREAKGLASS",
                reason_code="ACTOR_MISMATCH"
            )
            
        if grant.action != request.action:
            return PolicyDecisionResult(
                decision=PolicyDecision.DENY,
                policy_id="SEC-AUTHZ-BREAKGLASS",
                reason_code="ACTION_MISMATCH"
            )
            
        self.alert_port.emit_operational_alert(
            "SEC-BREAKGLASS-ACCESSED",
            f"Breakglass accessed by {request.actor.subject_id} for action {request.action} with reason: {request.purpose}"
        )

        return PolicyDecisionResult(
            decision=PolicyDecision.ALLOW,
            policy_id="SEC-AUTHZ-BREAKGLASS",
            reason_code="BREAKGLASS_GRANTED"
        )
