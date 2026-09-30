from __future__ import annotations

from collections.abc import Callable
import dataclasses
from typing import Any
from campus247.agent.state import AgentState, DraftResponse, RetrievalState, Route, Terminal

ABSTENTION_MESSAGE = (
    "Hiện tại tôi chưa tìm thấy tài liệu quy định chính thức về vấn đề này. "
    "Bạn có thể liên hệ bộ phận Một cửa hoặc tạo yêu cầu hỗ trợ để được giải đáp chi tiết."
)
MAX_CANDIDATES = 30
MAX_SCANNED_CANDIDATES = MAX_CANDIDATES * 4


class RetrieveEvidenceNode:
    """Retrieves knowledge evidence chunks for FAQ route or triggers safe abstention."""

    def __init__(self, search_fn: Callable[[str], list[dict[str, Any]]], max_candidates: int = MAX_CANDIDATES) -> None:
        if not 1 <= max_candidates <= MAX_CANDIDATES:
            raise ValueError(f"max_candidates must be between 1 and {MAX_CANDIDATES}")
        self._search_fn = search_fn
        self._max_candidates = max_candidates

    @staticmethod
    def _abstain(state: AgentState, reason: str) -> AgentState:
        errors = state.errors if reason in state.errors else state.errors + (reason,)
        return dataclasses.replace(
            state,
            retrieval=RetrievalState(candidate_ids=(), citation_bundle_ref="bundle_empty"),
            terminal=Terminal.ABSTAINED,
            draft=DraftResponse(
                text=ABSTENTION_MESSAGE,
                claim_count=0,
                is_grounded=True,
                gate_decision="abstain",
                gate_reasons=(reason,),
            ),
            errors=errors,
            step_count=state.step_count + 1,
        )

    @staticmethod
    def _eligible_candidate(candidate: Any) -> str | None:
        if not isinstance(candidate, dict):
            return None
        chunk_id = candidate.get("chunk_id") or candidate.get("id")
        if not isinstance(chunk_id, str) or not chunk_id.strip():
            return None
        metadata = candidate.get("metadata")
        metadata = metadata if isinstance(metadata, dict) else candidate
        if metadata.get("status") is not None and metadata.get("status") != "PUBLISHED":
            return None
        if metadata.get("is_authorized") is False or metadata.get("authorized") is False:
            return None
        if metadata.get("is_effective") is False:
            return None
        return chunk_id.strip()

    def execute(self, state: AgentState) -> AgentState:
        if state.route is not None and state.route != Route.GROUNDED_FAQ:
            return self._abstain(state, "AI_RETRIEVAL_ROUTE_INVALID")

        query = state.request.query.strip()
        if not query:
            return self._abstain(state, "AI_RETRIEVAL_INVALID_QUERY")

        try:
            candidates = self._search_fn(query)
        except Exception:
            return self._abstain(state, "AI_RETRIEVAL_UNAVAILABLE")

        if not isinstance(candidates, (list, tuple)):
            return self._abstain(state, "AI_RETRIEVAL_INVALID_RESULT")

        candidate_ids: list[str] = []
        seen_ids: set[str] = set()
        for candidate in candidates[:MAX_SCANNED_CANDIDATES]:
            chunk_id = self._eligible_candidate(candidate)
            if chunk_id is None or chunk_id in seen_ids:
                continue
            seen_ids.add(chunk_id)
            candidate_ids.append(chunk_id)
            if len(candidate_ids) >= self._max_candidates:
                break

        if not candidate_ids:
            return self._abstain(state, "AI_RETRIEVAL_INSUFFICIENT")

        return dataclasses.replace(
            state,
            retrieval=RetrievalState(
                candidate_ids=tuple(candidate_ids),
                citation_bundle_ref="turn_bundle",
            ),
            draft=None,
            step_count=state.step_count + 1,
        )
