---
document_id: "DOC-PROD-BUSINESS-001"
version: "1.1.0"
status: "reviewed"
owner: "Product Management"
approvers: ["Product Owner", "Finance Owner", "Service Owner"]
last_updated: "2026-09-22"
---

# Business case

## Vấn đề

Thông tin sinh viên phân tán giữa website, văn bản, phòng ban và hệ thống nghiệp vụ. Câu hỏi lặp lại vẫn cần cán bộ trả lời; ngoài giờ hành chính sinh viên khó biết nguồn nào đang hiệu lực hoặc yêu cầu phải gửi cho đâu. Chatbot FAQ thông thường không giải quyết được hành động, phân quyền, nguồn lỗi thời hoặc handover.

## Cơ hội thương mại

Sản phẩm cung cấp một lớp dịch vụ AI nằm trên các hệ thống sẵn có, giảm chi phí hỗ trợ cấp một và cải thiện trải nghiệm mà không buộc trường thay SIS/LMS. V1 chứng minh giá trị tại một trường; mở rộng thương mại chỉ được xem xét sau khi chất lượng, bảo mật và khả năng vận hành được chứng minh.

## Giả thuyết giá trị

| ID | Giả thuyết | Bằng chứng cần thu |
|---|---|---|
| OBJ-001 | Sinh viên tự giải quyết phần lớn câu hỏi thủ tục nếu câu trả lời có nguồn và đúng hiệu lực. | Answer coverage, grounded correctness, citation precision, CSAT. |
| OBJ-002 | Hợp nhất hỏi đáp và ticket làm giảm ticket lặp lại/sai tuyến. | Deflection, duplicate rate, routing F1, reassignment rate. |
| OBJ-003 | Preview và xác nhận cho phép tool-use mà không mất kiểm soát. | Confirmation coverage, unauthorized action count, duplicate side effects. |
| OBJ-004 | Handover có cấu trúc rút ngắn thời gian cán bộ hiểu vụ việc. | Time-to-first-action, handover completeness, staff feedback. |
| OBJ-005 | Quản trị nguồn theo phiên bản giảm câu trả lời dựa trên văn bản hết hiệu lực. | Stale-source incident rate, freshness SLA. |
| OBJ-006 | Product team học được từ feedback có cấu trúc và telemetry có thể tái lập thay vì tối ưu theo cảm tính. | Feedback coverage, verified-resolution rate, cohort analysis, experiment evidence. |
| OBJ-007 | Mọi trải nghiệm demo giữ ranh giới mô phỏng, an toàn và riêng tư có thể kiểm chứng. | Synthetic/disclaimer coverage, critical-control violation count, privacy-control compliance. |

## Kinh tế đơn vị

Theo dõi tối thiểu:

```text
cost_per_active_student = monthly_variable_cost / monthly_active_students
cost_per_resolved_session = total_ai_and_platform_cost / resolved_sessions
automation_saving = avoided_first_line_minutes * loaded_staff_minute_cost
net_operational_value = automation_saving - monthly_operating_cost
```

Không chốt giá bán trước khi có telemetry pilot. Mọi đề xuất giá phải tách phí nền tảng, usage, triển khai/tích hợp và hỗ trợ.

## Điều kiện tiếp tục đầu tư

Pilot chỉ được coi là thành công khi đồng thời đạt quality gate, không có vi phạm quyền nghiêm trọng, có tín hiệu sử dụng thực, cán bộ xác nhận giảm tải và chi phí trên phiên có xu hướng kiểm soát được. Adoption không được thay thế chất lượng và ngược lại.
