---
document_id: "DOC-DATA-003"
version: "1.0.0"
status: "reviewed"
owner: "Domain Architect"
approvers: ["Product Owner", "Solution Architect", "Operations Lead"]
last_updated: "2026-09-21"
---

# Entity lifecycles and state machines

## 1. Quy tắc chung

| ID | Quy tắc |
|---|---|
| DATA-LIFE-001 | State transition MUST được thực hiện bằng named domain command; CRUD update trực tiếp field `status` bị cấm. |
| DATA-LIFE-002 | Mỗi transition MUST kiểm tra current state, actor permission, business guard và expected version atomically. |
| DATA-LIFE-003 | Transition thành công MUST ghi audit và domain event trong cùng transaction. |
| DATA-LIFE-004 | Transition không hợp lệ trả `409 INVALID_STATE_TRANSITION`; stale version trả `409 VERSION_CONFLICT`. |
| DATA-LIFE-005 | Terminal state không được rời khỏi nếu sơ đồ không ghi transition rõ ràng. Reopen là command riêng, không phải sửa status. |

## 2. Ticket lifecycle (`DATA-LIFE-TICKET`)

### 2.1 States

`DRAFT`, `CONFIRMATION_REQUIRED`, `OPEN`, `ASSIGNED`, `IN_PROGRESS`, `WAITING_STUDENT`, `RESOLVED`, `CLOSED`, `ESCALATED`, `CANCELLED`.

`ticket-state.schema.json` là enum wire chuẩn. `DRAFT` và `CONFIRMATION_REQUIRED` MAY chỉ tồn tại trong action-preview domain; persistent Ticket bắt đầu ở `OPEN` sau confirmation. Nếu implementation chọn cách này, API vẫn MUST biểu diễn pre-creation state bằng `ActionPreview`, không tạo ticket giả.

### 2.2 Allowed transitions

| From | Command | To | Actor | Guard |
|---|---|---|---|---|
| `DRAFT` | `request_confirmation` | `CONFIRMATION_REQUIRED` | student/system | payload complete, policy allow |
| `CONFIRMATION_REQUIRED` | `confirm_create` | `OPEN` | same student | valid unused confirmation |
| `CONFIRMATION_REQUIRED` | `expire_or_cancel` | `CANCELLED` | system/same student | expired or explicit cancel |
| `OPEN` | `assign` | `ASSIGNED` | support officer/system router | valid queue + active assignee |
| `OPEN` | `escalate` | `ESCALATED` | authorized staff/system safety | reason required |
| `ASSIGNED` | `start_work` | `IN_PROGRESS` | assigned officer | ownership unchanged |
| `ASSIGNED` | `reassign` | `ASSIGNED` | queue manager | new assignee differs; event required |
| `ASSIGNED` | `escalate` | `ESCALATED` | authorized staff | reason required |
| `IN_PROGRESS` | `request_student_input` | `WAITING_STUDENT` | assigned officer | safe public prompt required |
| `WAITING_STUDENT` | `student_replied` | `IN_PROGRESS` | requester | non-empty reply |
| `IN_PROGRESS` | `resolve` | `RESOLVED` | assigned officer | resolution code + public summary |
| `RESOLVED` | `reopen` | `IN_PROGRESS` | requester/authorized officer | within configured reopen window + reason |
| `RESOLVED` | `close` | `CLOSED` | system/authorized officer | closure policy satisfied |
| `ESCALATED` | `assign_escalation` | `ASSIGNED` | escalation manager | active assignee + queue |
| `OPEN` | `cancel` | `CANCELLED` | requester | no irreversible work begun |

`CLOSED` và `CANCELLED` là terminal. Attempt transition khác MUST fail; không silently reopen.

### 2.3 State invariants

- `ASSIGNED`, `IN_PROGRESS`, `WAITING_STUDENT`, `RESOLVED` MUST có `assigned_user_id`.
- `RESOLVED` MUST có `resolution_code`, `resolution_summary`, `resolved_at`.
- `CLOSED` MUST có `closed_at` và trước đó từng ở `RESOLVED`, trừ migration được phê duyệt.
- `ESCALATED` MUST có reason code và destination queue.
- `CRITICAL` priority không tự động cam kết human response; chỉ đảm bảo routing theo ASM-009.

## 3. Action preview/execution lifecycle (`DATA-LIFE-ACTION`)

### 3.1 States

Preview: `PENDING_CONFIRMATION`, `CONFIRMED`, `EXECUTING`, `SUCCEEDED`, `FAILED`, `EXPIRED`, `CANCELLED`.

### 3.2 Transitions

| From | Command | To | Guard |
|---|---|---|---|
| none | `create_preview` | `PENDING_CONFIRMATION` | actor authenticated; normalized payload; policy `ALLOW_WITH_CONFIRMATION` |
| `PENDING_CONFIRMATION` | `confirm` | `CONFIRMED` | same actor, token valid, now < expiry, payload hash matches |
| `PENDING_CONFIRMATION` | `expire` | `EXPIRED` | now >= expiry |
| `PENDING_CONFIRMATION` | `cancel` | `CANCELLED` | same actor/system policy |
| `CONFIRMED` | `begin_execution` | `EXECUTING` | idempotency lock acquired |
| `EXECUTING` | `mark_success` | `SUCCEEDED` | target reference exists or external receipt stored |
| `EXECUTING` | `mark_failure` | `FAILED` | stable failure code + retry classification |

Terminal: `SUCCEEDED`, `EXPIRED`, `CANCELLED`; `FAILED` terminal cho cùng preview nếu outcome không chắc chắn. Nếu external timeout tạo ambiguous outcome, state MUST là `FAILED` với `COMPENSATION_REQUIRED` execution hoặc remain recoverable by reconciliation; không được tự replay side effect mù quáng.

