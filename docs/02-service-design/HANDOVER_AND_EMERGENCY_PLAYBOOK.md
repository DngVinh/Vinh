---
document_id: "DOC-SVC-007"
version: "0.1.0"
status: "draft"
owner: "Student Support Lead"
approvers: ["Security/Privacy Lead", "Product Owner", "University Safety Owner"]
last_updated: "2026-09-21"
---

# Handover và emergency playbook

## 1. Safety boundary

AI hỗ trợ điều hướng, không phải dịch vụ khẩn cấp, chuyên gia y tế, tư vấn tâm lý, pháp lý hoặc người ra quyết định. AI MUST NOT chẩn đoán, đánh giá chắc chắn ý định của người dùng, tuyên bố đã liên hệ/cứu hộ, hoặc tạo cảm giác có người theo dõi real-time khi điều đó chưa xảy ra.

Safety mode là thay đổi cách phản hồi và ưu tiên; việc tạo case/handover là side effect và vẫn MUST tuân theo `DEC-015`. Chưa có legal/policy approval cho silent handover hoặc tự liên hệ bên ngoài; agent MUST NOT tự thiết kế ngoại lệ.

## 2. Handover triggers

### HITL-001 — Người dùng yêu cầu

Các câu như “cho tôi gặp cán bộ”, nút `Gặp cán bộ`, hoặc chọn support channel MUST mở handover flow mà không yêu cầu classifier confidence. Hệ thống MAY hỏi chọn chủ đề nếu điều đó không gây trì hoãn rủi ro; người dùng có thể chọn `Không chắc`.

### HITL-002 — Thiếu hoặc mâu thuẫn bằng chứng

Trigger khi policy/procedure answer không đạt evidence threshold, nguồn mâu thuẫn/hết hiệu lực, hoặc yêu cầu cần phán quyết ngoại lệ. AI MUST abstain trước, sau đó đề xuất handover/ticket.

### HITL-003 — Ảnh hưởng quyền lợi

Trigger khi yêu cầu liên quan thay đổi điểm, kỷ luật, tài chính, eligibility, deadline exception, khiếu nại hoặc phê duyệt. AI MAY cung cấp quy trình có citation nhưng MUST NOT quyết định kết quả.

### HITL-004 — Tool/result uncertainty

Trigger khi side effect có kết quả không xác định, retry có thể gây trùng, authorization/configuration bất thường hoặc adapter trả response mâu thuẫn. Case MUST kèm correlation/idempotency ID, không kèm secret.

### HITL-005 — Sensitive/emergency signal

Trigger từ deterministic rules hoặc classifier cho nội dung tự hại, gây hại, bạo lực, quấy rối, đe dọa an toàn, sức khỏe/tâm lý hoặc tình huống khác được policy approved. Deterministic signal MUST NOT bị model hạ mức. Trigger không phải chẩn đoán hoặc xác nhận sự kiện.

### HITL-006 — Low-confidence routing

Nếu intent không rõ nhưng không nhạy cảm, hệ thống MAY hỏi tối đa một clarification ngắn. Sau đó route `student_support_general`; MUST NOT lặp vô hạn hoặc buộc người dùng mô tả nội dung nhạy cảm nhiều lần.

## 3. Handover payload

### HITL-007 — Minimum necessary context

```yaml
handover_case:
  case_id: "uuid"
  actor_subject_id: "internal-pseudonymous-id"
  source_service_id: "SVC-CAT-006"
  target_queue_id: "SVC-QUE-001"
  priority: "P0_CRITICAL|P1_HIGH|P2_NORMAL|P3_LOW"
  reason_codes: []
  user_summary: "student-visible summary"
  transcript_excerpt_ids: []
  citation_ids: []
  deterministic_flags: []
  classifier_output_ref: null
  action_result_ref: null
  data_classification: "personal"
  consent_or_policy_basis: "explicit_confirmation"
  routing_policy_version: "string"
  created_at: "RFC3339"
```

Rules:

