from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
import sys
import pytest

ROOT = Path(__file__).resolve().parents[3]
API_SRC = ROOT / "services" / "api" / "src"
if str(API_SRC) not in sys.path:
    sys.path.insert(0, str(API_SRC))

from campus247.domain.shared.values import generate_uuid7
from campus247.ports.identity import IdentityContext, IdentityRole, AccountState


def test_identity_context_creation_valid() -> None:
    now = datetime.now(timezone.utc)
    ctx = IdentityContext(
        subject_id=generate_uuid7(),
        external_subject="syn_student_001",
        issuer="urn:campus247:issuer:synthetic",
        roles=(IdentityRole.STUDENT,),
        display_name="Nguyen Van A",
        email="sv240001@demo.huce.example",
        auth_time=now,
        expires_at=now + timedelta(hours=1),
        is_synthetic=True,
        student_code="SYN240001",
        faculty_code="FIT",
    )
    assert ctx.is_authenticated is True
    assert ctx.is_active is True
    assert ctx.has_role(IdentityRole.STUDENT) is True
    assert ctx.has_role(IdentityRole.SYSTEM_ADMIN) is False


def test_identity_context_immutable() -> None:
    now = datetime.now(timezone.utc)
    ctx = IdentityContext(
        subject_id=generate_uuid7(),
        external_subject="syn_staff_001",
        issuer="urn:campus247:issuer:synthetic",
        roles=(IdentityRole.SUPPORT_OFFICER,),
        display_name="Can Bo 1",
        auth_time=now,
        expires_at=now + timedelta(hours=1),
    )
    with pytest.raises(Exception):
        ctx.roles = (IdentityRole.SYSTEM_ADMIN,)  # type: ignore[misc]


def test_identity_context_validation_failures() -> None:
    now = datetime.now(timezone.utc)
    # Student role requires student_code
    with pytest.raises(ValueError, match="student_code"):
        IdentityContext(
            subject_id=generate_uuid7(),
            external_subject="syn_student_002",
            issuer="urn:campus247:issuer:synthetic",
            roles=(IdentityRole.STUDENT,),
            display_name="Nguyen Van B",
            auth_time=now,
            expires_at=now + timedelta(hours=1),
            student_code=None,
        )

    # Expired token
    with pytest.raises(ValueError, match="expires_at"):
        IdentityContext(
            subject_id=generate_uuid7(),
            external_subject="syn_student_003",
            issuer="urn:campus247:issuer:synthetic",
            roles=(IdentityRole.STUDENT,),
            display_name="Nguyen Van C",
            auth_time=now,
            expires_at=now - timedelta(minutes=1),
            student_code="SYN240003",
        )
