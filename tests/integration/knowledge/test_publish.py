from __future__ import annotations

from datetime import datetime, timezone, timedelta
import pytest

from campus247.application.audit.writer import AuditWriter
from campus247.application.knowledge.publish import (
    DocumentVersionRecord,
    KnowledgePublishService,
    PublishKnowledgeVersionCommand,
    PublishResult,
)
from campus247.domain.shared.values import generate_uuid7
from campus247.ports.identity import IdentityContext, IdentityRole


def make_admin(user_id: str | None = None, role: IdentityRole = IdentityRole.KNOWLEDGE_ADMIN) -> IdentityContext:
    now = datetime.now(timezone.utc)
    uid = user_id or generate_uuid7()
    return IdentityContext(
        subject_id=uid,
        external_subject=f"sub-{uid[:8]}",
        issuer="https://auth.huce.edu.vn",
        roles=(role,),
        display_name=f"Admin {uid[:4]}",
        auth_time=now,
        expires_at=now + timedelta(hours=1),
    )


@pytest.fixture
def service() -> KnowledgePublishService:
    audit = AuditWriter()
    return KnowledgePublishService(audit_writer=audit)


def test_publish_knowledge_version_success(service: KnowledgePublishService):
    creator = make_admin()
    approver = make_admin()
    source_id = generate_uuid7()
    checksum = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"

    version = DocumentVersionRecord(
        id=generate_uuid7(),
        knowledge_source_id=source_id,
        version_label="1.0.0",
        content_checksum=checksum,
        status="DRAFT",
        created_by=creator.subject_id,
    )
    service.register_version(version)

    cmd = PublishKnowledgeVersionCommand(
        version_id=version.id,
        expected_checksum=checksum,
    )

    result = service.publish_version(approver, cmd)
    assert isinstance(result, PublishResult)
    assert result.version.status == "PUBLISHED"
    assert result.version.published_by == approver.subject_id
    assert result.version.published_at is not None

    stored = service.get_version(version.id)
    assert stored.status == "PUBLISHED"


def test_publish_self_approval_denied_separation_of_duties(service: KnowledgePublishService):
    creator = make_admin()
    source_id = generate_uuid7()
    checksum = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"

    version = DocumentVersionRecord(
        id=generate_uuid7(),
        knowledge_source_id=source_id,
        version_label="1.0.0",
        content_checksum=checksum,
        status="DRAFT",
        created_by=creator.subject_id,
    )
    service.register_version(version)

    cmd = PublishKnowledgeVersionCommand(
        version_id=version.id,
        expected_checksum=checksum,
    )

    with pytest.raises(PermissionError, match="Separation of duties violation"):
        service.publish_version(creator, cmd)


def test_publish_checksum_mismatch_rejected(service: KnowledgePublishService):
    creator = make_admin()
    approver = make_admin()
    source_id = generate_uuid7()

    version = DocumentVersionRecord(
        id=generate_uuid7(),
        knowledge_source_id=source_id,
        version_label="1.0.0",
        content_checksum="correct-sha256-hash",
        status="DRAFT",
        created_by=creator.subject_id,
    )
    service.register_version(version)

    cmd = PublishKnowledgeVersionCommand(
        version_id=version.id,
        expected_checksum="tampered-sha256-hash",
    )

    with pytest.raises(ValueError, match="Checksum mismatch"):
        service.publish_version(approver, cmd)


def test_publish_supersedes_transition(service: KnowledgePublishService):
    creator = make_admin()
    approver = make_admin()
    source_id = generate_uuid7()

    v1 = DocumentVersionRecord(
        id=generate_uuid7(),
        knowledge_source_id=source_id,
        version_label="1.0.0",
        content_checksum="hash-v1",
        status="PUBLISHED",
        created_by=creator.subject_id,
    )
    v2 = DocumentVersionRecord(
        id=generate_uuid7(),
        knowledge_source_id=source_id,
        version_label="2.0.0",
        content_checksum="hash-v2",
        status="DRAFT",
        created_by=creator.subject_id,
    )
    service.register_version(v1)
    service.register_version(v2)

    cmd = PublishKnowledgeVersionCommand(
        version_id=v2.id,
        expected_checksum="hash-v2",
        supersedes_version_id=v1.id,
    )

    result = service.publish_version(approver, cmd)
    assert result.version.status == "PUBLISHED"

    # Predecessor superseded
    old_v1 = service.get_version(v1.id)
    assert old_v1.status == "SUPERSEDED"


def test_publish_cyclic_supersedes_rejected(service: KnowledgePublishService):
    creator = make_admin()
    approver = make_admin()
    source_id = generate_uuid7()
    v_id = generate_uuid7()

    v = DocumentVersionRecord(
        id=v_id,
        knowledge_source_id=source_id,
        version_label="1.0.0",
        content_checksum="hash-v1",
        status="DRAFT",
        created_by=creator.subject_id,
    )
    service.register_version(v)

    cmd = PublishKnowledgeVersionCommand(
        version_id=v_id,
        expected_checksum="hash-v1",
        supersedes_version_id=v_id,
    )

    with pytest.raises(ValueError, match="cannot supersede itself"):
        service.publish_version(approver, cmd)
