---
document_id: "DOC-ADR-016"
version: "1.0.0"
status: "draft"
owner: "Domain Architecture Lead"
approvers: ["Product Owner", "Architecture Lead", "Security Lead", "Service Owner"]
last_updated: "2026-09-21"
decision_status: "proposed"
---

# ADR-016 — Preview, explicit confirmation và idempotency cho mọi write action

## Context

AI có thể hiểu sai intent/parameters; user retry, network timeout và graph resume có thể lặp side effect. Authorization tại lúc đề xuất có thể stale khi thực thi.

## Decision

Mọi user-visible write action **MUST** đi qua `Action Control`:

```text
normalize -> authorize -> preview -> explicit confirm
-> re-authorize -> idempotent execute -> audit -> result
```

Confirmation bind actor, action type, canonical payload hash, policy decision/version, expiry và nonce. Execute requires client `Idempotency-Key`; repeated key returns stored result/state, không tạo side effect mới.

Read-only tools không cần preview nhưng vẫn authz/audit theo classification. Administrative destructive/security changes không được tự động hóa bằng normal confirmation; chúng theo approval protocol riêng.

## Alternatives

- Model executes immediately after tool call: rejected by `DEC-014`/`DEC-015`.
- Generic “Bạn đồng ý?” không bind payload: từ chối vì payload swap/stale.
- Idempotency only client-side: từ chối vì client/network không đáng tin.

## Consequences

Thêm một bước UX và durable records nhưng ngăn accidental/duplicate writes, cho audit/reconciliation. Preview expiry/state conflict phải thiết kế rõ.

## Constraints

- Preview human-readable và canonical payload lưu/hash; confirmation **MUST NOT** nhận payload thay thế.
- Re-authorize ngay trước execute.
- Domain change, audit và outbox commit cùng transaction khi nội bộ.
- External unknown outcome có reconciliation, không blind retry.
- Idempotency record retention **MUST** dài hơn maximum retry/reconciliation window.
- Graph resume **MUST** không execute lại action completed.

## Acceptance and failure

Tests: changed payload, wrong actor, expired token, changed policy, duplicate same key, same key/different payload, concurrent confirmation, crash points và external timeout. Zero unconfirmed writes is release gate. Nếu audit/idempotency unavailable, write **MUST** fail closed.

Traceability: `DEC-014`, `DEC-015`, `DEC-020`, `ARCH-006`, `ARCH-008`.

