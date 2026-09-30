from __future__ import annotations

from datetime import datetime, timezone

import pytest

from campus247.domain.retrieval import (
    AuthorizedScope,
    RetrievalBranchDiagnostic,
    RetrievalBranchStatus,
    RetrievalCandidate,
    RetrievalContext,
    RetrievalDiagnostics,
    RetrievalQuery,
    RetrievalResult,
    SimulationPolicy,
)


def authorized_scope() -> AuthorizedScope:
    return AuthorizedScope(
        tenant_id="HUCE",
        campus_id="HUCE",
        actor_id="user-001",
        roles=frozenset({"STUDENT"}),
        audiences=frozenset({"STUDENT", "COHORT-2026"}),
        faculty_codes=frozenset({"FIT"}),
        program_codes=frozenset({"SOFTWARE_ENGINEERING"}),
    )


def candidate(chunk_id: str = "chunk-001") -> RetrievalCandidate:
    return RetrievalCandidate(
        source_id="source-001",
        document_version_id="version-001",
        chunk_id=chunk_id,
        content_text="Nội dung quy định đã được duyệt.",
        title="Quy định học vụ",
        issuer="HUCE",
        canonical_uri="https://example.invalid/regulation/1",
        quote_span_hash="sha256:abc",
        section_path=("Chương I", "Điều 1"),
        page_start=1,
        page_end=1,
    )


def diagnostics() -> RetrievalDiagnostics:
    return RetrievalDiagnostics(
        retrieval_profile_version="rag-prod-v1.0.0",
        index_version="index-001",
        embedding_model_version="bge-m3@5617a9f",
        reranker_model_version="bge-reranker-v2-m3@953dc6f",
        branches=(
            RetrievalBranchDiagnostic(
                branch="lexical",
                status=RetrievalBranchStatus.SUCCEEDED,
                candidate_count=1,
                duration_ms=10,
            ),
        ),
        total_duration_ms=20,
    )


def test_retrieval_context_serialization_round_trip() -> None:
    context = RetrievalContext(
        authorized_scope=authorized_scope(),
        locale="vi",
        effective_at=datetime(2026, 9, 29, 12, 0, tzinfo=timezone.utc),
        simulation_policy=SimulationPolicy.DENY,
        trace_id="trace-001",
    )

    restored = RetrievalContext.from_dict(context.to_dict())

    assert restored == context
    assert restored.effective_at.tzinfo is timezone.utc


def test_query_normalizes_exact_identifiers() -> None:
    query = RetrievalQuery("  học phí CT-101  ", exact_identifiers=(" CT-101 ", ""))
    assert query.text == "học phí CT-101"
    assert query.exact_identifiers == ("CT-101",)


def test_authorized_scope_fails_closed_for_empty_scope() -> None:
    with pytest.raises(ValueError, match="roles must not be empty"):
        AuthorizedScope(
            tenant_id="HUCE",
            campus_id="HUCE",
            actor_id="user-001",
            roles=frozenset(),
            audiences=frozenset({"STUDENT"}),
            faculty_codes=frozenset({"FIT"}),
            program_codes=frozenset({"SOFTWARE_ENGINEERING"}),
        )


def test_context_rejects_naive_effective_time() -> None:
    with pytest.raises(ValueError, match="timezone-aware"):
        RetrievalContext(
            authorized_scope=authorized_scope(),
            locale="vi",
            effective_at=datetime(2026, 9, 29, 12, 0),
            simulation_policy=SimulationPolicy.DENY,
            trace_id="trace-001",
        )


def test_result_rejects_foreign_or_duplicate_selected_ids() -> None:
    with pytest.raises(ValueError, match="refer to returned candidates"):
        RetrievalResult(
            candidates=(candidate(),),
            selected_chunk_ids=("foreign-chunk",),
            diagnostics=diagnostics(),
        )
    with pytest.raises(ValueError, match="must not contain duplicates"):
        RetrievalResult(
            candidates=(candidate(),),
            selected_chunk_ids=("chunk-001", "chunk-001"),
            diagnostics=diagnostics(),
        )


def test_failed_branch_requires_reason_code() -> None:
    with pytest.raises(ValueError, match="reason_code is required"):
        RetrievalBranchDiagnostic(
            branch="vector",
            status=RetrievalBranchStatus.FAILED,
            candidate_count=0,
            duration_ms=700,
        )