- Transcript MUST mặc định chọn đoạn tối thiểu liên quan, không gửi toàn bộ lịch sử.
- `user_summary` MUST được hiển thị trong preview để người dùng sửa, trừ các flag hệ thống/audit không được giả là lời người dùng.
- Classifier output MUST là signal cho cán bộ, không là fact; UI phải gắn nhãn.
- Internal prompts, chain-of-thought, credentials và raw authorization tokens MUST NOT nằm trong payload.
- Sensitive queue MUST ẩn excerpt trên list view và chỉ tải sau authorization.

## 4. Handover lifecycle

### HITL-008 — Preview và confirmation

Trước khi tạo case, UI MUST cho biết:

- lý do chuyển;
- queue/đơn vị nhận ở mức đã được duyệt;
- nội dung tóm tắt và attachment sẽ gửi;
- priority dự kiến;
- giờ hỗ trợ/SLA chỉ khi approved;
- hành động `Xác nhận chuyển` và `Quay lại chỉnh sửa` tách biệt.

Nếu người dùng không xác nhận, không tạo case. Safety mode vẫn có thể hiển thị contact đã duyệt mà không đòi chia sẻ dữ liệu.

### HITL-009 — Persistence và acknowledgement

Hệ thống MUST persist case trước khi nói “đã chuyển”. Acknowledgement MUST gồm case ID, queue, timestamp và trạng thái `queued`. Notification failure không được đổi trạng thái persist. Persist failure MUST nói rõ “chưa thể chuyển yêu cầu”, giữ draft an toàn và đưa retry/kênh khác đã duyệt.

## 5. Emergency classification levels

| Level | Mô tả vận hành | Frontstage | Queue/escalation |
|---|---|---|---|
| `E0_NONE` | Không có safety signal | Flow bình thường | Theo intent |
| `E1_SENSITIVE` | Nhạy cảm nhưng không có dấu hiệu nguy cơ tức thời | Ngôn ngữ bình tĩnh, privacy disclosure, tùy chọn gặp cán bộ | P1/P2 restricted theo policy |
| `E2_URGENT` | Có dấu hiệu nguy cơ gần/tức thời theo rule approved | Dừng flow thường, hiển thị hướng dẫn đã duyệt và contact active; CTA handover ưu tiên | P0 restricted sau confirmation; operations alert |
| `E3_SYSTEM_SECURITY` | Rò rỉ dữ liệu hoặc side effect vượt quyền | Hạn chế chi tiết, xác nhận đã ghi nhận nếu thực sự persist | Security incident + safe mode consideration |

Agent MUST NOT thêm category y khoa hoặc ngưỡng ngôn ngữ cụ thể vào code nếu chưa có safety policy/eval được duyệt.

## 6. Emergency playbook

### Bước 1 — Detect và preserve context

- Chạy deterministic rules và classifier song song theo AI/security spec tương lai.
- Ghi policy version, trigger type và timestamp; MUST NOT log nhiều nội dung nhạy cảm hơn cần thiết.
- Không tiếp tục tool write flow đang dở; confirmation token chưa dùng MUST bị invalidate nếu context an toàn thay đổi.

### Bước 2 — Respond safely

- Dùng câu ngắn, bình tĩnh, không phán xét.
- Nêu rõ giới hạn: hệ thống AI không phải cơ quan khẩn cấp và không theo dõi real-time.
- Nếu contact config `approved_active`, hiển thị đúng label/value/hours; không diễn giải thêm.
- Nếu contact chưa cấu hình, demo chỉ được hiển thị banner `DEMO — chưa cấu hình đầu mối khẩn cấp chính thức`; public launch bị chặn.
- MUST NOT bịa số, dựa vào trí nhớ model hoặc dùng số từ nguồn không nằm trong approved configuration.

### Bước 3 — Offer immediate choices

- `Xem đầu mối hỗ trợ chính thức` nếu có config active.
- `Chuyển cho cán bộ` mở `HITL-008`.
- `Tiếp tục trò chuyện` MAY tồn tại nhưng không được che CTA an toàn.
- Không dùng dark pattern hoặc auto-submit.

### Bước 4 — Persist/route nếu đã xác nhận

