from __future__ import annotations

from campus247.ports.identity import IdentityRole
from campus247.ports.policy import (
    AuthorizationPolicyPort,
    PolicyDecision,
    PolicyDecisionResult,
    PolicyEvaluationRequest,
)


class StudentPolicyEngine(AuthorizationPolicyPort):
    def evaluate(self, request: PolicyEvaluationRequest) -> PolicyDecisionResult:
        if not request.actor.has_role(IdentityRole.STUDENT):
            return PolicyDecisionResult(
                decision=PolicyDecision.DENY,
                policy_id="SEC-AUTHZ-ROLE",
                reason_code="ROLE_NOT_STUDENT",
            )

        action = request.action.lower()

        # Public search/FAQ actions allowed
        if action in ("faq.search", "corpus.search"):
            return PolicyDecisionResult(
                decision=PolicyDecision.ALLOW,
                policy_id="SEC-AUTHZ-PUBLIC",
                reason_code="PUBLIC_ACCESS",
            )

        # Student personal resource reads require ownership
        if action in ("profile.read", "schedule.read", "ticket.read", "conversation.read"):
            if request.resource and request.resource.owner_subject_id == request.actor.subject_id:
                return PolicyDecisionResult(
                    decision=PolicyDecision.ALLOW,
                    policy_id="SEC-AUTHZ-002",
                    reason_code="OWNER_ALLOWED",
                )
            return PolicyDecisionResult(
                decision=PolicyDecision.DENY,
                policy_id="SEC-AUTHZ-002",
                reason_code="OWNERSHIP_REQUIRED",
            )

        # Student mutation requests require ownership and confirmation
        if action in ("ticket.create", "docreq.create", "booking.create", "ticket.close"):
            if request.resource and request.resource.owner_subject_id == request.actor.subject_id:
                return PolicyDecisionResult(
                    decision=PolicyDecision.ALLOW,
                    policy_id="SEC-AUTHZ-005",
                    reason_code="STUDENT_ACTION_ALLOWED",
                    obligations=("require_confirmation",),
                )
            return PolicyDecisionResult(
                decision=PolicyDecision.DENY,
                policy_id="SEC-AUTHZ-005",
                reason_code="OWNERSHIP_REQUIRED",
            )

        # Default deny all other actions for students
        return PolicyDecisionResult(
            decision=PolicyDecision.DENY,
            policy_id="SEC-AUTHZ-DENY",
            reason_code="ACTION_NOT_PERMITTED_FOR_STUDENT",
        )
