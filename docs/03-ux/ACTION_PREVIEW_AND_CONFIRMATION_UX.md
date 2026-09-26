---
document_id: "DOC-UX-006"
version: "0.1.0"
status: "reviewed"
owner: "Product Design Lead"
approvers: ["Security/Privacy Lead", "Service Design Lead", "Accessibility Lead"]
last_updated: "2026-09-21"
---

# Action preview và confirmation UX

## 1. Phạm vi

Áp dụng cho mọi write action: tạo ticket, gửi yêu cầu giấy tờ, booking request, handover, staff transfer/resolve, publish source và operations control. `DEC-015` yêu cầu preview + explicit confirmation. Chat phrase mơ hồ như “được”, “ok”, reaction emoji hoặc tiếp tục hội thoại MUST NOT được coi là confirmation.

## 2. State model

```text
editing -> validating -> preview_ready -> confirming -> processing
editing|validating -> validation_failed
preview_ready -> editing
preview_ready -> expired
processing -> succeeded|failed_no_effect|result_unknown
result_unknown -> reconciled_succeeded|reconciled_failed|staff_review
```

Agent MUST NOT implement transition trực tiếp `editing -> succeeded` hoặc `preview_ready -> succeeded`.

## 3. Preview contract

### UX-ACT-001 — Preview completeness

Preview MUST trình bày bằng structured fields, không chỉ paragraph do AI sinh:

```yaml
action_preview:
  action_type: "ticket.create|document_request.create|room_booking.create|handover.create|case.transfer|case.resolve|knowledge.publish|service_mode.change"
  actor_display: "string"
  recipient_or_target: "string"
  normalized_fields: []
  attachments: []
  consequences: []
  policy_or_fee_notes: []
  expected_status_after_submit: "string"
  published_sla_text: null
  confirmation_token_expires_at: "RFC3339"
  data_usage_summary: "string"
```

- Field order: action/recipient -> essential details -> consequences -> data usage -> expiry.
- Null/unknown MUST display explicitly and may block confirm depending validation; MUST NOT omit silently.
- AI MAY draft summary nhưng structured system values là authoritative.

### UX-ACT-002 — Service-specific fields

| Action | Required preview fields |
|---|---|
| Ticket | category, title/summary, queue, priority, attachment, published SLA if approved |
| Document request | request type, purpose, format/count if allowed, recipient, initial status |
| Room booking | room, date, start/end, timezone, purpose, approval status, cancellation rule |
| Handover | reason, queue, summary/transcript excerpts, citations, data shared |
| Case transfer | case ID, source/target queue, reason, SLA impact, ownership effect |
| Case resolve | case ID, resolution code, student-visible summary, follow-up effect |
| Knowledge publish | source/version/checksum, effective dates, eval result, affected corpus |
| Service mode | current/new mode, affected capabilities, reason, rollback owner |

Nếu field bắt buộc thiếu, confirm button MUST không thực thi; UI phải đưa back/edit hoặc blocker.

## 4. Explicit confirmation

### UX-ACT-003 — Confirmation control

- CTA label MUST nêu động từ + đối tượng: `Gửi yêu cầu`, `Xác nhận đặt phòng`, `Chuyển cho cán bộ`, `Xuất bản phiên bản`, `Chuyển sang chế độ an toàn`.
- Secondary action: `Quay lại chỉnh sửa` hoặc `Hủy`; MUST không dùng hai button cùng visual weight.
- High-impact staff/admin action SHOULD mở modal riêng; initial focus đặt vào safe/non-destructive control.
- Checkbox “Tôi đồng ý” chỉ dùng nếu có policy/legal reason; không thay thế button xác nhận.

### UX-ACT-004 — Confirmation token binding

UI MUST coi token là opaque, không lưu log/analytics. Token phải được backend bind actor, normalized payload hash, authorization/policy version, expiry và idempotency key theo `DEC-015`. Khi actor/payload/policy/permission thay đổi, UI MUST lấy preview/token mới.

### UX-ACT-005 — Expiry/revalidation

- Preview hết hạn -> `UX-STATE-019`, CTA `Kiểm tra lại`.
- Room availability, permissions, source version và queue config MUST được revalidate gần thời điểm execution.
- Revalidation làm thay đổi field/consequence -> quay về preview và highlight thay đổi; MUST không submit bằng consent cũ.

## 5. Processing và result

### UX-ACT-006 — Processing

- Sau activate, disable duplicate submit tại client nhưng idempotency là backend responsibility.
- Hiển thị action-specific status `Đang gửi yêu cầu…`; status announced một lần.
- Người dùng MAY rời trang nếu result có nơi theo dõi; UI phải nói nơi xem kết quả.
- Cancel processing chỉ xuất hiện nếu backend thực sự hỗ trợ cancellation; đóng modal không đồng nghĩa hủy request.

### UX-ACT-007 — Success

Success MUST lấy từ authoritative response và hiển thị reference ID, status, timestamp, next step và link detail. Copy MUST không vượt kết quả, ví dụ `Yêu cầu đã được gửi`, không phải `Yêu cầu đã được phê duyệt`.

### UX-ACT-008 — Failed with no effect

Chỉ dùng khi backend xác nhận không side effect. Giữ draft, giải thích cách sửa/retry; validation error focus đúng field. Retry MAY reuse draft nhưng phải obtain valid preview/token.

### UX-ACT-009 — Result unknown

Khi timeout/disconnect sau confirm mà chưa biết side effect:

- MUST hiển thị `Đang kiểm tra kết quả`, correlation/reference nếu an toàn.
- MUST disable `Gửi lại` trực tiếp.
- MUST query reconciliation bằng idempotency key.
- Nếu không resolve trong threshold, tạo `HITL-004`/operations case và cho người dùng link theo dõi.
- MUST NOT hiển thị generic “Thất bại, thử lại” nếu có khả năng action đã thành công.

### UX-ACT-010 — Edit/cancel

- Trước confirm: back/edit không side effect.
- Sau success: cancellation là action mới, chỉ xuất hiện nếu service contract hỗ trợ; cần preview/confirm riêng.
- Draft abandon MAY cần confirmation nếu có mất dữ liệu; không được gọi là “hủy yêu cầu” khi chưa có request.

## 6. Privacy và security

- Preview MUST ẩn secret/token; mask identifier theo privacy design nhưng đủ để người dùng nhận biết.
- Sensitive value không nên được đưa vào screenshot/analytics.
- Handover preview MUST cho phép xem excerpt được chia sẻ; system safety flags không được giả là lời người dùng.
- Confirmation event MUST audit actor/action/payload hash/policy/token ID/result, không audit raw token.
- Session/auth change invalidates preview.

## 7. Accessibility

- Preview dùng heading/definition list/table semantic phù hợp, không chỉ màu để chỉ field changed.
- Validation error summary focusable và links tới field.
- Modal tuân theo `UX-INT-040`; status/result dùng `role=status` hoặc phù hợp, tránh lặp announcement.
- Countdown expiry nếu hiển thị MUST không gây pressure; provide text và refresh path, không auto-submit.

## 8. Acceptance evidence và failure behavior

- State machine test cho mọi transition hợp lệ/bị cấm.
- Double click/network retry test chứng minh một side effect.
- Payload/token mutation/expiry/auth-change tests.
- Result-unknown reconciliation E2E test.
- Screenshots + keyboard/screen-reader evidence cho preview, validation, processing, success, unknown.
- Nếu backend không hỗ trợ preview/idempotency/reconciliation, frontend task MUST dừng; MUST NOT mô phỏng an toàn ở client.

