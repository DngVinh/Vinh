---
document_id: "DOC-SVC-006"
version: "0.1.0"
status: "draft"
owner: "Operations Lead"
approvers: ["Product Owner", "Student Support Lead", "Platform/SRE Lead"]
last_updated: "2026-09-21"
---

# SLA catalog

## 1. Phân biệt thuật ngữ

- **SLO hệ thống:** mục tiêu kỹ thuật cho availability/latency, được quy định chi tiết ở `docs/07-platform/**` khi tồn tại.
- **SLA hỗ trợ con người:** cam kết/target xử lý case theo business calendar.
- **Queue-delivery target:** thời gian hệ thống ghi và đưa case vào queue; không phải thời gian con người phản hồi.

Human SLA trong tài liệu này có trạng thái `PROVISIONAL_NOT_COMMITMENT` vì `ASM-008`, `ASM-009` và `OQ-001/OQ-003` chưa đóng. UI, email và marketing MUST NOT hiển thị chúng như cam kết trước approval.

## 2. Priority policy

### SLA-PRI-001 — `P0_CRITICAL`

- Điều kiện: nguy cơ an toàn tức thời theo deterministic policy; confirmed/credible active security or privacy breach; system-wide unauthorized side effect.
- Người dùng MUST NOT tự ép P0 chỉ bằng nội dung prompt; policy engine ghi reason/evidence.
- P0 không đồng nghĩa AI đã xác minh sự kiện ngoài đời.

### SLA-PRI-002 — `P1_HIGH`

- Điều kiện: nguy cơ ảnh hưởng gần tới quyền học tập/deadline; nhiều người bị chặn; restricted case không tức thời; integration lỗi gây mất dịch vụ trọng yếu.

### SLA-PRI-003 — `P2_NORMAL`

- Điều kiện: yêu cầu cá nhân chuẩn, cần cán bộ xử lý nhưng chưa có deadline gần hoặc rủi ro cao.

### SLA-PRI-004 — `P3_LOW`

- Điều kiện: góp ý, câu hỏi chung không gấp, yêu cầu cải tiến hoặc lỗi cosmetic.

Priority change MUST có actor, old/new value, reason code và timestamp. AI MAY đề xuất nhưng MUST NOT tự hạ priority; tăng priority theo deterministic rule được phép và phải audit.

## 3. System/queue targets đã chấp nhận cho simulation

| ID | Scope | Target | Window | Measurement |
|---|---|---:|---|---|
| `SLA-SYS-001` | Persist + enqueue case P0 | P95 ≤ 5 giây | 24/7 system availability | `queue_persisted_at - safety_triggered_at` |
| `SLA-SYS-002` | Persist + enqueue case P1–P3 | P95 ≤ 5 giây | 24/7 system availability | `queue_persisted_at - handover_confirmed_at` |
| `SLA-SYS-003` | Acknowledge ticket write result | P95 ≤ 10 giây hoặc `result_unknown` rõ ràng | service available | `response_at - confirmation_at` |
| `SLA-SYS-004` | Staff queue visibility after persist | P95 ≤ 5 giây | service available | `visible_at - queue_persisted_at` |

`SLA-SYS-001` chỉ chứng minh queue delivery theo `ASM-009`; MUST NOT được đổi thành “cán bộ phản hồi trong 5 giây”.

## 4. Human response targets dự thảo

| ID | Priority | First human response | Resolution target | Status |
|---|---|---:|---:|---|
| `SLA-HUM-001` | P0 | 5 phút trong staffed safety window | Theo playbook/owner | `PROVISIONAL_NOT_COMMITMENT` |
| `SLA-HUM-002` | P1 | 30 phút làm việc | 4 giờ làm việc hoặc kế hoạch xử lý | `PROVISIONAL_NOT_COMMITMENT` |
| `SLA-HUM-003` | P2 | 4 giờ làm việc | 2 ngày làm việc | `PROVISIONAL_NOT_COMMITMENT` |
| `SLA-HUM-004` | P3 | 1 ngày làm việc | 5 ngày làm việc | `PROVISIONAL_NOT_COMMITMENT` |

