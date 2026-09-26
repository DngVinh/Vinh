---
document_id: "DOC-SVC-001"
version: "0.1.0"
status: "draft"
owner: "Service Design Lead"
approvers: ["Product Owner", "Operations Lead", "Security/Privacy Lead"]
last_updated: "2026-09-21"
---

# Service design index

## 1. Mục đích và phạm vi

Thư mục này là đặc tả chuẩn cho cách Campus 24/7 cung cấp dịch vụ từ đầu đến cuối cho `HUCE Demo`. Nó mô tả cả trải nghiệm số, công việc của cán bộ, hàng chờ, SLA, handover và xử lý trường hợp khẩn cấp. Đây là thiết kế cho một trường duy nhất theo `DEC-001`; agent triển khai MUST NOT thêm tenancy, billing SaaS hoặc onboarding nhiều trường.

V1 bao gồm các dịch vụ đã chấp nhận tại `DEC-005`: hỏi đáp có căn cứ, lịch cá nhân, ticket, yêu cầu giấy tờ, đặt phòng, HITL, hàng chờ cán bộ, quản trị tri thức và giám sát vận hành. Bốn vai trò hợp lệ được cố định bởi `DEC-006`.

## 2. Thứ tự đọc bắt buộc

Implementation agent MUST đọc theo thứ tự sau trước khi thực hiện task liên quan:

1. `docs/README.md` và toàn bộ `docs/00-governance/**`.
2. `SERVICE_CATALOG.md`.
3. `JOURNEYS_AND_BLUEPRINT.md`.
4. `OPERATING_MODEL.md`.
5. `QUEUES_AND_ROUTING.md`.
6. `SLA_CATALOG.md`.
7. `HANDOVER_AND_EMERGENCY_PLAYBOOK.md`.
8. `ESCALATION_AND_RESPONSIBILITIES.md`.
9. Tài liệu UX tương ứng trong `docs/03-ux/**`.

Nếu hai tài liệu mâu thuẫn, agent MUST áp dụng thứ tự ưu tiên trong `docs/README.md`, MUST dừng thay vì tự chọn, và MUST xuất blocker theo mẫu tại mục 6.

## 3. Danh mục tài liệu

| Tài liệu | Nội dung chuẩn | ID chính |
|---|---|---|
| `SERVICE_CATALOG.md` | Boundary và contract của từng dịch vụ | `SVC-CAT-*` |
| `JOURNEYS_AND_BLUEPRINT.md` | Student/staff journeys và service blueprint | `SVC-JRN-*`, `SVC-BP-*` |
| `OPERATING_MODEL.md` | Chế độ vận hành, lịch, cadence, dữ liệu và kiểm soát | `SVC-OPS-*` |
| `QUEUES_AND_ROUTING.md` | Queue taxonomy, routing, ownership, chống thất lạc | `SVC-QUE-*` |
| `SLA_CATALOG.md` | Priority, timer, target và phép đo | `SLA-*` |
| `HANDOVER_AND_EMERGENCY_PLAYBOOK.md` | HITL, sensitive case, emergency playbook | `HITL-*` |
| `ESCALATION_AND_RESPONSIBILITIES.md` | Ma trận escalation, RACI và nhiệm vụ cán bộ | `SVC-ESC-*`, `SVC-ROLE-*` |

## 4. Quy tắc chung

