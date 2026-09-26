---
document_id: "DOC-PROD-SCOPE-001"
version: "1.0.0"
status: "approved"
owner: "Product Management"
approvers: ["Product Owner", "Architecture Owner", "Delivery Owner"]
last_updated: "2026-09-21"
---

# Phạm vi và roadmap

## V1 — Commercial-quality simulated product

- Bốn vai trò cốt lõi và mock authentication.
- Chat tiếng Việt có streaming, citation, feedback và history.
- Hybrid RAG trên corpus tổng hợp có version/effective dates.
- Tool đọc lịch; tool ghi ticket, yêu cầu giấy tờ và đặt phòng mô phỏng.
- Preview/confirmation/idempotency/audit cho mọi write action.
- Controlled LangGraph và HITL queue.
- Staff, knowledge và operations portals.
- Privacy center mô phỏng export/deletion workflow.
- Docker local environment và AWS reference deployment.
- Eval, security, observability, CI/CD, backup/restore và runbooks.

## Ngoài V1

- SaaS/multi-tenancy, billing, CRM và marketplace.
- SIS/LMS/Entra ID thật; chỉ cung cấp adapter contract và migration path.
- Native mobile app, voice bot hoặc mạng xã hội.
- Quyết định điểm, kỷ luật, tài chính, y tế/tâm lý hoặc ngoại lệ chính sách.
- Tự động liên hệ cơ quan khẩn cấp.
- Fine-tuning hoặc huấn luyện foundation model.

## Trình tự capability

1. Governance, contracts và synthetic-data foundation.
2. Identity boundary, role model và audit.
3. Knowledge ingestion, retrieval, citation và eval baseline.
4. Chat orchestration và read-only schedule tool.
5. Ticket and document-request write workflows.
6. HITL/staff queue và sensitive-case guardrails.
7. Room booking, knowledge admin và operations dashboard.
8. Hardening, AWS deployment, UAT và commercial pilot review.

Không bắt đầu capability sau nếu release gate của foundation phụ thuộc chưa đạt.

