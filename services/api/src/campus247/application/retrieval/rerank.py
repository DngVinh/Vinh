from __future__ import annotations

from typing import Sequence


class RerankOutputValidator:
    """Validates that reranker model output references ONLY allowlisted candidate IDs."""

    def __init__(self, allowlisted_ids: Sequence[str], top_k: int = 5) -> None:
        self._allowlisted_order = list(allowlisted_ids)
        self._allowlist_set = set(allowlisted_ids)
        self._top_k = top_k

    def validate_and_filter(self, candidate_ids: Sequence[str]) -> list[str]:
        valid_ordered: list[str] = []
        seen: set[str] = set()

        for cid in candidate_ids:
            if cid in self._allowlist_set and cid not in seen:
                valid_ordered.append(cid)
                seen.add(cid)

        # Fallback to original order if model output is empty or completely hallucinated
        if not valid_ordered:
            return self._allowlisted_order[: self._top_k]

        return valid_ordered[: self._top_k]
