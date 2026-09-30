from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import StrEnum
from typing import Any


class SimulationPolicy(StrEnum):
    DENY = "DENY"
    ALLOW_LABELED = "ALLOW_LABELED"


class RetrievalBranchStatus(StrEnum):
    SUCCEEDED = "SUCCEEDED"
    DEGRADED = "DEGRADED"
    FAILED = "FAILED"
    NOT_RUN = "NOT_RUN"


def _required(value: str, field_name: str) -> str:
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{field_name} is required")
    return normalized


def _normalized_scope(values: frozenset[str], field_name: str) -> frozenset[str]:
    normalized = frozenset(value.strip() for value in values if value.strip())
    if not normalized:
        raise ValueError(f"{field_name} must not be empty")
    return normalized


@dataclass(frozen=True)
class RetrievalQuery:
    text: str
    locale: str = "vi"
    exact_identifiers: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "text", _required(self.text, "text"))
        object.__setattr__(self, "locale", _required(self.locale, "locale"))
        object.__setattr__(
            self,
            "exact_identifiers",
            tuple(identifier.strip() for identifier in self.exact_identifiers if identifier.strip()),
        )


@dataclass(frozen=True)
class AuthorizedScope:
    tenant_id: str
    campus_id: str
    actor_id: str
    roles: frozenset[str]
    audiences: frozenset[str]
    faculty_codes: frozenset[str]
    program_codes: frozenset[str]

    def __post_init__(self) -> None:
        object.__setattr__(self, "tenant_id", _required(self.tenant_id, "tenant_id"))
        object.__setattr__(self, "campus_id", _required(self.campus_id, "campus_id"))
        object.__setattr__(self, "actor_id", _required(self.actor_id, "actor_id"))
        object.__setattr__(self, "roles", _normalized_scope(self.roles, "roles"))
        object.__setattr__(self, "audiences", _normalized_scope(self.audiences, "audiences"))
        object.__setattr__(self, "faculty_codes", _normalized_scope(self.faculty_codes, "faculty_codes"))
        object.__setattr__(self, "program_codes", _normalized_scope(self.program_codes, "program_codes"))


@dataclass(frozen=True)
class RetrievalContext:
    authorized_scope: AuthorizedScope
    locale: str
    effective_at: datetime
    simulation_policy: SimulationPolicy
    trace_id: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "locale", _required(self.locale, "locale"))
        object.__setattr__(self, "trace_id", _required(self.trace_id, "trace_id"))
        if self.effective_at.tzinfo is None or self.effective_at.utcoffset() is None:
            raise ValueError("effective_at must be timezone-aware")
        object.__setattr__(self, "effective_at", self.effective_at.astimezone(timezone.utc))

    def to_dict(self) -> dict[str, Any]:
        scope = self.authorized_scope
        return {
            "authorized_scope": {
                "tenant_id": scope.tenant_id,
                "campus_id": scope.campus_id,
                "actor_id": scope.actor_id,
                "roles": sorted(scope.roles),
                "audiences": sorted(scope.audiences),
                "faculty_codes": sorted(scope.faculty_codes),
                "program_codes": sorted(scope.program_codes),
            },
            "locale": self.locale,
            "effective_at": self.effective_at.isoformat().replace("+00:00", "Z"),
            "simulation_policy": self.simulation_policy.value,
            "trace_id": self.trace_id,
        }

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> RetrievalContext:
        scope = value["authorized_scope"]
        effective_at = datetime.fromisoformat(str(value["effective_at"]).replace("Z", "+00:00"))
        return cls(
            authorized_scope=AuthorizedScope(
                tenant_id=str(scope["tenant_id"]),
                campus_id=str(scope["campus_id"]),
                actor_id=str(scope["actor_id"]),
                roles=frozenset(scope["roles"]),
                audiences=frozenset(scope["audiences"]),
                faculty_codes=frozenset(scope["faculty_codes"]),
                program_codes=frozenset(scope["program_codes"]),
            ),
            locale=str(value["locale"]),
            effective_at=effective_at,
            simulation_policy=SimulationPolicy(value["simulation_policy"]),
            trace_id=str(value["trace_id"]),
        )


@dataclass(frozen=True)
class RetrievalCandidate:
    source_id: str
    document_version_id: str
    chunk_id: str
    content_text: str
    title: str
    issuer: str
    canonical_uri: str
    quote_span_hash: str
    section_path: tuple[str, ...]
    document_number: str | None = None
    page_start: int | None = None
    page_end: int | None = None
    effective_from: datetime | None = None
    effective_until: datetime | None = None
    simulation_label: bool = False
    lexical_rank: int | None = None
    vector_rank: int | None = None
    fused_score: float | None = None
    rerank_score: float | None = None

    def __post_init__(self) -> None:
        for field_name in (
            "source_id",
            "document_version_id",
            "chunk_id",
            "content_text",
            "title",
            "issuer",
            "canonical_uri",
            "quote_span_hash",
        ):
            object.__setattr__(self, field_name, _required(getattr(self, field_name), field_name))
        if not self.section_path or any(not part.strip() for part in self.section_path):
            raise ValueError("section_path must contain non-empty locator parts")
        if self.page_start is not None and self.page_start < 1:
            raise ValueError("page_start must be positive")
        if self.page_end is not None and (self.page_start is None or self.page_end < self.page_start):
            raise ValueError("page_end requires page_start and must not precede it")


@dataclass(frozen=True)
class RetrievalBranchDiagnostic:
    branch: str
    status: RetrievalBranchStatus
    candidate_count: int
    duration_ms: int
    reason_code: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "branch", _required(self.branch, "branch"))
        if self.candidate_count < 0 or self.duration_ms < 0:
            raise ValueError("candidate_count and duration_ms must not be negative")
        if self.status in {RetrievalBranchStatus.DEGRADED, RetrievalBranchStatus.FAILED}:
            _required(self.reason_code or "", "reason_code")


@dataclass(frozen=True)
class RetrievalDiagnostics:
    retrieval_profile_version: str
    index_version: str
    embedding_model_version: str
    reranker_model_version: str
    branches: tuple[RetrievalBranchDiagnostic, ...]
    total_duration_ms: int

    def __post_init__(self) -> None:
        for field_name in (
            "retrieval_profile_version",
            "index_version",
            "embedding_model_version",
            "reranker_model_version",
        ):
            object.__setattr__(self, field_name, _required(getattr(self, field_name), field_name))
        if self.total_duration_ms < 0:
            raise ValueError("total_duration_ms must not be negative")


@dataclass(frozen=True)
class RetrievalResult:
    candidates: tuple[RetrievalCandidate, ...]
    selected_chunk_ids: tuple[str, ...]
    diagnostics: RetrievalDiagnostics

    def __post_init__(self) -> None:
        candidate_ids = {candidate.chunk_id for candidate in self.candidates}
        if len(candidate_ids) != len(self.candidates):
            raise ValueError("retrieval candidates must have unique chunk IDs")
        if len(set(self.selected_chunk_ids)) != len(self.selected_chunk_ids):
            raise ValueError("selected_chunk_ids must not contain duplicates")
        if any(chunk_id not in candidate_ids for chunk_id in self.selected_chunk_ids):
            raise ValueError("selected_chunk_ids must refer to returned candidates")
