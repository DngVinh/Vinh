---
document_id: "DOC-ADR-001"
version: "1.0.0"
status: "draft"
owner: "Architecture Lead"
approvers: ["Product Owner", "Backend Lead", "Operations Lead"]
last_updated: "2026-09-21"
decision_status: "proposed"
---

# ADR-001 — Modular monolith với ba runtime deployable

## Context

Sản phẩm có nhiều domain nhưng chỉ một người xây dựng với AI agents. Microservices sớm làm tăng số repository/pipeline, network failure, distributed transaction và observability burden. Một process duy nhất cho HTTP, ingestion và background job lại tạo contention và khó scale độc lập.

## Decision

Codebase **MUST** là modular monolith với bounded contexts trong `ARCH-003`, nhưng build/deploy thành:

- `web` Next.js;
- `api` FastAPI + request-time LangGraph;
- `worker` Python async/background runtime.

`api` và `worker` dùng cùng domain/application contracts từ cùng source revision. Module giao tiếp qua application ports/commands/events, không qua direct table/repository của nhau.

## Alternatives

- Microservices per domain: từ chối trong V1 vì operations/distributed-consistency cost không tương xứng tải giả định.
- One all-in-one container: từ chối vì HTTP và ingestion có scaling/failure profile khác nhau.
- Serverless function per action: chưa chọn vì SSE, LangGraph state, cold-start và local parity cần đánh giá riêng.

## Consequences

Tích cực: transaction đơn giản, refactor nhanh, một schema/pipeline chính, local development dễ. Tiêu cực: blast radius code lớn hơn, module boundaries cần automated fitness tests, deploy API có thể mang code không đổi của nhiều domain.

## Implementation constraints

- **MUST** enforce dependency direction bằng static/import tests.
- **MUST NOT** tạo service mới nếu chưa có ADR đo bằng load/team/security evidence.
- **MUST** tách worker process khỏi API request process.
- **MUST NOT** copy business rule giữa API và worker.

## Acceptance and failure

Accept khi import graph không cycle, domain unit tests không cần infrastructure và local compose chạy đủ ba runtime. Nếu task cần cross-module direct write hoặc một module không thể scale mà không scale toàn API, agent **MUST** báo architecture finding; không tự tách service.

Traceability: `DEC-003`, `DEC-011`, `ARCH-002`, `ARCH-003`.

