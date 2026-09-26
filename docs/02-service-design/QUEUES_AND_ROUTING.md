---
document_id: "DOC-SVC-005"
version: "0.1.0"
status: "draft"
owner: "Student Support Lead"
approvers: ["Operations Lead", "Product Owner", "Security/Privacy Lead"]
last_updated: "2026-09-21"
---

# Queues và routing

## 1. Invariants

- Mọi case được persist MUST có đúng một `current_queue_id`; case active MUST có queue owner, có thể chưa có individual assignee.
- Priority MUST do deterministic policy quyết định; classifier chỉ cung cấp signal và MUST NOT hạ priority deterministic.
- Explicit user request for human MUST luôn tạo handover hợp lệ hoặc trả lỗi rõ; không được bị classifier từ chối.
- Transfer MUST atomic; source giữ ownership nếu target assignment không hoàn tất.
- Queue routing MUST có reason code và `routing_policy_version` để audit.
- Payload MUST tuân thủ data minimization; queue list MUST không hiển thị nội dung nhạy cảm không cần thiết.

## 2. Queue catalog

### SVC-QUE-001 — `student_support_general`

- Phạm vi: câu hỏi chung, unknown intent, hướng dẫn sử dụng, fallback không nhạy cảm.
- Owner: Student Support Lead (`UNASSIGNED` cho tới `OQ-001` được giải quyết).
- Cho phép: P2/P3; P0/P1 MUST chuyển queue chuyên trách hoặc escalation.

### SVC-QUE-002 — `academic_policy`

- Phạm vi: quy chế đào tạo, đăng ký học, lịch/thi, quyền lợi học tập, trường hợp cần diễn giải người thật.
- Owner: Academic/Training Management role (`UNASSIGNED`).
- Restricted fields: chỉ thông tin học vụ cần thiết; không tự đưa hồ sơ sức khỏe/kỷ luật.

### SVC-QUE-003 — `document_services`

- Phạm vi: xin giấy xác nhận và theo dõi yêu cầu giấy tờ.
- Owner: Document Service role (`UNASSIGNED`).
- Không có quyền: tự ký/phát hành giấy trong V1.

### SVC-QUE-004 — `facilities_room`

- Phạm vi: đặt phòng, xung đột, cơ sở vật chất.
- Owner: Facilities role (`UNASSIGNED`).
- Routing input: room/building/time/reference ID; MUST NOT kèm transcript ngoài ngữ cảnh cần thiết.

### SVC-QUE-005 — `safety_restricted`

- Phạm vi: self-harm risk, bạo lực, quấy rối, đe dọa an toàn, sức khỏe/tâm lý hoặc nội dung nhạy cảm được policy xác định.
- Owner: official Safety/Student Affairs role (`UNASSIGNED`, launch blocker `OQ-003`).
- Access: allowlist riêng; list preview MUST redact content; audit bắt buộc.
- Nếu chưa có owner/contact/staffing được phê duyệt, public launch MUST bị chặn.

### SVC-QUE-006 — `privacy_security`

- Phạm vi: nghi rò rỉ dữ liệu, unauthorized access, yêu cầu quyền dữ liệu, báo cáo bảo mật.
- Owner: Security/Privacy role (`UNASSIGNED`).
- Case security incident MUST được xử lý theo incident process, không chỉ ticket support.

### SVC-QUE-007 — `knowledge_quality`

- Phạm vi: citation hỏng, nguồn mâu thuẫn/hết hạn, câu trả lời sai có căn cứ, source ingestion issue.
- Owner: Knowledge Lead (`UNASSIGNED`).
- Có link tới retrieval/model/source versions; MUST không chứa dữ liệu cá nhân không cần.

### SVC-QUE-OPS-001 — `operations_fallback`

- Phạm vi: routing failure, queue configuration lỗi, orphan risk, notification failure, integration/result unknown.
- Owner: Operations Lead (`UNASSIGNED`).
- Đây không phải nơi giữ case vĩnh viễn; MUST có alert và target chuyển đúng queue.

