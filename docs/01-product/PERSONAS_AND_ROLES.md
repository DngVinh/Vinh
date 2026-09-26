---
document_id: "DOC-PROD-PERSONA-001"
version: "1.0.0"
status: "approved"
owner: "Product Management"
approvers: ["Product Owner", "Service Owner", "Security Owner"]
last_updated: "2026-09-21"
---

# Personas và vai trò

## PER-001 — Sinh viên

- Mục tiêu: tìm câu trả lời đúng, xem thông tin của mình, gửi và theo dõi yêu cầu nhanh.
- Rủi ro: tin vào câu trả lời sai; gửi nhầm dữ liệu; thao tác ngoài ý muốn; không nhận được người hỗ trợ.
- Quyền V1: đọc dữ liệu của chính mình; tạo/xem ticket của mình; xem preview và xác nhận yêu cầu; yêu cầu gặp cán bộ; quản lý consent và lịch sử phù hợp.
- Không có quyền: dữ liệu người khác, hàng chờ cán bộ, publish tri thức, cấu hình hệ thống.

## PER-002 — Cán bộ hỗ trợ

- Mục tiêu: nhận đúng hàng chờ, đủ ngữ cảnh, quản lý SLA và phản hồi có trách nhiệm.
- Quyền V1: xem case thuộc đơn vị/phân công; nhận/chuyển/escalate/resolve; xem citation và audit nghiệp vụ; soạn phản hồi.
- Không có quyền mặc định: sửa tri thức đã publish, thay guardrail, xem case ngoài phạm vi.

## PER-003 — Quản trị tri thức

- Mục tiêu: bảo đảm nguồn chính thức, còn hiệu lực, có provenance và có thể rollback.
- Quyền V1: upload/parse/review/publish/supersede tài liệu trong miền được giao; chạy test truy hồi; xem ảnh hưởng phiên bản.
- Hạn chế: publish nguồn rủi ro cao cần dual approval; không sửa audit lịch sử.

## PER-004 — Quản trị hệ thống/vận hành

- Mục tiêu: vận hành an toàn, đạt SLO, kiểm soát chi phí và sự cố.
- Quyền V1: cấu hình không chứa secret qua giao diện quản trị, xem metrics/traces đã redaction, quản lý role binding theo quy trình, kích hoạt degraded mode/kill switch.
- Hạn chế: không được đọc nội dung nhạy cảm chỉ vì có quyền vận hành; secret access tách riêng và audit.

## Không thuộc V1

Khách chưa đăng nhập, phụ huynh, giảng viên, cố vấn học tập và đối tác không có persona sản phẩm V1. Không được ngầm tái sử dụng vai trò cán bộ cho họ.

