from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime, timezone
from typing import Any

from campus247.application.audit.writer import AuditWriter
from campus247.ports.identity import IdentityContext, IdentityRole


@dataclass
class DocumentVersionRecord:
    id: str
    knowledge_source_id: str
    version_label: str
    content_checksum: str
    status: str
    created_by: str
    supersedes_version_id: str | None = None
    published_at: datetime | None = None
    published_by: str | None = None
    effective_from: datetime | None = None
    effective_until: datetime | None = None
    version: int = 1


@dataclass(frozen=True)
class PublishKnowledgeVersionCommand:
    version_id: str
    expected_checksum: str
    supersedes_version_id: str | None = None
    effective_from: datetime | None = None
    effective_until: datetime | None = None


@dataclass(frozen=True)
class PublishResult:
    version_id: str
    version: DocumentVersionRecord
    superseded_version_id: str | None = None


class KnowledgePublishService:
    def __init__(self, audit_writer: AuditWriter | None = None) -> None:
        self._audit_writer = audit_writer or AuditWriter()
        self._versions: dict[str, DocumentVersionRecord] = {}

    def register_version(self, record: DocumentVersionRecord) -> None:
        self._versions[record.id] = record

    def get_version(self, version_id: str) -> DocumentVersionRecord | None:
        return self._versions.get(version_id)

    def publish_version(
        self,
        approver: IdentityContext,
        cmd: PublishKnowledgeVersionCommand,
    ) -> PublishResult:
        if not (approver.has_role(IdentityRole.KNOWLEDGE_ADMIN) or approver.has_role(IdentityRole.SYSTEM_ADMIN)):
            raise PermissionError("Approver requires KNOWLEDGE_ADMIN role")

        if cmd.version_id not in self._versions:
            raise KeyError(f"Document version {cmd.version_id} not found")

        target = self._versions[cmd.version_id]

        if target.status != "DRAFT":
            raise ValueError(f"Only DRAFT versions can be published, got {target.status}")

        # Four-eyes / Dual-review check (SEC-CTRL-012, REQ-F-KNOW-006)
        if target.created_by == approver.subject_id:
            raise PermissionError("Separation of duties violation: editor cannot approve or publish their own draft")

        # Content hash verification (REQ-F-KNOW-005)
        if cmd.expected_checksum != target.content_checksum:
            raise ValueError(
                f"Checksum mismatch: expected '{cmd.expected_checksum}', actual '{target.content_checksum}'"
            )

        # Predecessor / Supersedes check (REQ-F-KNOW-008, REQ-F-KNOW-009)
        superseded_id = cmd.supersedes_version_id
        if superseded_id:
            if superseded_id == target.id:
                raise ValueError("Version cannot supersede itself")
            if superseded_id not in self._versions:
                raise KeyError(f"Predecessor version {superseded_id} not found")
            predecessor = self._versions[superseded_id]
            if predecessor.knowledge_source_id != target.knowledge_source_id:
                raise ValueError("Superseded version must belong to the same knowledge source")
            # Retire predecessor
            predecessor.status = "SUPERSEDED"
            predecessor.version += 1

        now = datetime.now(timezone.utc)
        target.status = "PUBLISHED"
        target.published_by = approver.subject_id
        target.published_at = now
        target.supersedes_version_id = superseded_id
        target.effective_from = cmd.effective_from or now
        target.effective_until = cmd.effective_until
        target.version += 1

        self._audit_writer.record_event(
            actor_type="KNOWLEDGE_ADMIN",
            actor_id=approver.subject_id,
            action_code="knowledge.version_publish",
            resource_type="document_version",
            resource_id=target.id,
            outcome="SUCCESS",
            metadata={
                "knowledge_source_id": target.knowledge_source_id,
                "checksum": target.content_checksum,
                "supersedes": superseded_id,
            },
        )

        return PublishResult(version_id=target.id, version=target, superseded_version_id=superseded_id)
