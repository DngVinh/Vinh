---
document_id: "DOC-UX-003"
version: "0.1.0"
status: "reviewed"
owner: "Product Design Lead"
approvers: ["Product Owner", "Accessibility Lead", "Service Design Lead"]
last_updated: "2026-09-21"
---

# Screen inventory

## 1. Screen contract

Mỗi screen implementation MUST hỗ trợ các state được liệt kê, authorization trước data fetch, heading/title, responsive layout, keyboard path và telemetry tối thiểu. “Screen” gồm full page, modal/drawer quan trọng hoặc workspace state có URL/context riêng.

## 2. Public và authentication

| ID | Route/surface | Outcome | Primary actions | Required states |
|---|---|---|---|---|
| `UX-SCR-001` | `/` landing | hiểu sản phẩm mô phỏng, khả năng/giới hạn | Đăng nhập, Xem trợ giúp | `UX-STATE-001`, `UX-STATE-007` |
| `UX-SCR-002` | `/login` | vào đúng auth mode | Đăng nhập demo; tương lai Entra | `UX-STATE-003`, `UX-STATE-007`, `UX-STATE-012` |
| `UX-SCR-003` | `/auth/error` | hiểu lỗi auth và cách phục hồi | Thử lại, Trợ giúp | `UX-STATE-007`, `UX-STATE-010` |
| `UX-SCR-004` | `/service-status` | biết service mode/incident công khai | Refresh, kênh hỗ trợ approved | `UX-STATE-006`, `UX-STATE-009`, `UX-STATE-011` |

## 3. Student screens

### UX-SCR-010 — Student dashboard `/app`

- Nội dung: lời chào không chứa dữ liệu nhạy cảm, next schedule items, open-ticket summary, service notice, quick actions.
- MUST hỗ trợ partial failure per widget; một widget lỗi không làm trắng toàn trang.
- States: `UX-STATE-001`, `UX-STATE-004`, `UX-STATE-006`, `UX-STATE-013`.

### UX-SCR-011 — Assistant `/app/assistant`

- Nội dung: AI disclosure, conversation list/current conversation, messages, composer, citations, stop/retry, handover.
- MUST phân biệt streaming, validating, completed, abstained, blocked, failed.
- MUST không render raw model tool calls/system prompt.
- States: `UX-STATE-002`, `UX-STATE-007`, `UX-STATE-008`, `UX-STATE-009`, `UX-STATE-012`.

### UX-SCR-012 — Citation detail drawer/modal

- Nội dung: source title, issuer, document number/version, section/page, effective dates, simulation label, excerpt và canonical link nếu có.
- Primary actions: `Mở nguồn`, `Báo nguồn có vấn đề`, `Đóng`.
- States: `UX-STATE-001`, `UX-STATE-005`, `UX-STATE-007`, `UX-STATE-013`.

### UX-SCR-013 — Personal schedule `/app/schedule`

- Views: day/week; filter tối thiểu; timezone và last sync.
- MUST có empty/error/stale riêng.
- States: `UX-STATE-001`, `UX-STATE-004`, `UX-STATE-006`, `UX-STATE-013`.

### UX-SCR-014 — Ticket list `/app/tickets`

- Content: status filters, ticket ID/title/type/status/updated/SLA only if approved.
- MUST không dùng color-only status.
- States: `UX-STATE-001`, `UX-STATE-004`, `UX-STATE-005`, `UX-STATE-007`, `UX-STATE-008`.

### UX-SCR-015 — New ticket `/app/tickets/new`

- Steps: category -> details -> attachments if allowed -> preview -> confirm -> result.
- MUST preserve valid input on validation/network failure; sensitive-field rationale.
- States: `UX-STATE-001`, `UX-STATE-003`, `UX-STATE-007`, `UX-STATE-008`, `UX-STATE-014`–`UX-STATE-019`.

### UX-SCR-016 — Ticket detail `/app/tickets/:ticketId`

- Content: ticket ID, current status, queue label, next step, timeline, student-visible messages, related references.
- Internal notes and hidden policy flags MUST NOT render.
- States: `UX-STATE-001`, `UX-STATE-007`, `UX-STATE-010`, `UX-STATE-013`.

### UX-SCR-017 — Document request `/app/document-requests/new`

- Reuses action pattern; language MUST be `Gửi yêu cầu`, not approval guarantee.
- States: same as `UX-SCR-015`.

### UX-SCR-018 — Room search/request `/app/rooms`, `/app/rooms/request`

- Content: date/time/timezone, capacity/attributes, availability timestamp, purpose, policy summary.
- Conflict and unknown-source MUST be distinct.
- States: `UX-STATE-001`, `UX-STATE-004`, `UX-STATE-007`, `UX-STATE-013`, `UX-STATE-014`–`UX-STATE-019`.

