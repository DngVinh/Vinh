from __future__ import annotations

from collections.abc import Callable
import dataclasses
from typing import Any
from campus247.agent.state import AgentState, DraftResponse, RetrievalState, Terminal

ABSTENTION_MESSAGE = (
    "Hiện tại tôi chưa tìm thấy tài liệu quy định chính thức về vấn đề này. "
    "Bạn có thể liên hệ bộ phận Một cửa hoặc tạo yêu cầu hỗ trợ để được giải đáp chi tiết."
)


class RetrieveEvidenceNode:
    """Retrieves knowledge evidence chunks for FAQ route or triggers safe abstention."""

    def __init__(self, search_fn: Callable[[str], list[dict[str, Any]]]) -> None:
        self._search_fn = search_fn

    def execute(self, state: AgentState) -> AgentState:
        query = state.request.query
        candidates = self._search_fn(query)

        if not candidates:
            # Abstain deterministically
            return dataclasses.replace(
                state,
                terminal=Terminal.ABSTAINED,
                draft=DraftResponse(
                    text=ABSTENTION_MESSAGE,
                    claim_count=0,
                    is_grounded=True,
                ),
            )

        candidate_ids = tuple(str(c.get("chunk_id", "")) for c in candidates if c.get("chunk_id"))
        return dataclasses.replace(
            state,
            retrieval=RetrievalState(
                candidate_ids=candidate_ids,
                citation_bundle_ref="turn_bundle",
            ),
        )
