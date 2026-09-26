from __future__ import annotations

import re
from typing import Any
from fastapi import Request
from fastapi.exceptions import HTTPException, RequestValidationError
from starlette.responses import JSONResponse

from campus247.domain.shared.values import generate_uuid7, is_valid_uuid7

PROBLEM_TYPE_BASE = "https://campus247.example/problems"

STATUS_CODE_MAP: dict[int, tuple[str, str]] = {
    400: ("VALIDATION_FAILED", "Yêu cầu không hợp lệ"),
    401: ("AUTHENTICATION_REQUIRED", "Yêu cầu xác thực danh tính"),
    403: ("FORBIDDEN", "Từ chối quyền truy cập"),
    404: ("RESOURCE_NOT_FOUND", "Không tìm thấy tài nguyên"),
    409: ("INVALID_STATE_TRANSITION", "Trạng thái nghiệp vụ không hợp lệ"),
    413: ("PAYLOAD_TOO_LARGE", "Dung lượng yêu cầu vượt quá giới hạn"),
    415: ("UNSUPPORTED_MEDIA_TYPE", "Định dạng dữ liệu không được hỗ trợ"),
    422: ("VALIDATION_FAILED", "Dữ liệu yêu cầu không hợp lệ"),
    429: ("RATE_LIMITED", "Tần suất yêu cầu vượt quá hạn mức"),
    500: ("INTERNAL_ERROR", "Lỗi nội bộ hệ thống"),
    502: ("DEPENDENCY_UNAVAILABLE", "Dịch vụ phụ thuộc không khả dụng"),
    503: ("DEPENDENCY_UNAVAILABLE", "Hệ thống đang bảo trì hoặc quá tải"),
}


def create_problem_details(
    status: int,
    code: str,
    title: str,
    detail: str,
    request: Request,
    errors: list[dict[str, str]] | None = None,
    retryable: bool = False,
) -> JSONResponse:
    """Build RFC 9457 Problem Details JSONResponse conforming to error.schema.json."""
    req_id = getattr(request.state, "request_id", None)
    if not req_id or not is_valid_uuid7(str(req_id)):
        req_id = generate_uuid7()

    type_suffix = code.lower().replace("_", "-")
    problem_type = f"{PROBLEM_TYPE_BASE}/{type_suffix}"

    body: dict[str, Any] = {
        "type": problem_type,
        "title": title[:160],
        "status": status,
        "detail": detail[:1000] if detail else title,
        "instance": f"urn:request:{req_id}",
        "code": code,
        "request_id": str(req_id),
        "retryable": retryable,
    }
    if errors is not None:
        body["errors"] = errors[:50]

    return JSONResponse(
        status_code=status,
        content=body,
        headers={
            "Content-Type": "application/problem+json",
            "X-Request-Id": str(req_id),
        },
    )


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Handle standard HTTPException by converting into RFC 9457 Problem Details."""
    status = exc.status_code
    default_code, default_title = STATUS_CODE_MAP.get(
        status, ("INTERNAL_ERROR", "Lỗi xử lý yêu cầu")
    )

    detail_str = str(exc.detail) if exc.detail else default_title

    # Custom mapping if detail indicates specific error
    code = default_code
    title = default_title
    if status == 403 and "ownership" in detail_str.lower():
        code = "FORBIDDEN"
        title = "Không có quyền sở hữu tài nguyên"
    elif status == 404:
        code = "RESOURCE_NOT_FOUND"
        title = "Tài nguyên không tồn tại"

    return create_problem_details(
        status=status,
        code=code,
        title=title,
        detail=detail_str,
        request=request,
    )


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Handle Pydantic RequestValidationError by formatting RFC 6901 pointers."""
    field_errors: list[dict[str, str]] = []
    for err in exc.errors():
        loc = err.get("loc", ())
        # Build RFC 6901 JSON pointer
        pointer_parts = [str(p) for p in loc if str(p) not in ("body", "query", "path")]
        pointer = "/" + "/".join(pointer_parts) if pointer_parts else "/"

        err_type = str(err.get("type", "VALIDATION_ERROR")).upper().replace(".", "_")
        clean_code = re.sub(r"[^A-Z0-9_]", "_", err_type)[:64]
        if not re.match(r"^[A-Z][A-Z0-9_]{1,63}$", clean_code):
            clean_code = "VALUE_ERROR"

        msg = str(err.get("msg", "Dữ liệu không hợp lệ"))
        field_errors.append(
            {
                "code": clean_code,
                "pointer": pointer,
                "detail": msg[:500],
            }
        )

    return create_problem_details(
        status=422,
        code="VALIDATION_FAILED",
        title="Dữ liệu yêu cầu không hợp lệ",
        detail="Một hoặc nhiều trường dữ liệu không vượt qua kiểm tra tính hợp lệ.",
        request=request,
        errors=field_errors,
        retryable=False,
    )
