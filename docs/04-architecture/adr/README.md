---
document_id: "DOC-ADR-000"
version: "1.1.0"
status: "approved"
owner: "Architecture Lead"
approvers: ["Product Owner", "Security Lead", "Platform Lead"]
last_updated: "2026-09-22"
---

# Architecture Decision Record index

## 1. Usage contract

Mỗi ADR ghi một quyết định có chi phí thay đổi cao. `document status` quản lý artifact; `decision_status` trong từng ADR quản lý quyết định. Toàn bộ 16 ADR (ADR-001 đến ADR-016) được phê duyệt chấp thuận (`Accepted`) cho phạm vi triển khai synthetic implementation ngày 2026-09-22 theo `TASK-DOC-ARCH-001`.

Agent **MUST NOT**:

- tự đổi status;
- chọn phương án bị từ chối;
- dùng ADR `proposed` làm lý do mở rộng task;
- sửa ADR để khớp code đã viết;
- silently supersede quyết định.

Khi ADR mới thay ADR cũ, ADR cũ chuyển `superseded`, ghi ID thay thế và vẫn được giữ để audit.

## 2. Registry

| ADR | Decision | Current state |
|---|---|---|
| `ADR-001` | Modular monolith, ba runtime deployable | Accepted |
| `ADR-002` | Amazon ECS/Fargate, không Kubernetes V1 | Accepted |
| `ADR-003` | Next.js web và FastAPI application API | Accepted |
| `ADR-004` | PostgreSQL + pgvector là truth; Redis ephemeral | Accepted |
| `ADR-005` | Hybrid lexical/vector retrieval + rerank | Accepted |
| `ADR-006` | Controlled LangGraph workflow | Accepted |
| `ADR-007` | Provider-neutral LLM gateway, DeepSeek first | Accepted |
| `ADR-008` | SQS at-least-once + transactional outbox | Accepted |
| `ADR-009` | Ports/adapters cho integration và simulation | Accepted |
| `ADR-010` | REST/JSON + SSE; không WebSocket baseline | Accepted |
| `ADR-011` | Cache-aside có scope; cấm shared personal cache | Accepted |
| `ADR-012` | Single-region Multi-AZ, backup/restore DR | Accepted |
| `ADR-013` | Single institution; không multi-tenancy V1 | Accepted |
| `ADR-014` | AWS CDK TypeScript cho IaC | Accepted |
| `ADR-015` | Internal identity contract; mock → Entra OIDC | Accepted |
| `ADR-016` | Preview/confirmation/idempotency cho mọi write | Accepted |

## 3. Approval rule

Trước khi chấp nhận một ADR, reviewer **MUST**:

1. kiểm tra alignment với `DEC-*`, requirement và security/privacy controls;
2. đánh giá ít nhất các alternative đã ghi;
3. xác nhận operational owner và acceptance evidence;
4. tạo/update task/contract downstream;
5. ghi ngày và role phê duyệt qua document control.

Nếu một ADR phụ thuộc `OQ-*` chưa đóng, có thể chấp nhận cho synthetic implementation nhưng **MUST** ghi production gate rõ; không được xóa gate.