## 3. Routing contract

Input chuẩn:

```yaml
routing_input:
  case_id: "uuid"
  actor_role: "student|support_officer|knowledge_admin|operations_admin"
  explicit_human_request: false
  deterministic_flags: []
  predicted_intent: "academic_policy"
  intent_confidence: 0.0
  source_service_id: "SVC-CAT-001"
  data_classification: "public|internal|personal|sensitive_personal"
  current_queue_id: null
  routing_policy_version: "string"
```

Thứ tự quyết định bắt buộc:

1. Security/privacy incident flag -> `SVC-QUE-006` và incident escalation.
2. Emergency/sensitive deterministic flag -> `SVC-QUE-005` nếu cấu hình hợp lệ; nếu chưa hợp lệ, launch-block hoặc demo-only safe message.
3. Explicit human request -> queue chuyên môn theo selected reason; confidence không được chặn.
4. Known transactional service -> `SVC-QUE-003` hoặc `SVC-QUE-004`.
5. Academic policy/rights impact -> `SVC-QUE-002`.
6. Knowledge/citation defect -> `SVC-QUE-007`.
7. Unknown/low-confidence không nhạy cảm -> `SVC-QUE-001`.
8. Missing/invalid queue config -> `SVC-QUE-OPS-001` + alert.

## 4. Confidence và ambiguity

- Confidence threshold là configuration được eval; agent MUST NOT hard-code giá trị chưa được AI Quality phê duyệt.
- Low confidence MUST tăng khả năng hỏi một clarification có giới hạn hoặc route general; MUST NOT tự đóng case.
- Nếu clarification làm tăng rủi ro hoặc trì hoãn emergency, bỏ clarification và thực hiện safety route.
- Nếu người dùng chọn category rõ ràng, selection đó ưu tiên classifier trừ deterministic security/safety rule.

## 5. Queue item states

```text
queued -> claimed -> in_progress -> waiting_student -> in_progress
in_progress -> resolved -> closed
queued|claimed|in_progress|waiting_student -> transferred -> queued(target)
any_active_state -> escalated
resolved -> reopened -> queued
```

Rules:

- `claimed` MUST có assignee và claim expiry/heartbeat policy.
- `waiting_student` chỉ dùng khi có câu hỏi cụ thể đã gửi; SLA pause chỉ theo `SLA-CAL-003`.
- `resolved` MUST có resolution code và student-visible summary.
- `closed` là terminal cho workflow hiện tại nhưng audit/history được giữ theo retention.
- Reopen MUST giữ parent timeline và có reason.

## 6. Sorting và fairness

Default queue ordering MUST dùng: priority -> breach risk -> oldest effective due time -> created time. Hệ thống MUST NOT xếp theo khả năng xử lý nhanh, giá trị sinh viên hoặc AI confidence. Manual pin/override cần reason và audit.

Batch action MUST NOT áp dụng cho reply, resolve, transfer restricted case hoặc thay priority. Bulk tagging read-only/administrative có thể được phép bằng requirement riêng.

## 7. Notification contract

- Notification là side effect độc lập và retry idempotent.
- Delivery failure MUST không đảo ngược ticket creation/transfer đã thành công.
- Staff UI là source of truth; email/push chỉ là thông báo, MUST không chứa dữ liệu nhạy cảm không cần.
- P0/P1 notification failure MUST tạo operations alert; MUST không tuyên bố người nhận đã thấy.

## 8. Acceptance evidence và failure behavior

- Table-driven tests cho toàn bộ thứ tự routing.
- Negative test chứng minh classifier không hạ emergency/security route.
- Concurrency test chứng minh claim/transfer không orphan hoặc double-owner.
- Access test cho `safety_restricted` và `privacy_security`.
- Data-minimization snapshot cho từng queue.
- Unknown queue/config test đi tới `operations_fallback` và phát alert.
- Nếu owner/allowlist của restricted queue chưa được phê duyệt, release gate MUST fail.