### 3.3 Confirmation security

- Plain token MUST một lần, entropy tối thiểu 128 bit, không ghi log.
- Confirmation request MUST chứa `preview_id`, `confirmation_token` và `Idempotency-Key`.
- Server MUST so khớp actor từ auth context; body MUST NOT được phép chọn actor.
- Payload thay đổi dù một field MUST tạo preview mới.

## 4. Document request lifecycle (`DATA-LIFE-DOCUMENT`)

States: `DRAFT`, `PENDING_CONFIRMATION`, `SUBMITTED`, `VALIDATING`, `PROCESSING`, `READY`, `FULFILLED`, `REJECTED`, `CANCELLED`.

| From | To | Command/guard |
|---|---|---|
| `DRAFT` | `PENDING_CONFIRMATION` | complete catalog fields, policy allowed |
| `PENDING_CONFIRMATION` | `SUBMITTED` | valid action confirmation |
| `SUBMITTED` | `VALIDATING` | worker accepts exactly once |
| `VALIDATING` | `PROCESSING` | eligibility validated |
| `VALIDATING` | `REJECTED` | public reason code + safe detail |
| `PROCESSING` | `READY` | artifact/collection reference available |
| `READY` | `FULFILLED` | verified delivery/pickup acknowledgment |
| `DRAFT` / `PENDING_CONFIRMATION` / `SUBMITTED` | `CANCELLED` | actor authorized; no irreversible processing |

`FULFILLED`, `REJECTED`, `CANCELLED` terminal. V1 MUST NOT claim a simulated document is an official HUCE document.

## 5. Room booking lifecycle (`DATA-LIFE-BOOKING`)

Action preview covers draft/confirmation. Persistent booking states: `CONFIRMED`, `CANCELLED`, `COMPLETED`.

- `CONFIRMED -> CANCELLED`: requester or authorized staff, before start minus policy cutoff.
- `CONFIRMED -> COMPLETED`: system after end time; MAY be derived but event emitted once.
- Conflict check MUST execute atomically at confirmation, not only at preview.
- A preview does not reserve room. UI MUST disclose this and handle `409 ROOM_SLOT_UNAVAILABLE` at confirm.

## 6. Handover lifecycle (`DATA-LIFE-HANDOVER`)

States: `QUEUED`, `ASSIGNED`, `ACCEPTED`, `IN_PROGRESS`, `RESOLVED`, `RETURNED`, `CANCELLED`.

| From | To | Guard |
|---|---|---|
| none | `QUEUED` | queue exists; reason/risk/context minimized |
| `QUEUED` | `ASSIGNED` | active support officer in queue scope |
| `ASSIGNED` | `ACCEPTED` | same assignee acknowledges |
| `ACCEPTED` | `IN_PROGRESS` | same assignee starts work |
| `IN_PROGRESS` | `RESOLVED` | resolution reference + summary |
| `ASSIGNED` / `ACCEPTED` / `IN_PROGRESS` | `RETURNED` | reason + destination/requeue decision |
| `RETURNED` | `QUEUED` | routing corrected, retry count below limit |
| `QUEUED` | `CANCELLED` | duplicate or user withdrawal; not critical unresolved case |

`RESOLVED` và `CANCELLED` terminal. Critical handover MUST NOT auto-cancel on timeout; it escalates via operations policy.

## 7. Knowledge document lifecycle (`DATA-LIFE-KNOWLEDGE`)

States: `DRAFT`, `VALIDATING`, `READY_FOR_REVIEW`, `APPROVED`, `PUBLISHED`, `SUPERSEDED`, `REJECTED`, `FAILED`.

| From | To | Guard |
|---|---|---|
| none | `DRAFT` | source owner/provenance recorded |
| `DRAFT` | `VALIDATING` | immutable content checksum stored |
| `VALIDATING` | `READY_FOR_REVIEW` | malware/OCR/schema/chunk checks pass |
| `VALIDATING` | `FAILED` | machine validation fails with code |
| `READY_FOR_REVIEW` | `APPROVED` | knowledge admin distinct review action |
| `READY_FOR_REVIEW` | `REJECTED` | reviewer reason required |
| `APPROVED` | `PUBLISHED` | effective dates valid; index ready; authorized publisher |
| `PUBLISHED` | `SUPERSEDED` | replacement published atomically |
| `FAILED` | `VALIDATING` | new validation run; content unchanged or new version created |

Content bytes MUST be immutable after checksum. Any byte change creates new `DocumentVersion`; state rollback không được mutate published content.

## 8. Conversation lifecycle (`DATA-LIFE-CONVERSATION`)

States: `ACTIVE`, `HANDED_OVER`, `CLOSED`, `ARCHIVED`.

- `ACTIVE -> HANDED_OVER` khi handover được queue thành công.
- `HANDED_OVER -> ACTIVE` chỉ khi handover resolved và user tiếp tục bot session mới/được phép.
- `ACTIVE|HANDED_OVER -> CLOSED` do user hoặc inactivity policy; close không xóa message.
- `CLOSED -> ARCHIVED` theo retention job.
- `ARCHIVED` terminal trong V1; restore cần future contract.

## 9. Acceptance evidence và failure behavior

Mỗi state machine MUST có table-driven tests cho mọi allowed transition và ít nhất một denied case cho mọi state. Concurrency tests MUST chứng minh expected-version guard. Nếu requirement khác yêu cầu transition không có ở đây, agent MUST dừng với `STATE_MACHINE_GAP` và nêu entity, current state, requested command, expected state và requirement ID.
