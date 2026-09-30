from __future__ import annotations

from pathlib import Path
import sys
import pytest

ROOT = Path(__file__).resolve().parents[3]
API_SRC = ROOT / "services" / "api" / "src"
if str(API_SRC) not in sys.path:
    sys.path.insert(0, str(API_SRC))

from campus247.agent.tools.registry import (
    ToolDefinition,
    ToolRegistry,
    ToolValidationError,
)


def test_tool_registry_contains_v1_tools() -> None:
    registry = ToolRegistry.default_v1()
    assert registry.has_tool("TOOL-SCHEDULE-001")
    assert registry.has_tool("TOOL-TICKET-001")
    assert registry.has_tool("TOOL-HITL-001")

    sched = registry.get_tool("TOOL-SCHEDULE-001")
    assert sched.is_write is False
    assert sched.requires_confirmation is False

    ticket = registry.get_tool("TOOL-TICKET-001")
    assert ticket.is_write is True
    assert ticket.requires_confirmation is True


def test_validate_tool_candidate_valid() -> None:
    registry = ToolRegistry.default_v1()
    validated = registry.validate_candidate(
        tool_id="TOOL-SCHEDULE-001",
        arguments={"date_from": "2026-09-22", "date_to": "2026-09-28"},
    )
    assert validated["date_from"] == "2026-09-22"


def test_validate_tool_candidate_rejects_actor_smuggling() -> None:
    registry = ToolRegistry.default_v1()
    # Model attempts to inject unauthorized actor_id
    with pytest.raises(ToolValidationError, match="Forbidden argument"):
        registry.validate_candidate(
            tool_id="TOOL-SCHEDULE-001",
            arguments={"actor_id": "user_other_student", "date_from": "2026-09-22"},
        )


def test_validate_unknown_tool_fails() -> None:
    registry = ToolRegistry.default_v1()
    with pytest.raises(ToolValidationError, match="Unknown tool ID"):
        registry.validate_candidate(tool_id="TOOL-UNKNOWN-999", arguments={})


@pytest.mark.asyncio
async def test_tool_execute_with_policy_success() -> None:
    registry = ToolRegistry.default_v1()
    
    async def fake_tool():
        return "success"
        
    res = await registry.execute_with_policy("TOOL-ROOM-001", fake_tool)
    assert res == "success"

@pytest.mark.asyncio
async def test_tool_execute_with_policy_timeout() -> None:
    from campus247.agent.tools.registry import ToolExecutionError
    import asyncio
    registry = ToolRegistry.default_v1()
    
    # Temporarily set timeout to small value
    tool = registry.get_tool("TOOL-ROOM-001")
    object.__setattr__(tool, "timeout_ms", 10)
    
    async def fake_slow_tool():
        await asyncio.sleep(0.05)
        return "success"
        
    with pytest.raises(ToolExecutionError) as exc:
        await registry.execute_with_policy("TOOL-ROOM-001", fake_slow_tool)
        
    assert "timed out" in str(exc.value)

@pytest.mark.asyncio
async def test_tool_execute_with_policy_circuit_breaker() -> None:
    from campus247.agent.tools.registry import ToolExecutionError, CircuitBreakerTrippedError
    registry = ToolRegistry.default_v1()
    
    async def fake_failing_tool():
        raise RuntimeError("failed")
        
    # Fail 3 times to trip breaker
    for _ in range(3):
        with pytest.raises(ToolExecutionError):
            await registry.execute_with_policy("TOOL-ROOM-001", fake_failing_tool)
            
    with pytest.raises(CircuitBreakerTrippedError):
        await registry.execute_with_policy("TOOL-ROOM-001", fake_failing_tool)
