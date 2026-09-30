from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Literal, Protocol, Sequence


class EmbeddingContractError(ValueError):
    """Base error for deterministic embedding contract violations."""


class EmptyEmbeddingInputError(EmbeddingContractError):
    pass


class EmbeddingBatchLimitError(EmbeddingContractError):
    pass


class EmbeddingDimensionMismatchError(EmbeddingContractError):
    pass


class EmbeddingModelMismatchError(EmbeddingContractError):
    pass


class InvalidEmbeddingVectorError(EmbeddingContractError):
    pass


class EmbeddingTimeoutError(TimeoutError):
    pass


@dataclass(frozen=True)
class EmbeddingProfile:
    model_id: str
    model_revision: str
    dimension: int
    normalization: Literal["l2"] = "l2"
    batch_limit: int = 64
    timeout_ms: int = 10_000

    def __post_init__(self) -> None:
        if not self.model_id.strip() or not self.model_revision.strip():
            raise EmbeddingContractError("model_id and model_revision are required")
        if self.dimension <= 0 or self.batch_limit <= 0 or self.timeout_ms <= 0:
            raise EmbeddingContractError("dimension, batch_limit and timeout_ms must be positive")


@dataclass(frozen=True)
class EmbeddingVector:
    values: tuple[float, ...]
    model_id: str
    model_revision: str
    dimension: int
    normalization: Literal["l2"]


@dataclass(frozen=True)
class EmbeddingBatch:
    vectors: tuple[EmbeddingVector, ...]
    model_id: str
    model_revision: str
    dimension: int
    normalization: Literal["l2"]


class EmbeddingPort(Protocol):
    @property
    def profile(self) -> EmbeddingProfile:
        ...

    def embed_documents(self, texts: Sequence[str]) -> EmbeddingBatch:
        ...

    def embed_query(self, text: str) -> EmbeddingVector:
        ...


def validate_embedding_inputs(texts: Sequence[str], profile: EmbeddingProfile) -> tuple[str, ...]:
    if not texts:
        raise EmptyEmbeddingInputError("at least one embedding input is required")
    if len(texts) > profile.batch_limit:
        raise EmbeddingBatchLimitError(
            f"embedding batch size {len(texts)} exceeds limit {profile.batch_limit}"
        )

    normalized = tuple(text.strip() for text in texts)
    if any(not text for text in normalized):
        raise EmptyEmbeddingInputError("embedding inputs must not be empty")
    return normalized


def validate_embedding_vector(
    values: Sequence[float],
    profile: EmbeddingProfile,
    *,
    model_id: str | None = None,
    model_revision: str | None = None,
) -> EmbeddingVector:
    if model_id is not None and model_id != profile.model_id:
        raise EmbeddingModelMismatchError("embedding model_id does not match the active profile")
    if model_revision is not None and model_revision != profile.model_revision:
        raise EmbeddingModelMismatchError("embedding model_revision does not match the active profile")
    if len(values) != profile.dimension:
        raise EmbeddingDimensionMismatchError(
            f"embedding dimension {len(values)} does not match expected {profile.dimension}"
        )

    vector = tuple(float(value) for value in values)
    if any(not math.isfinite(value) for value in vector):
        raise InvalidEmbeddingVectorError("embedding vector contains NaN or Infinity")

    norm = math.sqrt(sum(value * value for value in vector))
    if norm == 0.0 or not math.isclose(norm, 1.0, rel_tol=1e-3, abs_tol=1e-3):
        raise InvalidEmbeddingVectorError("embedding vector is not L2-normalized")

    return EmbeddingVector(
        values=vector,
        model_id=profile.model_id,
        model_revision=profile.model_revision,
        dimension=profile.dimension,
        normalization=profile.normalization,
    )
