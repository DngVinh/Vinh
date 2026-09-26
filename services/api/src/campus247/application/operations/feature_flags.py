from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import StrEnum


class SystemState(StrEnum):
    NORMAL = "NORMAL"
    DEGRADED_NO_LLM = "DEGRADED_NO_LLM"
    DEGRADED_NO_INTEGRATION = "DEGRADED_NO_INTEGRATION"
    DEGRADED_ASYNC_BACKLOG = "DEGRADED_ASYNC_BACKLOG"
    READ_ONLY = "READ_ONLY"
    SEARCH_ONLY = "SEARCH_ONLY"
    MAINTENANCE = "MAINTENANCE"


class FeatureFlag(StrEnum):
    LLM_GENERATION = "llm_generation"
    TOOL_PLANNING = "tool_planning"
    DOCUMENT_SEARCH = "document_search"
    TICKET_CREATION = "ticket_creation"
    ROOM_BOOKING = "room_booking"
    HANDOVER_CREATION = "handover_creation"
    WRITE_OPERATIONS = "write_operations"


WRITE_FLAGS: frozenset[FeatureFlag] = frozenset({
    FeatureFlag.TICKET_CREATION,
    FeatureFlag.ROOM_BOOKING,
    FeatureFlag.HANDOVER_CREATION,
})

GENERATIVE_FLAGS: frozenset[FeatureFlag] = frozenset({
    FeatureFlag.LLM_GENERATION,
    FeatureFlag.TOOL_PLANNING,
})


class InvalidFlagError(ValueError):
    """Raised when an unknown feature flag is queried or set."""


class FlagStateError(ValueError):
    """Raised when an invalid state transition or parameter is applied."""


@dataclass
class FlagOverride:
    killed: bool
    reason: str | None
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class FeatureFlagService:
    def __init__(self, base_state: SystemState = SystemState.NORMAL) -> None:
        self._base_state = base_state
        self._overrides: dict[FeatureFlag, FlagOverride] = {}
        self._reason: str | None = None

    @property
    def reason(self) -> str | None:
        return self._reason

    def _resolve_flag(self, flag: FeatureFlag | str) -> FeatureFlag:
        if isinstance(flag, FeatureFlag):
            return flag
        try:
            return FeatureFlag(flag)
        except ValueError:
            raise InvalidFlagError(f"Unknown feature flag: {flag}")

    def is_enabled(self, flag: FeatureFlag | str) -> bool:
        resolved = self._resolve_flag(flag)
        state = self.get_effective_state()

        if state == SystemState.MAINTENANCE:
            return False

        if resolved == FeatureFlag.WRITE_OPERATIONS:
            if state in {SystemState.READ_ONLY, SystemState.SEARCH_ONLY}:
                return False
            override = self._overrides.get(FeatureFlag.WRITE_OPERATIONS)
            return not (override and override.killed)

        if state == SystemState.READ_ONLY and resolved in WRITE_FLAGS:
            return False

        if state == SystemState.SEARCH_ONLY and (resolved in GENERATIVE_FLAGS or resolved in WRITE_FLAGS):
            return False

        if state == SystemState.DEGRADED_NO_LLM and resolved in GENERATIVE_FLAGS:
            return False

        if resolved in WRITE_FLAGS:
            write_override = self._overrides.get(FeatureFlag.WRITE_OPERATIONS)
            if write_override and write_override.killed:
                return False

        override = self._overrides.get(resolved)
        if override and override.killed:
            return False

        return True

    def set_kill_switch(self, flag: FeatureFlag | str, kill: bool = True, reason: str | None = None) -> None:
        resolved = self._resolve_flag(flag)
        self._overrides[resolved] = FlagOverride(killed=kill, reason=reason)
        if reason:
            self._reason = reason

    def set_safe_mode(self, state: SystemState | str, reason: str | None = None) -> None:
        try:
            state_enum = SystemState(state)
        except ValueError:
            raise FlagStateError(f"Invalid system state: {state}")
        self._base_state = state_enum
        self._reason = reason

    def get_effective_state(self) -> SystemState:
        if self._base_state != SystemState.NORMAL:
            return self._base_state

        write_override = self._overrides.get(FeatureFlag.WRITE_OPERATIONS)
        if write_override and write_override.killed:
            return SystemState.READ_ONLY

        llm_override = self._overrides.get(FeatureFlag.LLM_GENERATION)
        if llm_override and llm_override.killed:
            return SystemState.DEGRADED_NO_LLM

        return SystemState.NORMAL

    def export_capabilities(self) -> dict[str, bool]:
        return {
            "chat_generation": self.is_enabled(FeatureFlag.LLM_GENERATION),
            "tool_planning": self.is_enabled(FeatureFlag.TOOL_PLANNING),
            "document_search": self.is_enabled(FeatureFlag.DOCUMENT_SEARCH),
            "ticket_create": self.is_enabled(FeatureFlag.TICKET_CREATION),
            "ticket_read": True,
            "room_booking": self.is_enabled(FeatureFlag.ROOM_BOOKING),
            "handover_create": self.is_enabled(FeatureFlag.HANDOVER_CREATION),
            "admin_operations": self.is_enabled(FeatureFlag.WRITE_OPERATIONS),
        }
