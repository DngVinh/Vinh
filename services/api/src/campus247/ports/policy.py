from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Protocol

from campus247.ports.identity import IdentityContext


class PolicyDecision(StrEnum):
    ALLOW = "allow"
    DENY = "deny"


@dataclass(frozen=True)
class PolicyResourceContext:
    owner_subject_id: str | None = None
    assigned_unit_id: str | None = None
    classification: str | None = None
    state: str | None = None


@dataclass(frozen=True)
class PolicyEvaluationRequest:
    actor: IdentityContext
    action: str
    resource_type: str
    correlation_id: str
    resource: PolicyResourceContext | None = None
    purpose: str | None = None
    environment: str = "local"


@dataclass(frozen=True)
class PolicyDecisionResult:
    decision: PolicyDecision
    policy_id: str
    reason_code: str
    obligations: tuple[str, ...] = ()

    @property
    def is_allowed(self) -> bool:
        return self.decision == PolicyDecision.ALLOW


class AuthorizationPolicyPort(Protocol):
    def evaluate(self, request: PolicyEvaluationRequest) -> PolicyDecisionResult:
        ...
