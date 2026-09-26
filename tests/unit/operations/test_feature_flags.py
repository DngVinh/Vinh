from __future__ import annotations

import pytest
from campus247.application.operations.feature_flags import (
    FeatureFlagService,
    FeatureFlag,
    InvalidFlagError,
    FlagStateError,
    SystemState,
)


def test_default_feature_flags_all_enabled() -> None:
    service = FeatureFlagService()
    assert service.is_enabled(FeatureFlag.LLM_GENERATION) is True
    assert service.is_enabled(FeatureFlag.TOOL_PLANNING) is True
    assert service.is_enabled(FeatureFlag.ROOM_BOOKING) is True
    assert service.is_enabled(FeatureFlag.TICKET_CREATION) is True
    assert service.is_enabled(FeatureFlag.DOCUMENT_SEARCH) is True
    assert service.get_effective_state() == SystemState.NORMAL


def test_kill_switch_llm_degrades_to_no_llm() -> None:
    service = FeatureFlagService()
    service.set_kill_switch(FeatureFlag.LLM_GENERATION, kill=True, reason="Provider timeout")
    assert service.is_enabled(FeatureFlag.LLM_GENERATION) is False
    assert service.is_enabled(FeatureFlag.DOCUMENT_SEARCH) is True
    assert service.get_effective_state() == SystemState.DEGRADED_NO_LLM


def test_kill_switch_write_operations_degrades_to_read_only() -> None:
    service = FeatureFlagService()
    service.set_kill_switch(FeatureFlag.WRITE_OPERATIONS, kill=True, reason="Audit risk")
    assert service.is_enabled(FeatureFlag.WRITE_OPERATIONS) is False
    assert service.is_enabled(FeatureFlag.TICKET_CREATION) is False
    assert service.is_enabled(FeatureFlag.ROOM_BOOKING) is False
    assert service.is_enabled(FeatureFlag.DOCUMENT_SEARCH) is True
    assert service.get_effective_state() == SystemState.READ_ONLY


def test_search_only_mode_disables_generative_and_writes() -> None:
    service = FeatureFlagService()
    service.set_safe_mode(SystemState.SEARCH_ONLY, reason="AI safety review")
    assert service.is_enabled(FeatureFlag.LLM_GENERATION) is False
    assert service.is_enabled(FeatureFlag.TOOL_PLANNING) is False
    assert service.is_enabled(FeatureFlag.DOCUMENT_SEARCH) is True
    assert service.is_enabled(FeatureFlag.TICKET_CREATION) is False
    assert service.get_effective_state() == SystemState.SEARCH_ONLY


def test_negative_invalid_flag_name_raises_error() -> None:
    service = FeatureFlagService()
    with pytest.raises(InvalidFlagError, match="Unknown feature flag"):
        service.is_enabled("INVALID_UNKNOWN_FLAG")  # type: ignore

    with pytest.raises(InvalidFlagError, match="Unknown feature flag"):
        service.set_kill_switch("INVALID_UNKNOWN_FLAG", kill=True)  # type: ignore


def test_negative_invalid_safe_mode_raises_error() -> None:
    service = FeatureFlagService()
    with pytest.raises(FlagStateError, match="Invalid system state"):
        service.set_safe_mode("UNKNOWN_STATE")  # type: ignore


def test_export_capabilities_matches_system_capabilities() -> None:
    service = FeatureFlagService()
    caps = service.export_capabilities()
    assert caps["chat_generation"] is True
    assert caps["tool_planning"] is True
    assert caps["document_search"] is True

    service.set_kill_switch(FeatureFlag.LLM_GENERATION, kill=True)
    caps_degraded = service.export_capabilities()
    assert caps_degraded["chat_generation"] is False
    assert caps_degraded["document_search"] is True
