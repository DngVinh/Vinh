---
document_id: "DOC-UX-007"
version: "0.1.0"
status: "reviewed"
owner: "Product Design Lead"
approvers: ["Accessibility Lead", "Operations Lead", "Frontend Lead"]
last_updated: "2026-09-21"
---

# Loading, empty, error, offline và recovery states

## 1. State precedence

Khi nhiều state cùng đúng, áp dụng precedence:

```text
suspended/security block
> emergency safety surface
> not_authorized/auth_required
> result_unknown
> offline
> degraded/partial/stale
> recoverable error/rate limit
> loading/processing
> empty/zero results
> ready/success
```

Agent MUST không che state ưu tiên cao bằng skeleton, empty state hoặc cached success.

## 2. State catalog

### UX-STATE-001 — Initial loading

- Dùng skeleton có shape gần content hoặc status text; không dùng skeleton cho duration vô hạn.
- Giữ page title/navigation; `aria-busy=true` trên region phù hợp.
- Nếu quá timeout threshold từ platform contract, chuyển recoverable error/degraded, không quay spinner vô hạn.

### UX-STATE-002 — AI generating/validating

- Hiển thị `Đang soạn câu trả lời…` rồi `Đang kiểm tra nguồn…` khi backend thực sự có phase.
- Citation/action CTA inactive cho tới completed.
- Cho phép stop generation; partial text có nhãn incomplete.

### UX-STATE-003 — Form submitting/validating

- Button phản hồi ngay, ngăn duplicate UI activation.
- Field không bị xóa; validation message chỉ khi có result.

### UX-STATE-004 — True empty

- Áp dụng khi request thành công và collection thật sự rỗng.
- Nêu ý nghĩa và next action; ví dụ lịch rỗng khác lỗi đồng bộ.
- MUST không hiện empty khi chưa fetch hoặc permission unknown.

### UX-STATE-005 — Zero search/filter results

- Nêu query/filter không có kết quả; CTA xóa filter/sửa từ khóa.
- Không gợi ý rằng dữ liệu tổng thể rỗng.

### UX-STATE-006 — Partial data

- Render phần thành công; mỗi region lỗi/stale có label và retry riêng.
- Global summary nêu dữ liệu chưa đầy đủ; MUST không tính metric aggregate như complete.

### UX-STATE-007 — Recoverable error

- Message gồm điều gì không làm được, dữ liệu/action có bị ghi không, user làm gì tiếp theo, support reference.
- Retry bounded; không xóa input.
- Technical detail/log ID MAY expandable cho staff, không expose stack/secret cho student.

### UX-STATE-008 — Rate limited/busy

- Nêu hệ thống đang bận, thời điểm thử lại chỉ khi server cung cấp `Retry-After`/approved value.
- Write action sau confirm phải kiểm tra result unknown trước retry.
- MUST không đổ lỗi người dùng.

### UX-STATE-009 — Degraded/safe mode

- Persistent banner nêu capability unavailable và alternatives.
- Không dùng màu xanh/“hoạt động bình thường”.
- Search/ticket paths vẫn dùng nếu healthy.

### UX-STATE-010 — Not authorized

- Không render protected data trước/đằng sau overlay.
- Nêu không có quyền và safe navigation/help; không gợi ý bypass.
- Audit/reference only if policy allows.

### UX-STATE-011 — Maintenance/suspended

- Maintenance: planned status, approved timeframe/status link.
- Suspended: public-safe explanation, no root cause leak, approved support link.
- MUST không tự tính recovery time.

### UX-STATE-012 — Authentication required/expired

- Giải thích đăng nhập cần thiết/hết hạn; preserve safe destination/draft.
- Sau login re-authorize/revalidate; account switch không expose draft trước.

### UX-STATE-013 — Stale data

- Hiển thị `Cập nhật lần cuối <timestamp>` và reason if known.
- Stale schedule MAY read-only; stale room availability MUST không cho confirm trước recheck.
- Unknown timestamp -> `Chưa xác định thời điểm cập nhật`, không dùng “vừa xong”.

### UX-STATE-014 — Action preview ready

- Structured preview đầy đủ; confirm/edit actions; expiry visible nếu hữu ích.

### UX-STATE-015 — Action processing

- Persistent processing status; no duplicate submit; leaving-page guidance.

### UX-STATE-016 — Action succeeded

- Reference/status/time/next step; language accurately reflects result.

### UX-STATE-017 — Action failed, no effect

- Chỉ khi authoritative no-side-effect; giữ draft và safe retry.

### UX-STATE-018 — Action result unknown

- `Đang kiểm tra kết quả`; reconcile; no immediate resend; route ops/HITL if unresolved.

### UX-STATE-019 — Preview expired/revalidation changed

- Explain need to recheck; highlight changed values; obtain new confirmation.

### UX-STATE-020 — Emergency configuration unavailable

- Demo only: `DEMO — chưa cấu hình đầu mối khẩn cấp chính thức`; no fake contact.
- Public/real-user environment MUST be launch-blocked, not merely show this state.

### UX-STATE-021 — Offline

- Persistent offline indicator; cached content has timestamp/stale label.
- Disable external/write actions; keep local draft if privacy-safe.
- Reconnect revalidates, never auto-submits.

## 3. Error copy schema

```yaml
error_message:
  title: "Điều không thể hoàn tất"
  impact: "Dữ liệu/yêu cầu đã hay chưa được ghi"
  recovery_actions: []
  support_reference: "non-secret correlation id or null"
  technical_details_staff_only: null
```

Copy MUST NOT dùng chỉ `Có lỗi xảy ra`, `Invalid request`, `Unknown error` hoặc stack trace.

## 4. Retry policy UX

- Read retry MAY immediate, exponential/backoff do platform quyết định.
- Pre-confirm validation retry safe.
- Post-confirm retry MUST depend on authoritative no-effect or idempotent reconciliation.
- UI MUST not implement hidden infinite auto-retry.
- Sau bounded failures, cung cấp safe alternative/hand-over; không lặp CTA duy nhất.

## 5. Offline/cache privacy

- Sensitive staff/restricted case content MUST NOT be stored for offline unless separate security approval.
- Student cached data MUST be scoped to current account and cleared on logout/account switch.
- Service worker/browser cache MUST NOT cache auth callback, confirmation token, raw API response with sensitive data or audit pages.
- Offline indicator MUST be visible before user relies on stale data.

## 6. Acceptance evidence và failure behavior

- Story/screenshot fixture cho 21 states trên relevant screens.
- State precedence tests, đặc biệt suspended vs cached success và result_unknown vs generic error.
- Network simulation: slow, timeout, disconnect-after-confirm, reconnect, 401/403/404/409/429/5xx.
- Accessibility: status announced once, focus moved only when needed, retry reachable.
- Nếu backend error không cho biết effect status sau write, map `UX-STATE-018`; MUST NOT map `UX-STATE-017`.

