from __future__ import annotations

from pathlib import Path
import sys
import pytest

ROOT = Path(__file__).resolve().parents[3]
API_SRC = ROOT / "services" / "api" / "src"
if str(API_SRC) not in sys.path:
    sys.path.insert(0, str(API_SRC))

from campus247.application.audit.writer import AuditEventRecord, AuditWriter
from campus247.domain.shared.values import generate_uuid7


def test_write_audit_event_success():
    writer = AuditWriter()
    actor_id = generate_uuid7()
    resource_id = generate_uuid7()

    evt = writer.record_event(
        actor_type="USER",
        actor_id=actor_id,
        action_code="ticket.create",
        resource_type="ticket",
        resource_id=resource_id,
        outcome="SUCCESS",
        metadata={"subject": "Request paper", "doc_code": "D-1"},
    )

    assert evt.id is not None
    assert evt.actor_id == actor_id
    assert evt.outcome == "SUCCESS"
    assert evt.metadata_safe is not None
    assert "doc_code" in evt.metadata_safe


def test_audit_writer_redacts_sensitive_fields():
    writer = AuditWriter()
    actor_id = generate_uuid7()

    evt = writer.record_event(
        actor_type="USER",
        actor_id=actor_id,
        action_code="auth.login",
        resource_type="session",
        resource_id=None,
        outcome="SUCCESS",
        metadata={
            "token": "secret_jwt_token",
            "password": "raw_password",
            "safe_cohort": 2024,
        },
    )

    assert "safe_cohort" in evt.metadata_safe
    assert "token" not in evt.metadata_safe
    assert "password" not in evt.metadata_safe


def test_audit_log_append_only():
    writer = AuditWriter()
    evt1 = writer.record_event("USER", generate_uuid7(), "action.1", "res.1", None, "SUCCESS")
    evt2 = writer.record_event("USER", generate_uuid7(), "action.2", "res.2", None, "SUCCESS")

    history = writer.get_history()
    assert len(history) == 2
    assert history[0].id == evt1.id
    assert history[1].id == evt2.id
