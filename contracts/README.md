---
document_id: "DOC-CONTRACTS-INDEX-001"
version: "1.0.0"
status: "approved"
owner: "Solution Architect"
approvers: ["Product Owner", "Architecture Lead", "Security Lead", "Data Lead"]
last_updated: "2026-09-22"
---

# Machine-Readable Contracts Index

Thư mục này chứa toàn bộ các hợp đồng máy đọc (machine-readable contracts) chuẩn của hệ thống Campus 24/7 (V1 — HUCE Demo). Toàn bộ danh mục hợp đồng đã được phê duyệt chính thức cho việc triển khai mô phỏng dữ liệu tổng hợp (synthetic implementation) theo quyết định của `TASK-DOC-CONTRACT-001`.

## 1. Cấu trúc thư mục

| Đường dẫn | Loại hợp đồng | Tiêu chuẩn | Mục đích |
|---|---|---|---|
| `openapi/v1/openapi.yaml` | HTTP API | OpenAPI 3.1 | Khế ước REST API cho web frontend và external caller |
| `asyncapi/v1/asyncapi.yaml` | Event Contract | AsyncAPI 3.0 | Khế ước sự kiện bất đồng bộ qua Transactional Outbox / SQS |
| `json-schema/**` | Wire Schemas | JSON Schema Draft 2020-12 | Dữ liệu chia sẻ: Actions, Citations, Config, Identity, Privacy, Tickets |
| `tools/**` | Tool Schemas | YAML Schema | Khế ước typed tools dành cho backend execution có kiểm soát |

## 2. Nguyên tắc quản trị

- **Bất biến ngữ nghĩa**: Không tự tiện bổ sung endpoint, operation hay schema property ngoài phạm vi V1.
- **Phục vụ trường duy nhất**: Tuyệt đối không thêm `tenant_id`, cơ chế thanh toán SaaS hay định tuyến đa trường học.
- **Chỉ dùng dữ liệu tổng hợp**: Mọi ví dụ, default value và fixture đều là synthetic data.
- **Xác thực tự động**: Toàn bộ hợp đồng phải vượt qua công cụ kiểm tra offline:
  ```powershell
  python contracts/tools/validate_openapi.py
  ```
