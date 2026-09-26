---
document_id: "DOC-PROD-VISION-001"
version: "1.0.0"
status: "approved"
owner: "Product Management"
approvers: ["Product Owner", "Service Owner", "Architecture Owner"]
last_updated: "2026-09-21"
---

# Tầm nhìn sản phẩm

## Tuyên bố

Campus 24/7 là trung tâm dịch vụ sinh viên có AI, giúp sinh viên tra cứu thông tin có căn cứ, truy cập dữ liệu cá nhân theo quyền, thực hiện yêu cầu hành chính có xác nhận và chuyển giao an toàn cho cán bộ khi AI không nên hoặc không thể xử lý.

Sản phẩm đầu tiên phục vụ một trường duy nhất. `HUCE Demo` là cấu hình mô phỏng cho Khoa Công nghệ Thông tin, Trường Đại học Xây dựng Hà Nội và không phải dịch vụ chính thức của trường.

## Giá trị cốt lõi

1. **Trust before fluency** — đúng nguồn, đúng phiên bản và biết từ chối quan trọng hơn câu trả lời trôi chảy.
2. **Action with control** — hành động có preview, phân quyền, xác nhận, idempotency và audit.
3. **Human accountability** — AI hỗ trợ; trách nhiệm nghiệp vụ và quyết định nhạy cảm thuộc về con người.
4. **Privacy by design** — tối thiểu hóa dữ liệu và không dùng dữ liệu sinh viên thật trong mô phỏng.
5. **Measurable quality** — mọi thay đổi model, prompt, retrieval hoặc tool phải qua eval và release gate.
6. **Operable product** — có SLO, quan sát, runbook, chi phí và degraded mode; không chỉ là chatbot demo.

## Kết quả mong muốn

- Sinh viên có một điểm vào duy nhất cho câu hỏi, lịch, ticket, giấy tờ và đặt phòng.
- Cán bộ giảm câu hỏi lặp lại và nhận handover có đủ ngữ cảnh.
- Nhà trường kiểm soát nguồn tri thức, quyền truy cập và toàn bộ lịch sử hành động.
- Đội sản phẩm đo được chất lượng, adoption, chi phí và rủi ro theo từng phiên bản.

## Ranh giới

Campus 24/7 không chẩn đoán sức khỏe/tâm lý, không quyết định kỷ luật, điểm, tài chính hoặc ngoại lệ chính sách; không tự liên hệ cứu hộ; không thay thế hệ thống SIS/LMS; không tự phê duyệt yêu cầu; không phải nền tảng SaaS đa trường trong V1.

