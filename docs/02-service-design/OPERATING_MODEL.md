---
document_id: "DOC-SVC-004"
version: "0.1.0"
status: "draft"
owner: "Operations Lead"
approvers: ["Product Owner", "Student Support Lead", "Security/Privacy Lead"]
last_updated: "2026-09-21"
---

# Operating model

## 1. Mục tiêu

Mô hình này quy định cách con người, quy trình và hệ thống cùng vận hành Campus 24/7. “24/7” chỉ mô tả khả năng truy cập AI và self-service khi hệ thống khả dụng; MUST NOT được diễn giải thành có cán bộ trực 24/7 theo `ASM-008`.

## 2. Các chế độ dịch vụ

### SVC-OPS-001 — `normal`

- Điều kiện: auth, RAG, ticket và queue dependencies đạt health threshold; knowledge freshness hợp lệ.
- Cho phép: toàn bộ capability V1 theo quyền.
- Frontstage MUST hiển thị giờ hỗ trợ con người đã cấu hình và trạng thái mô phỏng.

### SVC-OPS-002 — `degraded`

- Trigger: một dependency không critical lỗi, latency/error budget vượt warning, hoặc dữ liệu cá nhân chỉ còn cache hợp lệ.
- Hành vi: giữ capability an toàn; disable capability phụ thuộc nguồn lỗi; hiển thị timestamp/staleness và đường thay thế.
- MUST NOT: biểu diễn dữ liệu stale như real-time; cho phép write nếu không thể xác minh kết quả.

### SVC-OPS-003 — `search_ticket_only`

- Trigger: LLM provider lỗi/rủi ro, eval regression critical, prompt/model bị đình chỉ, hoặc Product/Security kích hoạt safe mode.
- Cho phép: deterministic search, xem nguồn, tạo/theo dõi ticket và contact được duyệt.
- Cấm: sinh câu trả lời tự do, tool selection bằng model, model-based routing không có deterministic fallback.

### SVC-OPS-004 — `maintenance`

- Trigger: maintenance window được phê duyệt.
- Hành vi: read-only nếu an toàn; write action disabled; banner nêu thời gian bắt đầu/kết thúc dự kiến đã duyệt.
- MUST có rollback/abort owner; MUST NOT dùng maintenance như trạng thái mặc định cho sự cố chưa biết nguyên nhân.

### SVC-OPS-005 — `suspended`

- Trigger: nghi rò rỉ dữ liệu, authorization bypass, side effect vượt quyền, nguồn tri thức bị đầu độc, hoặc quyết định stop-service của Security/Product.
- Hành vi: chặn đăng nhập/feature theo phạm vi sự cố; bảo toàn audit; cung cấp thông báo tối thiểu và kênh hỗ trợ đã duyệt.
- Chỉ Incident Commander cùng Security Owner được phục hồi sau evidence kiểm chứng.

## 3. Operating ownership

### SVC-OPS-006 — Single accountable owner

Mỗi capability, queue, knowledge source, integration, dashboard, alert và runbook MUST có đúng một accountable owner và ít nhất một backup trước launch. Group chung không có người trực chịu trách nhiệm không đủ điều kiện.

Owner registry tối thiểu:

```yaml
service_ownership:
  product_owner: "UNASSIGNED"          # OQ-001
  operations_lead: "UNASSIGNED"
  student_support_lead: "UNASSIGNED"
  knowledge_lead: "UNASSIGNED"
  security_owner: "UNASSIGNED"
  privacy_legal_owner: "UNASSIGNED"
  identity_owner: "UNASSIGNED"
  platform_on_call: "UNASSIGNED"
```

Mọi giá trị `UNASSIGNED` là launch blocker cho production. Demo MUST dùng role label, không được giả tên người thật.

## 4. Giờ hoạt động và lịch trực

### SVC-OPS-007 — Business calendar

- Calendar MUST là configuration versioned gồm timezone, ngày làm việc, ca làm việc, ngày nghỉ và effective range.
- Timezone chuẩn hiển thị là `Asia/Bangkok` theo bối cảnh hiện tại; backend SHOULD lưu instant dạng UTC và timezone identifier.
- Human SLA timer MUST dùng calendar được publish tại thời điểm case được tạo và lưu `calendar_version`.
- Nếu calendar chưa duyệt, UI MUST chỉ nói “Yêu cầu đã được ghi nhận”; MUST NOT công bố deadline phản hồi.
- Thay đổi calendar MUST NOT sửa ngược deadline đã cam kết trừ incident/change được phê duyệt và thông báo.

