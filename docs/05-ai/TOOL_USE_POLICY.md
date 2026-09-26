---
document_id: "DOC-TOOL-001"
version: "1.0.0"
status: "reviewed"
owner: "Backend Architecture Lead"
approvers: ["AI Architecture Lead", "Security Architect", "Product Owner", "QA Lead"]
last_updated: "2026-09-21"
---

# Tool-use policy

## 1. Mô hình quyền

Tool là capability do application cung cấp. LLM chỉ tạo `ToolCandidate`; `ToolBroker` sở hữu validate, authorize, preview, confirmation, execution, idempotency và audit. Tool adapter MUST không nhận raw prompt hoặc model object.

```text
LLM/deterministic route
 -> candidate arguments (untrusted)
 -> schema validation
 -> semantic validation
 -> authorization(trusted actor context)
 -> [read: execute]
 -> [write: preview -> explicit confirmation -> reauthorize -> execute]
 -> normalized result
 -> response composer
```

## 2. V1 tool registry

Máy đọc tại `contracts/tools/tool-registry.yaml`. Tool IDs bất biến:

| Tool ID | Loại | Vai trò V1 | Confirmation |
|---|---|---|---|
| TOOL-SCHEDULE-001 `student_schedule_get` | read | student own; authorized staff scope | no |
| TOOL-TICKET-001 `ticket_create` | write | student/support officer | yes |
| TOOL-TICKET-002 `ticket_get` | read | owner/assigned authorized staff | no |
| TOOL-DOCUMENT-001 `document_request_create` | write | student/support officer | yes |
| TOOL-ROOM-001 `room_availability_search` | read | authenticated roles per policy | no |
| TOOL-ROOM-002 `room_booking_create` | write | authorized requester | yes |
| TOOL-HITL-001 `handover_create` | write safety | system/support flow | policy-controlled; emergency MAY use pre-approved system authority |

Không tool generic như `http_request`, `sql_query`, `shell`, `send_any_message`, `read_any_file` hoặc `execute_code` được đăng ký.

## 3. Atomicity và contract

- Mỗi tool thực hiện một business capability duy nhất.
- Input/output MUST validate theo schema ref trong registry.
- Input tool MUST không nhận `actor_id`, role, permission, tenant, approval flag hoặc arbitrary destination từ model. Broker inject trusted context riêng.
- `additionalProperties: false` bắt buộc.
- Tool version thay breaking behavior phải có ID/version mới hoặc formal migration; không đổi semantic âm thầm.
- Tool result MUST dùng normalized error/result envelope; adapter error/raw stack không đi vào prompt.
- Tool descriptions gửi model MUST mô tả khi dùng, required fields và giới hạn; MUST không tiết lộ internal authorization rule hoặc secret.

## 4. Authorization

Authorization decision input:

```text
trusted actor claims
+ tool_id/contract_version
+ normalized candidate arguments
+ resource attributes loaded server-side
+ policy version/current time
```

Decision output: `allow|deny|step_up_required`, reason code và policy version. Broker MUST reauthorize ngay trước execute write. Deny response MUST không xác nhận resource của người khác tồn tại.

Ví dụ invariants:

- student schedule luôn dùng subject từ trusted actor; input không có `student_id` tùy ý;
- ticket/document request `requester_id` do broker inject;
- `ticket_get` chỉ trả ticket owner hoặc staff assignment/scope;
- room booking requester/organization scope từ identity/context, không từ model;
- handover queue ID được map từ approved routing table, model chỉ cung cấp reason/category allowlisted.

## 5. Preview và confirmation

Write preview MUST chứa:

- `preview_id`, `tool_id`, `contract_version`;
- localized human-readable field/value summary;
- exact normalized payload hash;
- impact statement và recipient/queue không mơ hồ;
- expiry (baseline 10 phút, configurable);
- policy version;
- idempotency key reference;
- fields redacted theo viewer.

Confirmation token MUST ký server-side và bind actor, session/conversation, preview, payload hash, tool version, policy version và expiry. Free-text “đồng ý” chỉ được chấp nhận nếu UI/API chuyển thành explicit decision gắn đúng preview; model không tự diễn giải một câu mơ hồ thành confirmation.

Edit bất kỳ write field nào MUST invalidate preview/token và tạo preview mới.

## 6. Idempotency