- Hệ thống MUST tự nhận diện là bản mô phỏng không chính thức theo `DEC-002` tại đăng nhập, trang giới thiệu và màn hình trợ giúp.
- Dữ liệu V1 MUST là dữ liệu tổng hợp theo `DEC-004`; giao diện hoặc tài liệu MUST NOT ngụ ý HUCE đã phê duyệt dịch vụ.
- AI MUST NOT tự ra quyết định ảnh hưởng quyền học tập, kỷ luật, tài chính, sức khỏe hoặc an toàn của sinh viên.
- Mọi phát biểu về quy định/thủ tục MUST có citation kiểm chứng được theo `DEC-013`.
- Mọi hành động ghi MUST có preview và xác nhận rõ ràng theo `DEC-015`.
- Mọi trường hợp nhạy cảm/khẩn cấp MUST đi qua policy deterministic và classifier theo `DEC-016`.
- AI MUST NOT bịa đầu mối, số điện thoại, giờ trực, SLA con người hoặc trạng thái cứu trợ.
- Hệ thống MUST cung cấp đường thoát sang ticket/handover khi AI không đủ căn cứ hoặc người dùng yêu cầu gặp cán bộ.

## 5. Launch blockers

Các mục sau không chặn phát triển bằng dữ liệu mô phỏng nhưng MUST chặn phát hành cho người dùng hoặc dữ liệu thật:

| Open question | Blocker | Điều kiện đóng |
|---|---|---|
| `OQ-001` | Chưa có Product Owner/approver chính thức | Có tên/chức danh, trách nhiệm và phê duyệt bằng văn bản |
| `OQ-002`, `OQ-007` | Chưa có owner và contract của tích hợp thật | Mỗi integration có owner, sandbox, data contract, auth và rate limit |
| `OQ-003` | Chưa có đầu mối khẩn cấp và giờ trực được duyệt | Configuration được hai vai trò nghiệp vụ/an toàn phê duyệt và kiểm thử |
| `OQ-004` | Chưa có Entra tenant/claim mapping | Identity mapping được Security và Identity Admin phê duyệt |
| `OQ-005`, `OQ-006` | Chưa chốt transfer/retention dữ liệu thật | Privacy/legal approval và cấu hình retention có test |
| `OQ-008` | Chưa có budget AWS/LLM | Hard budget, alert và owner được phê duyệt |

## 6. Failure contract cho implementation agent

Khi thiếu hoặc mâu thuẫn dữ liệu chuẩn, agent MUST dừng task và trả đúng cấu trúc sau; MUST NOT tạo placeholder ngầm trong production path:

```yaml
result: "blocked"
blocker_type: "missing_normative_input|conflicting_requirement|out_of_scope"
source_ids: ["OQ-003"]
affected_ids: ["HITL-EMR-001", "UX-EMR-001"]
evidence:
  - "Official emergency contact configuration is UNCONFIGURED."
safe_state: "Keep the emergency flow in launch-blocked simulation mode."
requested_decision: "Provide approved contacts, staffed hours and message templates."
```

## 7. Bằng chứng nghiệm thu tài liệu

Reviewer chỉ được chuyển bộ tài liệu sang `reviewed` khi có:

- kiểm tra mọi file có YAML control header hợp lệ;
- kiểm tra mọi ID là duy nhất và không tái sử dụng;
- ma trận liên kết `SVC -> SLA/HITL -> UX state` không có liên kết đứt;
- xác nhận không có số điện thoại hoặc địa chỉ khẩn cấp tự suy đoán;
- xác nhận tất cả human-response target chưa duyệt được gắn `PROVISIONAL_NOT_COMMITMENT`;
- xác nhận service/UX specs không mở rộng ngoài `DEC-005` và `DEC-006`;
- biên bản review của Product, Operations và Security/Privacy.

## 8. Căn cứ thiết kế

- `DEC-001`–`DEC-021`, `ASM-001`–`ASM-010`, `OQ-001`–`OQ-008`.
- GOV.UK Service Manual coi dịch vụ là toàn bộ những gì cần để người dùng đạt kết quả, không chỉ phần giao diện: <https://www.gov.uk/service-manual/service-assessments/what-a-service-is>.
- Hướng dẫn hỗ trợ người dùng chính thức yêu cầu ước lượng nhu cầu, xác định service level và đo hiệu năng hỗ trợ: <https://www.gov.uk/service-manual/helping-people-to-use-your-service/set-up-and-manage-user-support>.

