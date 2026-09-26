from __future__ import annotations

import dataclasses
import re
from campus247.agent.state import AgentState, DraftResponse, Terminal
from campus247.application.retrieval.citations import CitationBundle

SECRET_PATTERNS = [
    r"sk-[a-zA-Z0-9_-]{16,}",
    r"bearer\s+[a-zA-Z0-9_\-\.]{20,}",
    r"password\s*[:=]\s*\S+",
    r"secret_token\s*[:=]\s*\S+",
]


class ComposeGroundedNode:
    """Synthesizes grounded draft response using active citation bundle context."""

    def execute(self, state: AgentState, bundle: CitationBundle) -> AgentState:
        citations = bundle.citations
        if not citations:
            return dataclasses.replace(
                state,
                draft=DraftResponse(
                    text="Không có thông tin trích dẫn để soạn thảo câu trả lời.",
                    claim_count=0,
                    is_grounded=False,
                ),
            )

        # Build grounded draft referencing citations
        first_cit_id = sorted(citations.keys())[0]
        first_rec = citations[first_cit_id]

        response_text = f"{first_rec.content_text} [{first_cit_id}]."
        return dataclasses.replace(
            state,
            draft=DraftResponse(
                text=response_text,
                claim_count=1,
                is_grounded=True,
            ),
        )


class OutputGuardNode:
    """Scans response draft for secret leakage and unsafe content before delivery."""

    def execute(self, state: AgentState) -> AgentState:
        if not state.draft or not state.draft.text:
            return dataclasses.replace(state, terminal=Terminal.SAFE_FAILURE)

        text = state.draft.text

        # Check for secret leakage
        for pattern in SECRET_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                return dataclasses.replace(
                    state,
                    terminal=Terminal.SAFE_FAILURE,
                    draft=DraftResponse(
                        text="Phản hồi bị chặn do vi phạm quy tắc an toàn bảo mật thông tin.",
                        is_grounded=False,
                    ),
                    errors=state.errors + ("Secret leakage detected in output",),
                )

        terminal = state.terminal if state.terminal is not None else Terminal.ANSWERED
        return dataclasses.replace(state, terminal=terminal)
