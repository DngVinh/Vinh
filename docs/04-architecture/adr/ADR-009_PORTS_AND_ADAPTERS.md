---
document_id: "DOC-ADR-009"
version: "1.0.0"
status: "draft"
owner: "Integration Architect"
approvers: ["Architecture Lead", "Backend Lead", "Security Lead"]
last_updated: "2026-09-21"
decision_status: "proposed"
---

# ADR-009 — Ports/adapters cho simulation và institutional integrations

## Context

Không có SIS/SSO/booking/ticket API thật trong giai đoạn này (`OQ-004`, `OQ-007`), nhưng sản phẩm thương mại phải thay mock bằng integration thật mà không viết lại domain. Mock quá đơn giản sẽ che lỗi timeout/conflict/mapping.

## Decision

Mỗi external capability **MUST** có canonical typed port và ít nhất deterministic mock adapter. Production adapter về sau implement cùng contract và shared contract test. Composition root chọn adapter từ server config; domain không thấy vendor wire format.

Adapter là anti-corruption layer: auth, request mapping, response validation, normalization, error taxonomy, idempotency/reconciliation, metrics và redaction.

## Alternatives

- Mock HTTP server matching guessed vendor APIs: từ chối vì chưa có contract chính thức và dễ khóa sai assumptions.
- Direct integration logic trong service: từ chối vì coupling và khó test.
- Generic `execute(name, dict)` adapter: từ chối vì mất type/safety/traceability.

## Consequences

Thêm interfaces/mapping/test fixtures nhưng domain ổn định và simulation có giá trị. Production adapter vẫn bị block tới khi owner/API/sandbox approved.

## Constraints

- Mock dùng seeded deterministic data và injectable clock.
- Mock cover success/timeout/rate-limit/malformed/conflict/duplicate/unknown.
- Port method **MUST** nhận correlation/idempotency context khi cần.
- Adapter **MUST NOT** broaden data request ngoài canonical need.
- Unknown external write outcome có explicit state/reconciliation.

## Acceptance and failure

Shared contract suite pass; fixture provenance rõ; switching adapter requires config only. Nếu production API khác canonical semantics, mở change request/ADR; agent **MUST NOT** leak vendor field vào domain để “làm nhanh”.

Traceability: `DEC-004`, `DEC-007`, `OQ-004`, `OQ-007`, `ARCH-001`, `ARCH-008`.

