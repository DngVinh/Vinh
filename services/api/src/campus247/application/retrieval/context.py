from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Protocol

from campus247.domain.retrieval import AuthorizedScope, RetrievalContext, SimulationPolicy
from campus247.ports.identity import AccountState, IdentityContext


class RetrievalContextError(ValueError):
    """Raised when trusted retrieval context cannot be established."""


@dataclass(frozen=True)
class ResolvedRetrievalScope:
    tenant_id: str
    campus_id: str
    audiences: frozenset[str]
    faculty_codes: frozenset[str]
    program_codes: frozenset[str]


class TrustedScopeResolver(Protocol):
    def resolve(self, identity: IdentityContext) -> ResolvedRetrievalScope:
        ...


class RetrievalContextFactory:
    """Builds authorization scope only from verified identity and server-side data."""

    def __init__(
        self,
        *,
        scope_resolver: TrustedScopeResolver,
        configured_tenant_id: str,
        configured_campus_id: str,
    ) -> None:
        self._scope_resolver = scope_resolver
        self._tenant_id = configured_tenant_id.strip()
        self._campus_id = configured_campus_id.strip()
        if not self._tenant_id or not self._campus_id:
            raise RetrievalContextError("configured tenant and campus are required")

    def create(
        self,
        identity: IdentityContext,
        *,
        effective_at: datetime,
        locale: str,
        trace_id: str,
        allow_simulation: bool = False,
    ) -> RetrievalContext:
        if not isinstance(identity, IdentityContext):
            raise RetrievalContextError("verified identity is required")
        if identity.account_state is not AccountState.ACTIVE:
            raise RetrievalContextError("identity must be active")
        if effective_at.tzinfo is None or effective_at.utcoffset() is None:
            raise RetrievalContextError("effective_at must be timezone-aware")

        at_utc = effective_at.astimezone(timezone.utc)
        if identity.expires_at.astimezone(timezone.utc) <= at_utc:
            raise RetrievalContextError("identity session is expired")
        if not identity.roles:
            raise RetrievalContextError("identity roles are required")

        resolved = self._scope_resolver.resolve(identity)
        identity_tenant = (identity.tenant_id or "").strip()
        if not identity_tenant or identity_tenant != self._tenant_id:
            raise RetrievalContextError("identity tenant does not match configured tenant")
        if resolved.tenant_id != self._tenant_id or resolved.campus_id != self._campus_id:
            raise RetrievalContextError("resolved scope crosses the configured tenant or campus")
        if identity.faculty_code and identity.faculty_code not in resolved.faculty_codes:
            raise RetrievalContextError("resolved scope does not contain the trusted faculty claim")

        return RetrievalContext(
            authorized_scope=AuthorizedScope(
                tenant_id=resolved.tenant_id,
                campus_id=resolved.campus_id,
                actor_id=identity.subject_id,
                roles=frozenset(role.value for role in identity.roles),
                audiences=resolved.audiences,
                faculty_codes=resolved.faculty_codes,
                program_codes=resolved.program_codes,
            ),
            locale=locale,
            effective_at=at_utc,
            simulation_policy=(
                SimulationPolicy.ALLOW_LABELED
                if allow_simulation and identity.is_synthetic
                else SimulationPolicy.DENY
            ),
            trace_id=trace_id,
        )
