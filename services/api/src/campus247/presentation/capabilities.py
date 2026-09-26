from __future__ import annotations

from datetime import datetime, timezone
from enum import StrEnum
from typing import Any
from fastapi import APIRouter
from starlette.responses import JSONResponse


class SystemState(StrEnum):
    NORMAL = "NORMAL"
    DEGRADED_NO_LLM = "DEGRADED_NO_LLM"
    DEGRADED_NO_INTEGRATION = "DEGRADED_NO_INTEGRATION"
    DEGRADED_ASYNC_BACKLOG = "DEGRADED_ASYNC_BACKLOG"
    READ_ONLY = "READ_ONLY"
    SEARCH_ONLY = "SEARCH_ONLY"
    MAINTENANCE = "MAINTENANCE"


STATE_BANNERS = {
    SystemState.NORMAL: None,
    SystemState.DEGRADED_NO_LLM: "Hệ thống đang hoạt động ở chế độ dự phòng (tạm ngừng sinh câu trả lời AI tự động).",
    SystemState.DEGRADED_NO_INTEGRATION: "Kết nối hệ thống tích hợp tạm thời gián đoạn. Một số chức năng ghi bị tạm dừng.",
    SystemState.DEGRADED_ASYNC_BACKLOG: "Hàng đợi xử lý đang quá tải. Các tác vụ nền có thể bị chậm trễ.",
    SystemState.READ_ONLY: "Hệ thống đang ở chế độ chỉ đọc. Mọi thao tác tạo mới tạm thời bị khóa.",
    SystemState.SEARCH_ONLY: "Chế độ chỉ tra cứu tài liệu đang được kích hoạt.",
    SystemState.MAINTENANCE: "Hệ thống đang được bảo trì theo kế hoạch. Vui lòng quay lại sau.",
}


class CapabilityManager:
    def __init__(self, initial_state: SystemState = SystemState.NORMAL) -> None:
        self._state = initial_state
        self._reason: str | None = None
        self._version = 1
        self._updated_at = datetime.now(timezone.utc)

    def set_state(self, new_state: SystemState | str, reason: str | None = None) -> None:
        try:
            state_enum = SystemState(new_state)
        except ValueError:
            raise ValueError(f"Invalid system state: {new_state}")

        self._state = state_enum
        self._reason = reason
        self._version += 1
        self._updated_at = datetime.now(timezone.utc)

    def get_capabilities_map(self) -> dict[str, bool]:
        s = self._state
        if s == SystemState.NORMAL:
            return {
                "chat_generation": True,
                "tool_planning": True,
                "document_search": True,
                "ticket_create": True,
                "ticket_read": True,
                "room_booking": True,
                "handover_create": True,
                "admin_operations": True,
            }
        if s == SystemState.DEGRADED_NO_LLM:
            return {
                "chat_generation": False,
                "tool_planning": False,
                "document_search": True,
                "ticket_create": True,
                "ticket_read": True,
                "room_booking": True,
                "handover_create": True,
                "admin_operations": True,
            }
        if s == SystemState.READ_ONLY:
            return {
                "chat_generation": True,
                "tool_planning": False,
                "document_search": True,
                "ticket_create": False,
                "ticket_read": True,
                "room_booking": False,
                "handover_create": False,
                "admin_operations": False,
            }
        if s == SystemState.SEARCH_ONLY:
            return {
                "chat_generation": False,
                "tool_planning": False,
                "document_search": True,
                "ticket_create": False,
                "ticket_read": True,
                "room_booking": False,
                "handover_create": False,
                "admin_operations": False,
            }
        if s == SystemState.MAINTENANCE:
            return {
                "chat_generation": False,
                "tool_planning": False,
                "document_search": False,
                "ticket_create": False,
                "ticket_read": False,
                "room_booking": False,
                "handover_create": False,
                "admin_operations": False,
            }
        # default fallback for DEGRADED_NO_INTEGRATION / BACKLOG
        return {
            "chat_generation": True,
            "tool_planning": False,
            "document_search": True,
            "ticket_create": True,
            "ticket_read": True,
            "room_booking": False,
            "handover_create": True,
            "admin_operations": True,
        }

    def get_state_payload(self) -> dict[str, Any]:
        return {
            "system_state": self._state.value,
            "capabilities": self.get_capabilities_map(),
            "degradation_reason": self._reason,
            "banner_message": STATE_BANNERS.get(self._state),
            "version": self._version,
            "checked_at": datetime.now(timezone.utc).isoformat(),
        }


def create_capabilities_router(manager: CapabilityManager | None = None) -> APIRouter:
    router = APIRouter(tags=["Operations"])
    cap_mgr = manager or CapabilityManager()

    async def _handle_capabilities() -> JSONResponse:
        data = cap_mgr.get_state_payload()
        return JSONResponse(
            status_code=200,
            content=data,
            headers={
                "ETag": f'"{data["version"]}"',
                "Cache-Control": "public, max-age=5",
            },
        )

    @router.get("/v1/capabilities")
    async def get_capabilities() -> JSONResponse:
        return await _handle_capabilities()

    @router.get("/v1/operations/capabilities")
    async def get_operations_capabilities() -> JSONResponse:
        return await _handle_capabilities()

    return router
