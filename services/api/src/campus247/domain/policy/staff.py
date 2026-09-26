from __future__ import annotations

from campus247.ports.identity import IdentityRole
from campus247.ports.policy import (
    AuthorizationPolicyPort,
    PolicyDecision,
    PolicyDecisionResult,
    PolicyEvaluationRequest,
)


class StaffPolicyEngine(AuthorizationPolicyPort):
    def evaluate(self, request: PolicyEvaluationRequest) -> PolicyDecisionResult:
        actor = request.actor
        action = request.action.lower()

        # Public search/FAQ actions allowed for all staff
        if action in ("faq.search", "corpus.search"):
            return PolicyDecisionResult(
                decision=PolicyDecision.ALLOW,
                policy_id="SEC-AUTHZ-PUBLIC",
                reason_code="PUBLIC_ACCESS",
            )

        if actor.has_role(IdentityRole.SUPPORT_OFFICER):
            # Support officer queue-scoped ticket actions
            if action in ("ticket.read", "ticket.update", "ticket.close", "booking.approve"):
                if (
                    request.resource
                    and request.resource.assigned_unit_id
                    and request.resource.assigned_unit_id in actor.unit_ids
                ):
                    return PolicyDecisionResult(
                        decision=PolicyDecision.ALLOW,
                        policy_id="SEC-AUTHZ-003",
                        reason_code="QUEUE_SCOPE_MATCHED",
                    )
                return PolicyDecisionResult(
                    decision=PolicyDecision.DENY,
                    policy_id="SEC-AUTHZ-003",
                    reason_code="QUEUE_SCOPE_MISMATCH",
                )

        if actor.has_role(IdentityRole.KNOWLEDGE_ADMIN):
            # Knowledge admin actions
            if action in ("knowledge.upload", "knowledge.publish", "knowledge.diagnostics"):
                return PolicyDecisionResult(
                    decision=PolicyDecision.ALLOW,
                    policy_id="SEC-AUTHZ-KNOW",
                    reason_code="KNOWLEDGE_ADMIN_ALLOWED",
                )

        if actor.has_role(IdentityRole.SYSTEM_ADMIN):
            # System admin technical actions (no direct access to student private data)
            if action in ("system.config.manage", "system.metrics.view"):
                return PolicyDecisionResult(
                    decision=PolicyDecision.ALLOW,
                    policy_id="SEC-AUTHZ-SYSADMIN",
                    reason_code="SYSTEM_ADMIN_ALLOWED",
                )

        return PolicyDecisionResult(
            decision=PolicyDecision.DENY,
            policy_id="SEC-AUTHZ-DENY",
            reason_code="ACTION_NOT_PERMITTED_FOR_STAFF",
        )
