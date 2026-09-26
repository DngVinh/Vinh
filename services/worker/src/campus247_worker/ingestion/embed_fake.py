from __future__ import annotations

import hashlib
import math
import random


class DeterministicEmbeddingAdapter:
    """Offline, deterministic embedding adapter that produces L2-normalized vectors."""

    def __init__(self, dimension: int = 1536) -> None:
        self.dimension = dimension

    def embed_text(self, text: str) -> list[float]:
        if not text or not text.strip():
            raise ValueError("Cannot embed empty text")

        # Derive 64-bit integer seed from sha256 of text
        digest = hashlib.sha256(text.strip().encode("utf-8")).digest()
        seed = int.from_bytes(digest[:8], byteorder="big")

        rng = random.Random(seed)
        # Generate pseudo-random vector with standard normal distribution
        raw_vec = [rng.gauss(0.0, 1.0) for _ in range(self.dimension)]

        # L2-normalize
        norm = math.sqrt(sum(x * x for x in raw_vec))
        if norm == 0.0:
            return [0.0] * self.dimension

        return [round(x / norm, 6) for x in raw_vec]

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        return [self.embed_text(t) for t in texts]
