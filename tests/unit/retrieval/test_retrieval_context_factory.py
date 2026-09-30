from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from campus247.application.retrieval.context import (
    ResolvedRetrievalScope,
    RetrievalContextError,
    RetrievalContextFactory,
)
from campus247.domain.retrieval import SimulationPolicy
from campus247.domain.shared.values import generate_uuid7
from campus247.ports.identity import AccountState, IdentityContext, IdentityRole


NOW = datetime(2026, 9, 29, 12, 0, tzinfo=timezone.utc)


class StaticTrustedScopeResolver:
    def __init__(self, scope: ResolvedRetrievalScope) -> None:
        self.scope = scope

    def resolve(self, identity: IdentityContext) -> ResolvedRetrievalScope:
        assert identity.subject_id
        return self.scope


def identity(**overrides: object) -> IdentityContext:
    values: dict[str, object] = {
        "subject_id": generate_uuid7(),
        "external_subject": "verified-subject",
        "issuer": "urn:campus247:issuer:synthetic",
        "roles": (IdentityRole.STUDENT,),
        "display_name": "Synthetic Student",
        "auth_time": NOW - timedelta(minutes=5),
        "expires_at": NOW + timedelta(hours=1),
        "tenant_id": "tenant-huce",
        "student_code": "SYN001",
        "faculty_code": "FIT",
        "is_synthetic": True,
    }
    values.update(overrides)
    return IdentityContext(**values)  # type: ignore[arg-type]


def factory(scope: ResolvedRetrievalScope | None = None) -> RetrievalContextFactory:
    return RetrievalContextFactory(
        scope_resolver=StaticTrustedScopeResolver(
            scope
            or ResolvedRetrievalScope(
                tenant_id="tenant-huce",
                campus_id="HUCE",
                audiences=frozenset({"STUDENT"}),
                faculty_codes=frozenset({"FIT"}),
                program_codes=frozenset({"SOFTWARE_ENGINEERING"}),
            )
        ),
        configured_tenant_id="tenant-huce",
        configured_campus_id="HUCE",
    )


def test_factory_uses_only_verified_identity_and_resolved_scope() -> None:
    actor = identity()
    context = factory().create(
        actor,
        effective_at=NOW,
        locale="vi",
        trace_id="trace-001",
        allow_simulation=True,
    )

    assert context.authorized_scope.actor_id == actor.subject_id
    assert context.authorized_scope.roles == frozenset({"STUDENT"})
    assert context.authorized_scope.faculty_codes == frozenset({"FIT"})
    assert context.simulation_policy is SimulationPolicy.ALLOW_LABELED


def test_request_controlled_authorization_fields_are_not_accepted() -> None:
    with pytest.raises(TypeError):
        factory().create(
            identity(),
            effective_at=NOW,
            locale="vi",
            trace_id="trace-001",
            role="SYSTEM_ADMIN",  # type: ignore[call-arg]
            tenant_id="other-tenant",  # type: ignore[call-arg]
        )


def test_missing_or_inactive_identity_fails_closed() -> None:
    with pytest.raises(RetrievalContextError, match="verified identity"):
        factory().create(None, effective_at=NOW, locale="vi", trace_id="trace-001")  # type: ignore[arg-type]
    with pytest.raises(RetrievalContextError, match="active"):
        factory().create(
            identity(account_state=AccountState.SUSPENDED),
            effective_at=NOW,
            locale="vi",
            trace_id="trace-001",
        )


def test_expired_identity_and_tenant_crossing_fail_closed() -> None:
    with pytest.raises(RetrievalContextError, match="expired"):
        factory().create(
            identity(expires_at=NOW),
            effective_at=NOW,
            locale="vi",
            trace_id="trace-001",
        )

    crossed = ResolvedRetrievalScope(
        tenant_id="other-tenant",
        campus_id="OTHER",
        audiences=frozenset({"STUDENT"}),
        faculty_codes=frozenset({"FIT"}),
        program_codes=frozenset({"SOFTWARE_ENGINEERING"}),
    )
    with pytest.raises(RetrievalContextError, match="crosses"):
        factory(crossed).create(
            identity(),
            effective_at=NOW,
            locale="vi",
            trace_id="trace-001",
        )


def test_real_identity_cannot_enable_simulation() -> None:
    context = factory().create(
        identity(is_synthetic=False),
        effective_at=NOW,
        locale="vi",
        trace_id="trace-001",
        allow_simulation=True,
    )
    assert context.simulation_policy is SimulationPolicy.DENY
