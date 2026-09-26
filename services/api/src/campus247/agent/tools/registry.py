from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


class ToolValidationError(Exception):
    """Raised when tool candidate arguments fail validation or violate invariants."""
    pass


FORBIDDEN_ARGUMENTS = {"actor_id", "user_id", "role", "permissions", "tenant_id", "is_admin"}


@dataclass(frozen=True)
class ToolDefinition:
    tool_id: str
    name: str
    description: str
    is_write: bool
    requires_confirmation: bool
    allowed_arguments: tuple[str, ...] = ()


class ToolRegistry:
    """Registry of authorized typed tools and validator for tool candidate arguments."""

    def __init__(self, tools: dict[str, ToolDefinition]) -> None:
        self._tools = tools

    @classmethod
    def default_v1(cls) -> ToolRegistry:
        defs = [
            ToolDefinition(
                tool_id="TOOL-SCHEDULE-001",
                name="student_schedule_get",
                description="Get personal class and exam schedule",
                is_write=False,
                requires_confirmation=False,
                allowed_arguments=("from", "to", "cursor", "limit", "date_from", "date_to", "semester"),
            ),
            ToolDefinition(
                tool_id="TOOL-TICKET-001",
                name="ticket_create",
                description="Create student support ticket",
                is_write=True,
                requires_confirmation=True,
                allowed_arguments=("category", "subject", "description", "contact_preference", "attachment_refs", "title", "priority"),
            ),
            ToolDefinition(
                tool_id="TOOL-TICKET-002",
                name="ticket_get",
                description="Get details of an existing ticket",
                is_write=False,
                requires_confirmation=False,
                allowed_arguments=("ticket_id",),
            ),
            ToolDefinition(
                tool_id="TOOL-DOCUMENT-001",
                name="document_request_create",
                description="Request official student certificate or transcript",
                is_write=True,
                requires_confirmation=True,
                allowed_arguments=("document_type", "purpose", "delivery_method", "copies", "quantity"),
            ),
            ToolDefinition(
                tool_id="TOOL-ROOM-001",
                name="room_availability_search",
                description="Search available rooms and lecture halls",
                is_write=False,
                requires_confirmation=False,
                allowed_arguments=("building", "date", "slot"),
            ),
            ToolDefinition(
                tool_id="TOOL-ROOM-002",
                name="room_booking_create",
                description="Reserve room or hall for class/club",
                is_write=True,
                requires_confirmation=True,
                allowed_arguments=("room_id", "starts_at", "ends_at", "purpose", "attendee_count", "start_time", "end_time"),
            ),
            ToolDefinition(
                tool_id="TOOL-HITL-001",
                name="handover_create",
                description="Escalate conversation to human support queue",
                is_write=True,
                requires_confirmation=False,
                allowed_arguments=("category", "summary", "urgency", "reason"),
            ),
        ]
        return cls(tools={t.tool_id: t for t in defs})

    def has_tool(self, tool_id: str) -> bool:
        return tool_id in self._tools

    def get_tool(self, tool_id: str) -> ToolDefinition:
        if tool_id not in self._tools:
            raise ToolValidationError(f"Unknown tool ID: '{tool_id}'")
        return self._tools[tool_id]

    def validate_candidate(self, tool_id: str, arguments: dict[str, Any]) -> dict[str, Any]:
        tool = self.get_tool(tool_id)

        # Check for forbidden arguments (smuggling / privilege injection)
        for forbidden in FORBIDDEN_ARGUMENTS:
            if forbidden in arguments:
                raise ToolValidationError(
                    f"Forbidden argument '{forbidden}' in tool candidate for {tool_id}"
                )

        # Validate arguments against allowed list
        for arg_name in arguments:
            if arg_name not in tool.allowed_arguments:
                raise ToolValidationError(
                    f"Unexpected argument '{arg_name}' for tool {tool_id}. Allowed: {tool.allowed_arguments}"
                )

        return dict(arguments)