- Tạo case idempotent tới `SVC-QUE-005`.
- Nếu restricted queue chưa configured, production MUST không khởi chạy feature; demo route simulator có nhãn rõ và không notification ra ngoài.
- Acknowledge theo `HITL-009`; không nói “đã báo cơ quan chức năng”.

### Bước 5 — Staff triage

- Chỉ staff được training và allowlist truy cập.
- Cán bộ kiểm tra context, thực hiện playbook tổ chức đã duyệt, ghi action/outcome.
- AI recommendation không thay thế đánh giá của cán bộ.
- Chuyển tuyến phải atomic, có reason và không làm mất P0 timer.

### Bước 6 — Close và review

- P0 closure cần resolution code, reviewer theo policy và student-visible summary phù hợp.
- Review false negative/positive bằng dữ liệu đã giảm định danh.
- Nếu playbook/config sai, tạo change request; MUST không sửa production prompt trực tiếp.

## 7. Contact configuration — launch blocker

Không có contact chính thức nào được phê duyệt tại thời điểm viết. Configuration chuẩn bắt buộc:

```yaml
emergency_contact_catalog:
  version: "UNCONFIGURED"
  locale: "vi-VN"
  institution: "HUCE Demo"
  contacts:
    - contact_id: "student_affairs"
      display_name: null
      channel: null
      value: null
      staffed_hours_text: null
      intended_use: null
      source_url: null
      source_owner: null
      verified_at: null
      effective_from: null
      effective_until: null
      approval_status: "UNCONFIGURED"
    - contact_id: "campus_safety"
      display_name: null
      channel: null
      value: null
      staffed_hours_text: null
      intended_use: null
      source_url: null
      source_owner: null
      verified_at: null
      effective_from: null
      effective_until: null
      approval_status: "UNCONFIGURED"
    - contact_id: "health_or_wellbeing"
      display_name: null
      channel: null
      value: null
      staffed_hours_text: null
      intended_use: null
      source_url: null
      source_owner: null
      verified_at: null
      effective_from: null
      effective_until: null
      approval_status: "UNCONFIGURED"
```

Validation MUST reject publish nếu `value` là placeholder, source/owner/verified date thiếu, effective range không hợp lệ, hoặc approval không phải `approved_active`. Contact hết hiệu lực MUST biến mất khỏi frontstage và tạo critical configuration alert.

## 8. Prohibited behavior

- Không yêu cầu người dùng mô tả thêm chi tiết gây hại chỉ để tăng classifier confidence.
- Không tranh luận, hạ thấp hoặc phủ nhận trải nghiệm của người dùng.
- Không dùng gamification, urgency giả hoặc countdown giả.
- Không hiển thị confidence score về nguy cơ cho sinh viên.
- Không tự gọi điện/email/SMS/cơ quan ngoài trường.
- Không hứa bảo mật tuyệt đối hoặc cam kết thời gian con người chưa approved.
- Không đánh dấu case resolved chỉ vì AI đã gửi một tin nhắn.

## 9. Acceptance evidence và failure behavior

### Evidence

- Scenario tests cho explicit handover, insufficient evidence, rights impact, tool uncertainty, E1/E2/E3.
- Negative tests chứng minh không có external contact/action khi chưa confirm.
- Snapshot chứng minh mọi contact là config-driven và demo placeholder không giống contact thật.
- Queue persist-before-ack test; idempotent retry test; restricted access test.
- Accessibility test cho safety alert, focus và keyboard.
- Red-team test prompt yêu cầu AI bịa số liên hệ phải bị từ chối.

### Failure behavior

- `OQ-003` mở -> production/public pilot gate MUST fail.
- Queue/contact config invalid -> không tạo cam kết giả; chuyển service mode phù hợp và alert Operations.
- Safety classifier unavailable -> deterministic rules vẫn chạy; nếu cả hai không khả dụng, disable generative chat và chuyển `search_ticket_only`.
- Persist unknown -> hiển thị `Đang kiểm tra kết quả`, reconcile bằng idempotency; MUST không tạo case thứ hai.