## 5. Cadence vận hành

### SVC-OPS-008 — Mỗi ca/ngày làm việc

- Triage lead kiểm tra critical/high queue, unassigned cases, breach risk và failed notifications khi bắt đầu ca.
- Queue owner kiểm tra capacity ít nhất đầu và giữa ca.
- Operations kiểm tra service mode, dependency health và data freshness.
- Kết thúc ca phải handoff các case chưa xong với owner, next action và priority; MUST NOT để case chỉ nằm trong ghi chú cá nhân.

### SVC-OPS-009 — Hàng tuần

- Review backlog theo queue/reason, transfer rate, reopen rate, citation report và abstention.
- Knowledge Lead xử lý top missing/expired source; Product review top unmet need.
- Security review anomalous access/tool denial; Privacy review data-minimization sample khi có dữ liệu thật.
- Mọi action item MUST có owner, due date và evidence link.

### SVC-OPS-010 — Mỗi release/model/prompt/source change

- Chạy regression eval phù hợp.
- Review ảnh hưởng service/UX/SLA/security/privacy.
- Có rollback target và owner.
- Publish change log cho cán bộ nếu thay routing, queue hoặc xử lý case.
- Agent MUST NOT tự thay đổi prompt/model/policy production từ dashboard.

## 6. Capacity và demand

Planning baseline lấy từ `ASM-001`–`ASM-003`: 5.000 sinh viên, 100 cán bộ, 200 concurrent users, 10.000 chat requests/ngày, 1.000 ticket actions/ngày, 150–300 tài liệu và tối đa 100.000 trang/chunks stress-test.

- Đây là giả định capacity, MUST NOT được trình bày như số liệu HUCE thật.
- Trước pilot, Operations MUST thay bằng demand forecast và load-test evidence.
- Nếu queue arrival rate vượt processing capacity, hệ thống MUST tăng breach-risk alert và hiển thị kỳ vọng đã duyệt; MUST NOT hạ priority tự động để che backlog.

Nguồn tham khảo chính thức về lập kế hoạch hỗ trợ và phân nhóm demand: <https://www.gov.uk/service-manual/helping-people-to-use-your-service/set-up-and-manage-user-support>.

## 7. Data handling trong vận hành

- Staff MUST chỉ truy cập case thuộc queue/đơn vị được cấp quyền.
- Queue views MUST mặc định ẩn field nhạy cảm không cần cho triage.
- Export MUST bị tắt trong demo trừ task/requirement riêng; production export cần purpose, authorization và audit.
- Internal notes MUST không xuất hiện cho sinh viên hoặc được đưa vào LLM context mặc định.
- Conversation retention mô phỏng mặc định 90 ngày theo `ASM-007`; đây không phải policy production cho dữ liệu thật.
- Staff MUST NOT copy case sang email/chat cá nhân để xử lý.

## 8. Training và quyền thực thi

Trước khi role được kích hoạt, cán bộ MUST hoàn thành training theo phạm vi:

- Support officer: triage, privacy, citation verification, transfer/resolve, emergency limits.
- Knowledge admin: provenance, source lifecycle, injection/quarantine, eval gate.
- Operations admin: service modes, incident, audit, cost/quality dashboard.
- Security/privacy reviewer: access review, incident, data subject request và vendor boundary.

Training status MUST có expiry/review date. Role chưa đủ training MUST bị chặn khỏi action nhạy cảm thay vì chỉ cảnh báo.

NIST AI RMF nhấn mạnh vai trò, trách nhiệm, communication lines và training về rủi ro AI phải được ghi rõ: <https://www.nist.gov/publications/artificial-intelligence-risk-management-framework-ai-rmf-10>.

## 9. Acceptance evidence và failure behavior

### Bằng chứng bắt buộc

- owner registry không còn `UNASSIGNED` cho production scope;
- business calendar có version, approver và boundary tests;
- runbook drill cho `degraded`, `search_ticket_only` và `suspended`;
- queue shift-handover sample không có owner trống;
- access review và training completion report;
- dashboard phân biệt `unknown`, `zero`, `stale`.

### Failure behavior

- Thiếu owner/calendar/training/contact -> feature liên quan MUST ở `launch_blocked`.
- Telemetry thiếu -> health state `unknown`; MUST NOT tự coi là healthy.
- Không thể xác nhận side effect -> chuyển `result_unknown`, reconciliation job và staff alert.
- Runbook hoặc rollback chưa test -> release gate MUST fail.