Các giá trị trên là baseline lập kế hoạch đã được người dùng chấp nhận ở giai đoạn discovery, nhưng MUST có demand/capacity evidence, owner, calendar và approver trước public display.

## 5. Timer semantics

### SLA-CAL-001 — Start

- Queue delivery: bắt đầu tại safety trigger hoặc handover confirmation như bảng.
- First response: bắt đầu khi case persist trong queue hợp lệ.
- Resolution: bắt đầu cùng thời điểm first-response timer, trừ loại case có contract khác được duyệt.

### SLA-CAL-002 — Stop

- First response dừng ở staff response có nội dung hành động, không phải auto-ack/claim/internal note.
- Resolution dừng ở `resolved` với resolution code và student-visible summary.

### SLA-CAL-003 — Pause

Resolution timer MAY pause ở `waiting_student` chỉ khi:

1. cán bộ đã gửi câu hỏi cụ thể;
2. người dùng được thông báo;
3. `pause_reason` và timestamp được lưu;
4. tổng pause được tính riêng.

Timer MUST NOT pause vì thiếu nhân sự, transfer nội bộ, incident nội bộ, chờ manager approval hoặc dependency do đội vận hành sở hữu.

### SLA-CAL-004 — Resume/reopen

- Sinh viên phản hồi -> resume theo cùng calendar version hoặc rule được duyệt.
- Reopen trong configured window -> tiếp tục case và metric `reopened`; MUST không xóa breach lịch sử.
- Case mới sau window -> link previous case nhưng dùng timer mới.

## 6. Business calendar

Schema chuẩn:

```yaml
sla_calendar:
  calendar_id: "HUCE_DEMO_BUSINESS_HOURS"
  version: "UNAPPROVED"
  timezone: "Asia/Bangkok"
  weekly_windows: []
  holidays: []
  effective_from: null
  effective_until: null
  approval_status: "UNCONFIGURED"
```

`weekly_windows` rỗng hoặc `approval_status != approved_active` MUST chặn công bố human SLA.

## 7. Breach warning và escalation

- `at_risk`: remaining effective time ≤ 25% target hoặc threshold theo queue được duyệt.
- `breached`: clock vượt target mà chưa stop.
- At-risk P0/P1 MUST notify assignee, queue lead và operations; unassigned case notify queue lead ngay.
- Breach MUST không tự đổi case thành resolved/closed hoặc hạ priority.
- Dashboard MUST hiển thị numerator/denominator và loại trừ có lý do; không được bỏ case breach khỏi denominator do transfer.

## 8. Metrics

```text
first_response_attainment = eligible_cases_met_first_response / eligible_cases
resolution_attainment = eligible_cases_met_resolution / eligible_cases
queue_delivery_p95 = p95(queue_persisted_at - handover_trigger_at)
unassigned_age = now - queue_persisted_at
reopen_rate = reopened_resolved_cases / resolved_cases
transfer_rate = cases_with_transfer / created_cases
```

Metric MUST phân đoạn theo queue, priority, calendar version và service mode; nhóm nhỏ/nhạy cảm phải áp dụng privacy threshold trước khi hiển thị.

## 9. Acceptance evidence và failure behavior

- Unit/property tests cho start/stop/pause/resume, holiday, timezone và DST-safe instant handling.
- Test auto-ack không dừng first-response timer.
- Test transfer không reset timer.
- Dashboard fixture chứng minh `unknown` khác `0` và denominator minh bạch.
- Copy audit chứng minh provisional SLA không xuất hiện như cam kết ngoài môi trường demo nội bộ.
- Thiếu calendar/owner/approval -> human deadline field MUST là `null` cùng reason `sla_not_published`; feature không được tự tính bằng hard-coded hours.

