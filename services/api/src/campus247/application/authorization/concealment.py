

from __future__ import annotations

class ResourceNotFoundError(Exception):
    def __init__(self, message: str = "Tài nguyên không tồn tại"):
        super().__init__(message)


from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from campus247.application.audit.writer import AuditWriter


class AccessDenialReason(StrEnum):
    ABSENT = "ABSENT"
    UNAUTHORIZED_OWNER = "UNAUTHORIZED_OWNER"
    CROSS_TENANT = "CROSS_TENANT"
    PRIVILEGE_INSUFFICIENT = "PRIVILEGE_INSUFFICIENT"


@dataclass(frozen=True)
class ResourceMetadata:
    resource_id: str
    resource_type: str
    owner_id: str
    tenant_id: str


@dataclass(frozen=True)
class ConcealedAccessResult:
    is_accessible: bool
    denial_reason: AccessDenialReason | None = None
    resource_id: str | None = None
    resource_type: str | None = None


class ExistenceConcealmentService:
    """Central policy for existence concealment to prevent object enumeration."""

    def __init__(self, audit_writer: AuditWriter | None = None) -> None:
        self._audit_writer = audit_writer or AuditWriter()
        self._registry: dict[str, ResourceMetadata] = {}

    def register_resource(
        self,
        resource_id: str,
        resource_type: str,
        owner_id: str,
        tenant_id: str = "tenant-huce",
    ) -> None:
        self._registry[resource_id] = ResourceMetadata(
            resource_id=resource_id,
            resource_type=resource_type,
            owner_id=owner_id,
            tenant_id=tenant_id,
        )

    def evaluate_read_access(
        self,
        actor_id: str,
        resource_type: str,
        resource_id: str,
        actor_tenant: str = "tenant-huce",
        is_staff_override: bool = False,
    ) -> ConcealedAccessResult:
        meta = self._registry.get(resource_id)
        if not meta or meta.resource_type != resource_type:
            return ConcealedAccessResult(
                is_accessible=False,
                denial_reason=AccessDenialReason.ABSENT,
                resource_id=resource_id,
                resource_type=resource_type,
            )

        if meta.tenant_id != actor_tenant and not is_staff_override:
            return ConcealedAccessResult(
                is_accessible=False,
                denial_reason=AccessDenialReason.CROSS_TENANT,
                resource_id=resource_id,
                resource_type=resource_type,
            )

        if meta.owner_id != actor_id and not is_staff_override:
            return ConcealedAccessResult(
                is_accessible=False,
                denial_reason=AccessDenialReason.UNAUTHORIZED_OWNER,
                resource_id=resource_id,
                resource_type=resource_type,
            )

        return ConcealedAccessResult(
            is_accessible=True,
            resource_id=resource_id,
            resource_type=resource_type,
        )

    def audit_and_conceal(self, actor_id: str, outcome: ConcealedAccessResult) -> None:
        """Record internal audit event with true denial category, then raise uniform 404."""
        reason_val = outcome.denial_reason.value if outcome.denial_reason else "UNKNOWN"
        self._audit_writer.record_event(
            actor_type="USER",
            actor_id=actor_id,
            action_code="authorization.access_denied",
            resource_type=outcome.resource_type or "resource",
            resource_id=outcome.resource_id or "unknown",
            outcome="DENIED",
            metadata={
                "denial_reason": reason_val,
                "resource_id": outcome.resource_id,
                "resource_type": outcome.resource_type,
            },
        )

        # AC-TASK-API-CONCEAL-001-01: Normalize response to indistinguishable 404
        raise ResourceNotFoundError()
