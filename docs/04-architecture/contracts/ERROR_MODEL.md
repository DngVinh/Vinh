---
document_id: "DOC-API-003"
version: "1.0.0"
status: "reviewed"
owner: "API Architect"
approvers: ["Solution Architect", "Security Lead", "Frontend Lead"]
last_updated: "2026-09-21"
---

# API error model

## 1. Chuẩn lỗi

API-ERR-001: mọi lỗi HTTP có body MUST dùng `application/problem+json` theo [RFC 9457](https://www.rfc-editor.org/rfc/rfc9457.html) và schema `contracts/json-schema/common/error.schema.json`.

```json
{
  "type": "https://campus247.example/problems/validation-failed",
  "title": "Dữ liệu không hợp lệ",
  "status": 422,
  "detail": "Một hoặc nhiều trường cần được sửa.",
  "instance": "urn:request:0199c9ac-4d7c-7f35-a1b2-1234567890ab",
  "code": "VALIDATION_FAILED",
  "request_id": "0199c9ac-4d7c-7f35-a1b2-1234567890ab",
  "retryable": false,
  "errors": [
    {"code": "REQUIRED", "pointer": "/subject", "detail": "Trường này là bắt buộc."}
  ]
}
```

## 2. Quy tắc trường

| ID | Rule |
|---|---|
| API-ERR-002 | `type` là stable absolute URI thuộc namespace sản phẩm; không thay đổi theo occurrence. |
| API-ERR-003 | `code` là stable `UPPER_SNAKE_CASE`; client branching chỉ dựa vào `status` + `code`, không parse `detail`. |
| API-ERR-004 | `title` là mô tả ngắn theo problem type; `detail` là safe occurrence guidance bằng tiếng Việt. |
| API-ERR-005 | `instance` là opaque request/resource occurrence URI, không chứa PII. |
| API-ERR-006 | `request_id` MUST khớp response header `X-Request-Id`. |
| API-ERR-007 | `retryable=true` chỉ khi cùng request có thể retry an toàn; write vẫn phải giữ nguyên idempotency key. |
| API-ERR-008 | `errors` chỉ dùng cho lỗi field-level cùng problem type, pointer là RFC 6901 JSON Pointer. |
| API-ERR-009 | Response MUST NOT chứa stack trace, SQL, internal hostname/path, provider raw message, token, secret hoặc chain-of-thought. |
| API-ERR-010 | Log nội bộ MAY chứa diagnostic code/reference nhưng vẫn phải redacted; client detail không được copy raw exception. |

## 3. Problem registry V1

| Code | HTTP | Type suffix | Retry | Khi dùng |
|---|---:|---|---:|---|
| `AUTHENTICATION_REQUIRED` | 401 | `authentication-required` | No | token missing/invalid/expired |
| `IDENTITY_PROVIDER_NOT_ALLOWED` | 403 | `identity-provider-not-allowed` | No | provider/environment mismatch |
| `ROLE_MAPPING_FAILED` | 403 | `role-mapping-failed` | No | claim role không map được |
| `FORBIDDEN` | 403 | `forbidden` | No | authenticated nhưng thiếu quyền |
| `RESOURCE_NOT_FOUND` | 404 | `resource-not-found` | No | absent hoặc intentionally concealed |
| `VALIDATION_FAILED` | 422 | `validation-failed` | No | request schema/business field invalid |
| `UNSUPPORTED_MEDIA_TYPE` | 415 | `unsupported-media-type` | No | content type unsupported |
| `PAYLOAD_TOO_LARGE` | 413 | `payload-too-large` | No | body/file exceeds configured limit |
| `VERSION_CONFLICT` | 409 | `version-conflict` | Conditional | stale `If-Match`; reread required |
| `INVALID_STATE_TRANSITION` | 409 | `invalid-state-transition` | No | command invalid for current state |
| `IDEMPOTENCY_KEY_REQUIRED` | 400 | `idempotency-key-required` | Yes | write missing key |
| `IDEMPOTENCY_KEY_REUSED` | 409 | `idempotency-key-reused` | No | same key, different fingerprint |
| `IDEMPOTENCY_IN_PROGRESS` | 409 | `idempotency-in-progress` | Yes | original request still processing |
| `ACTION_PREVIEW_EXPIRED` | 410 | `action-preview-expired` | No | confirmation too late |
| `ACTION_PREVIEW_ALREADY_USED` | 409 | `action-preview-already-used` | No | consumed/cancelled preview |
| `ACTION_CONFIRMATION_INVALID` | 403 | `action-confirmation-invalid` | No | invalid token/actor/hash |
| `POLICY_DENIED` | 403 | `policy-denied` | No | deterministic policy denial |
| `ROOM_SLOT_UNAVAILABLE` | 409 | `room-slot-unavailable` | No | conflict at execution time |
| `CITATION_UNRESOLVABLE` | 422 | `citation-unresolvable` | No | citation target invalid |
| `RATE_LIMITED` | 429 | `rate-limited` | Yes | quota exceeded |
| `DEPENDENCY_UNAVAILABLE` | 503 | `dependency-unavailable` | Yes | required integration unavailable |
| `INTEGRATION_NOT_ENABLED` | 503 | `integration-not-enabled` | No | real integration intentionally disabled |
| `EVENT_PUBLISH_FAILED` | 503 | `event-publish-failed` | Yes | only for synchronous admin operation requiring event evidence |
| `INTERNAL_ERROR` | 500 | `internal-error` | Conditional | unclassified safe fallback |

Code mới MUST được thêm vào registry và schema enum (nếu schema đóng), có owner, HTTP status và client recovery. Không reuse code cũ với meaning mới.

## 4. Error precedence

Khi nhiều lỗi cùng xảy ra, server SHOULD ưu tiên:

1. invalid transport/media/size;
2. authentication;
3. malformed schema;
4. authorization/concealment;
5. idempotency conflict;
6. optimistic concurrency;
7. state/business validation;
8. dependency/internal failure.

Server MUST NOT tiết lộ rằng resource tồn tại cho actor không có object permission. Trong trường hợp này trả `404 RESOURCE_NOT_FOUND`, nhưng audit nội bộ ghi `FORBIDDEN_CONCEALED`.

## 5. Retry behavior

- Client MUST honor `retryable` và `Retry-After` nếu có.
- `429`/`503` SHOULD có `Retry-After` khi server biết khoảng chờ.
- Retry write MUST gửi cùng `Idempotency-Key` và byte-equivalent semantic payload.
- `500` mặc định `retryable=false` trừ operation read-only hoặc outcome được chứng minh chưa commit.
- Timeout phía client không chứng minh server thất bại; client MUST query action/execution status hoặc retry cùng key.

## 6. Localization

`code` và `type` không localized. `title`/`detail` V1 là tiếng Việt; server MAY honor `Accept-Language` trong tương lai. Client MUST có fallback copy theo code nhưng không thay đổi semantic recovery.

## 7. Acceptance evidence và failure behavior

Mỗi registered problem cần contract fixture validate schema. Security tests MUST chứng minh không leak stack/provider/PII. Nếu exception chưa map, global handler trả generic `INTERNAL_ERROR`, log safe diagnostic reference và alert; agent MUST không trả raw exception để “dễ debug”.
