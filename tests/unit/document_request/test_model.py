from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import sys
import pytest

ROOT = Path(__file__).resolve().parents[3]
API_SRC = ROOT / "services" / "api" / "src"
if str(API_SRC) not in sys.path:
    sys.path.insert(0, str(API_SRC))

from campus247.domain.document_request.model import (
    DocumentDeliveryMethod,
    DocumentRequest,
    DocumentRequestStatus,
    InvalidDocumentRequestStateError,
    InvalidDocumentRequestValidationError,
)


def test_create_valid_document_request():
    now = datetime.now(timezone.utc)
    req = DocumentRequest.create_draft(
        student_user_id="01923456-789a-7def-8123-456789abcdef",
        document_type="STUDENT_CERTIFICATE",
        purpose_code="VISA_APPLICATION",
        delivery_method=DocumentDeliveryMethod.DIGITAL,
    )
    assert req.status == DocumentRequestStatus.DRAFT
    assert req.version == 1
    assert req.is_synthetic is True
    assert req.disclaimer == "DỮ LIỆU MÔ PHỎNG — KHÔNG CÓ GIÁ TRỊ"


def test_validation_errors():
    with pytest.raises(InvalidDocumentRequestValidationError, match="student_user_id must be a valid UUIDv7"):
        DocumentRequest.create_draft(
            student_user_id="invalid-uuid",
            document_type="STUDENT_CERTIFICATE",
            purpose_code="VISA",
            delivery_method=DocumentDeliveryMethod.DIGITAL,
        )

    with pytest.raises(InvalidDocumentRequestValidationError, match="document_type must match pattern"):
        DocumentRequest.create_draft(
            student_user_id="01923456-789a-7def-8123-456789abcdef",
            document_type="invalid type!",
            purpose_code="VISA",
            delivery_method=DocumentDeliveryMethod.DIGITAL,
        )


def test_state_transitions():
    req = DocumentRequest.create_draft(
        student_user_id="01923456-789a-7def-8123-456789abcdef",
        document_type="STUDENT_CERTIFICATE",
        purpose_code="VISA",
        delivery_method=DocumentDeliveryMethod.DIGITAL,
    )

    req = req.request_confirmation()
    assert req.status == DocumentRequestStatus.PENDING_CONFIRMATION
    assert req.version == 2

    exec_id = "01923456-789a-7def-8123-456789abcde0"
    req = req.confirm_submit(action_execution_id=exec_id)
    assert req.status == DocumentRequestStatus.SUBMITTED
    assert req.action_execution_id == exec_id
    assert req.submitted_at is not None
    assert req.version == 3

    req = req.start_validation()
    assert req.status == DocumentRequestStatus.VALIDATING
    assert req.version == 4

    req = req.start_processing()
    assert req.status == DocumentRequestStatus.PROCESSING
    assert req.version == 5

    req = req.mark_ready()
    assert req.status == DocumentRequestStatus.READY
    assert req.version == 6

    req = req.fulfill()
    assert req.status == DocumentRequestStatus.FULFILLED
    assert req.version == 7


def test_invalid_transitions():
    req = DocumentRequest.create_draft(
        student_user_id="01923456-789a-7def-8123-456789abcdef",
        document_type="TRANSCRIPT",
        purpose_code="SCHOLARSHIP",
        delivery_method=DocumentDeliveryMethod.PICKUP,
    )
    req = req.cancel()
    assert req.status == DocumentRequestStatus.CANCELLED

    # Cannot transition from terminal state CANCELLED
    with pytest.raises(InvalidDocumentRequestStateError, match="Cannot transition from terminal state"):
        req.request_confirmation()
