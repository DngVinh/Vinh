from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
import sqlite3
import sys
import pytest

ROOT = Path(__file__).resolve().parents[2]
API_SRC = ROOT / "services" / "api" / "src"
SYNTH_SRC = ROOT / "packages" / "synthetic" / "src"
for p in [API_SRC, SYNTH_SRC]:
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from campus247.domain.actions.confirmation import ConfirmationTokenService
from campus247.application.actions.confirm import (
    ConfirmationExecutionManager,
    ConfirmationReservationService,
    ConfirmationError,
)
from campus247.infrastructure.audit.writer import (
    AppendOnlyAuditWriter,
    AuditPersistenceError,
)


@pytest.fixture
def token_service():
    return ConfirmationTokenService(signing_key="audit-test-key-32b-secret-fixed")


@pytest.fixture
def audit_writer(tmp_path: Path):
    return AppendOnlyAuditWriter(database_path=tmp_path / "audit.sqlite3")


@pytest.fixture
def reservation_service():
    return ConfirmationReservationService()


def test_ac_01_complete_ordered_audit_trail(
    token_service: ConfirmationTokenService,
    reservation_service: ConfirmationReservationService,
    audit_writer: AppendOnlyAuditWriter,
) -> None:
    """AC-TASK-DB-AUDITFIX-001-01: Every attempted controlled write has a complete, ordered audit trail."""
    manager = ConfirmationExecutionManager(
        token_service=token_service,
        reservation_service=reservation_service,
        audit_writer=audit_writer,
    )

    base_time = datetime(2026, 9, 27, 14, 0, 0, tzinfo=timezone.utc)
    payload_hash = token_service.compute_payload_hash({"room": "H1-402"})
    token = token_service.mint_token(
        preview_id="prev-audit-01",
        actor_id="user-stu-1",
        action_type="ROOM_BOOKING",
        payload_hash=payload_hash,
        preview_version=1,
        expires_at=base_time + timedelta(minutes=10),
    )

    executed = False

    def do_action():
        nonlocal executed
        executed = True
        return {"booking_id": "BK-12345"}

    res = manager.execute(
        token=token,
        preview_id="prev-audit-01",
        actor_id="user-stu-1",
        action_type="ROOM_BOOKING",
        payload_hash=payload_hash,
        version=1,
        action_fn=do_action,
        at_time=base_time,
    )
    assert res == {"booking_id": "BK-12345"}
    assert executed is True

    # Inspect audit trail
    records = audit_writer.get_records(preview_id="prev-audit-01")
    assert len(records) == 2
    # Stage 1: RESERVED
    assert records[0].stage == "RESERVED"
    assert records[0].outcome == "SUCCESS"
    assert records[0].sequence_number == 1

    # Stage 2: COMPLETED
    assert records[1].stage == "COMPLETED"
    assert records[1].outcome == "SUCCESS"
    assert records[1].sequence_number == 2

    # Ordered and tamper-evident
    assert audit_writer.verify_integrity() is True


def test_ac_02_audit_failure_blocks_execution_or_fails_closed(
    token_service: ConfirmationTokenService,
    reservation_service: ConfirmationReservationService,
) -> None:
    """AC-TASK-DB-AUDITFIX-001-02: Audit failure cannot be hidden behind a successful response."""
    class FailingAuditWriter(AppendOnlyAuditWriter):
        def append_transition(self, *args, **kwargs):
            raise AuditPersistenceError("Audit storage unreachable")

    failing_writer = FailingAuditWriter()
    manager = ConfirmationExecutionManager(
        token_service=token_service,
        reservation_service=reservation_service,
        audit_writer=failing_writer,
    )

    base_time = datetime(2026, 9, 27, 14, 0, 0, tzinfo=timezone.utc)
    payload_hash = token_service.compute_payload_hash({"room": "H1-402"})
    token = token_service.mint_token(
        preview_id="prev-fail-audit",
        actor_id="user-stu-1",
        action_type="ROOM_BOOKING",
        payload_hash=payload_hash,
        preview_version=1,
        expires_at=base_time + timedelta(minutes=10),
    )

    side_effect_executed = False

    def do_action():
        nonlocal side_effect_executed
        side_effect_executed = True
        return "SUCCESS"

    with pytest.raises(AuditPersistenceError, match="Audit storage unreachable"):
        manager.execute(
            token=token,
            preview_id="prev-fail-audit",
            actor_id="user-stu-1",
            action_type="ROOM_BOOKING",
            payload_hash=payload_hash,
            version=1,
            action_fn=do_action,
            at_time=base_time,
        )

    # Side effect must NEVER execute if initial audit fails
    assert side_effect_executed is False


def test_ac_03_records_exclude_secrets_tokens_prompts(audit_writer: AppendOnlyAuditWriter) -> None:
    """AC-TASK-DB-AUDITFIX-001-03: Records exclude raw tokens, prompts, credentials, and unnecessary personal payloads."""
    raw_token = "ey.bearer.secret.token.999"
    secret_pass = "my-super-secret-password-123"
    llm_prompt = "System prompt with sensitive instructions"

    record = audit_writer.append_transition(
        action_type="SENSITIVE_WRITE",
        actor_id="user-stu-1",
        preview_id="prev-sec-01",
        binding_hash="hash-123",
        stage="RESERVED",
        outcome="SUCCESS",
        metadata={
            "safe_count": 5,
            "token": raw_token,
            "password": secret_pass,
            "prompt": llm_prompt,
            "auth_header": "Bearer " + raw_token,
        },
    )

    # Metadata safe must filter out all sensitive keys
    assert "safe_count" in record.metadata_safe
    assert "token" not in record.metadata_safe
    assert "password" not in record.metadata_safe
    assert "prompt" not in record.metadata_safe
    assert "auth_header" not in record.metadata_safe

    record_str = str(record)
    assert raw_token not in record_str
    assert secret_pass not in record_str
    assert llm_prompt not in record_str


def test_ac_04_audit_records_survive_reopen_and_reject_mutation(tmp_path: Path) -> None:
    """Durability and append-only enforcement survive a writer restart."""
    database_path = tmp_path / "durable-audit.sqlite3"
    first_writer = AppendOnlyAuditWriter(database_path=database_path)
    original = first_writer.append_transition(
        action_type="CONTROLLED_WRITE",
        actor_id="user-stu-1",
        preview_id="prev-durable-01",
        binding_hash="sha256:binding",
        stage="RESERVED",
        outcome="SUCCESS",
        metadata={"safe_code": "CONFIRMATION_ACCEPTED"},
    )

    reopened_writer = AppendOnlyAuditWriter(database_path=database_path)
    reopened = reopened_writer.get_records(preview_id="prev-durable-01")
    assert len(reopened) == 1
    assert reopened[0].record_hash == original.record_hash
    assert reopened_writer.verify_integrity() is True

    with sqlite3.connect(database_path) as connection:
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute("UPDATE audit_record SET outcome = 'TAMPERED'")
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute("DELETE FROM audit_record")
    assert reopened_writer.verify_integrity() is True


def test_production_audit_writer_requires_durable_configuration() -> None:
    with pytest.raises(AuditPersistenceError, match="durable audit storage is required"):
        AppendOnlyAuditWriter(environment="production")