### UX-SCR-019 — Privacy center `/app/profile/privacy`

- Simulation content: data categories, retention assumption, conversation controls if implemented, request/export/delete explanation.
- MUST NOT expose controls unsupported by backend as if completed; label future/unavailable clearly.
- States: `UX-STATE-001`, `UX-STATE-007`, `UX-STATE-010`.

### UX-SCR-020 — Handover/safety surface

- May be inline panel or modal, but MUST follow `HITL-008`, `UX-HITL-*` and accessible dialog rules.
- Contact values only from `approved_active` config.
- States: `UX-STATE-014`–`UX-STATE-019`, `UX-STATE-020`.

## 4. Staff screens

### UX-SCR-101 — Queue overview `/staff/queues`

- Cards/table: queue, unassigned, at-risk, breached, oldest age, staffing status.
- `unknown` MUST not be `0`; restricted queue card MUST not leak content.
- Supports `UX-STATE-001`, `004`, `006`, `007`, `010`, `013`.

### UX-SCR-102 — Queue list `/staff/queues/:queueId`

- Filters: priority, status, breach risk, assignment, reason; URL MAY contain non-sensitive filters.
- Default sort per `QUEUES_AND_ROUTING.md`.
- PII columns minimal; restricted list redacted.

### UX-SCR-103 — Case workspace `/staff/cases/:caseId`

- Regions: case header/status, student-visible context, citation/evidence, timeline, reply composer, internal note, actions.
- Reply và internal note MUST visually/semantically distinct.
- Claim/transfer/resolve each need authoritative result; transfer/resolve require preview where consequence merits.
- States: claim conflict, lost permission, stale version, send unknown, restricted access.

### UX-SCR-104 — Restricted access gate

- Step-up/training/permission explanation; MUST NOT reveal case details before approval.
- Denial has audit reference/support path; no bypass CTA.

### UX-SCR-105 — Service report `/staff/reports/service`

- Metrics with definition, date range, denominator, freshness and provisional label.
- Small sensitive cohorts MUST be suppressed per privacy policy.

## 5. Knowledge screens

| ID | Route | Required content/action | Key failure state |
|---|---|---|---|
| `UX-SCR-201` | `/knowledge/sources` | source/status/owner/version/effective dates; add source | partial/empty/error |
| `UX-SCR-202` | `/knowledge/sources/new` | register/upload as draft, metadata validation | quarantine/invalid metadata |
| `UX-SCR-203` | source/version detail | provenance, parsing/chunks, citations, diff, audit | parser/injection suspicion |
| `UX-SCR-204` | `/knowledge/reviews` | eval evidence, approve/reject with reason | stale version/concurrent review |
| `UX-SCR-205` | `/knowledge/quality` | citation defects, expired/conflicting source | metrics unknown |

Publish MUST be a distinct action from upload; rejected/quarantined source MUST never appear as active.

## 6. Operations screens

| ID | Route | Required content/action | Prohibition |
|---|---|---|---|
| `UX-SCR-301` | `/operations` | service mode, health, queue risk, AI quality/cost summary | no unknown-as-green |
| `UX-SCR-302` | `/operations/incidents` | incident timeline, owner, severity, actions | no hidden unresolved SEV0/1 |
| `UX-SCR-303` | `/operations/controls` | safe mode/kill switch preview, confirmation, audit reason | no one-click irreversible toggle |
| `UX-SCR-304` | `/operations/audit` | filtered audit metadata, access-controlled detail | no secret/raw token/delete |
| `UX-SCR-305` | `/operations/configuration` | owner/calendar/contact/config status | no emergency contact publish if validation fails |

## 7. Global/system screens

| ID | Purpose | Required action |
|---|---|---|
| `UX-SCR-901` | 403/not authorized | quay về destination an toàn, request access/help nếu approved |
| `UX-SCR-902` | 404/not found | quay về relevant index; không ngụ ý authorization |
| `UX-SCR-903` | offline | xem dữ liệu cache có nhãn nếu an toàn, thử lại; write disabled |
| `UX-SCR-904` | maintenance/suspended | lý do công khai tối thiểu, status/help links đã duyệt |

## 8. Acceptance evidence và failure behavior

- Mỗi screen có route/role/state test và ảnh ở viewport 360, 768, 1440 pixel width.
- Critical student journeys có E2E keyboard-only và screen-reader evidence.
- Staff screens test với long Vietnamese content, empty, 1 item, 100+ items và permission loss.
- Không có state trong inventory nhưng thiếu định nghĩa trong `UI_STATE_MATRIX.yaml`.
- Nếu backend contract chưa hỗ trợ field/action, UI MUST không giả dữ liệu; agent dừng và raise contract blocker.