- Idempotency key do server tạo trước execute, unique theo logical action.
- Key MUST stable qua transport retry/resume cùng action và khác khi payload đổi.
- Broker lưu state `reserved|in_progress|succeeded|failed_retryable|failed_final|uncertain` cùng payload hash.
- Duplicate với cùng key+hash MUST trả prior logical result.
- Cùng key khác hash MUST reject `IDEMPOTENCY_CONFLICT`.
- Adapter MUST truyền key/correlation tới upstream nếu hỗ trợ.
- Write timeout sau dispatch mà không biết kết quả MUST là `uncertain`; không retry với key mới, phải reconcile/handover.

## 7. Timeout và retry

Registry định nghĩa `timeout_ms`, `max_attempts`, `retry_safe` cho từng tool.

- Read tool: retry transient error tối đa registry cap với exponential backoff+jitter trong end-to-end deadline.
- Write tool: max attempt mặc định 1; retry chỉ với same idempotency key và adapter có verified idempotency/reconciliation.
- Validation, authorization, conflict, not-found và business-rule errors không retry.
- Circuit breaker theo integration/tool class; open circuit trả `DEPENDENCY_UNAVAILABLE`.
- Model không được quyết định retry count.

## 8. Audit

Mọi phase MUST emit append-only event theo `contracts/tools/audit-event.schema.yaml`:

```text
candidate_validated
authorization_decided
preview_created
confirmation_requested
confirmation_approved|rejected|expired
execution_started
execution_succeeded|failed|uncertain
result_disclosed
```

Audit event MUST có actor/ref, tool/version, request/turn/trace, payload hash, decision/reason, idempotency ref, timestamp và redaction metadata. MUST NOT chứa secret, auth token, raw prompt, chain-of-thought hoặc unredacted sensitive payload.

## 9. Normalized error codes

| Code | HTTP mapping tham khảo | User behavior |
|---|---:|---|
| `TOOL_INPUT_INVALID` | 422 | Hỏi lại field cụ thể, không execute. |
| `TOOL_AUTHORIZATION_DENIED` | 403/404 policy-dependent | Không tiết lộ resource. |
| `TOOL_STEP_UP_REQUIRED` | 401/403 | Yêu cầu auth step-up ngoài model. |
| `TOOL_CONFIRMATION_REQUIRED` | 409 | Render preview. |
| `TOOL_CONFIRMATION_INVALID` | 409 | Tạo preview mới nếu vẫn muốn. |
| `TOOL_CONFLICT` | 409 | Giải thích conflict an toàn. |
| `TOOL_NOT_FOUND` | 404 | Generic nếu ownership-sensitive. |
| `TOOL_RATE_LIMITED` | 429 | Retry later theo safe hint. |
| `TOOL_DEPENDENCY_UNAVAILABLE` | 503 | Degraded mode/ticket. |
| `TOOL_EXECUTION_UNCERTAIN` | 202/503 per API contract | Không retry; reconciliation/handover. |
| `TOOL_INTERNAL_ERROR` | 500 | Generic response + trace ID. |

## 10. Handover exception

`handover_create` là write nhưng critical safety handover không thể phụ thuộc user confirmation nếu approved safety policy cho phép system actor tạo queue item. Exception MUST:

- được explicit trong registry `confirmation.mode: policy_exception`;
- có policy rule/version và reason severity `critical|high`;
- chỉ tạo nội bộ, không gọi dịch vụ khẩn cấp bên ngoài;
- truyền tối thiểu transcript excerpt cần thiết, citation/tool refs và reason codes;
- không dùng contact chưa được cấu hình;
- vẫn idempotent và audited.

Nếu exception chưa được security/product approve, V1 MUST chỉ cung cấp safe response và hướng dẫn kênh cấu hình; không tự tạo handover.

## 11. Acceptance evidence

- schema conformance cho mọi input/output/error;
- negative auth tests cho IDOR/cross-user/cross-role;
- preview payload-hash tests;
- approve/reject/expire/replay/altered-payload confirmation tests;
- duplicate delivery và uncertain outcome tests;
- adapter timeout/circuit/reconciliation tests;
- audit sequence completeness và redaction tests;
- model fuzz output không thể thêm field/quyền/tool;
- zero direct network/database imports từ graph nodes.

## 12. Nguồn

DeepSeek mô tả function call là yêu cầu do model đề xuất, còn function thực tế do application cung cấp; arguments vẫn cần validate: [DeepSeek Tool Calls](https://api-docs.deepseek.com/guides/tool_calls/) và [Responses API](https://api-docs.deepseek.com/api/create-response/). LangGraph yêu cầu chú ý side effect trước interrupt vì node có thể chạy lại khi resume: [LangGraph Interrupts](https://docs.langchain.com/oss/python/langgraph/interrupts).

