---
document_id: "DOC-ADR-004"
version: "1.0.0"
status: "draft"
owner: "Data Architect"
approvers: ["Architecture Lead", "Backend Lead", "Security Lead", "Operations Lead"]
last_updated: "2026-09-21"
decision_status: "proposed"
---

# ADR-004 — PostgreSQL + pgvector là source of truth; Redis là ephemeral

## Context

V1 cần relational transaction cho ticket/action/audit/outbox, lexical search, vector search và LangGraph persistence. Quy mô chưa biện minh nhiều specialized datastore. Redis cần cho rate limit/cache nhưng không nên tạo durability path thứ hai.

## Decision

PostgreSQL là authoritative datastore cho business state, metadata, audit/outbox, lexical index, pgvector embeddings và durable checkpoints. Redis chỉ dùng cho cache/rate-limit/short-lived coordination có thể tái tạo.

Raw document/blob nằm ở S3; PostgreSQL giữ metadata/checksum/key. Production dùng RDS PostgreSQL version đã pin, xác minh pgvector support; AWS duy trì extension compatibility matrix riêng ([RDS extensions](https://docs.aws.amazon.com/AmazonRDS/latest/PostgreSQLReleaseNotes/postgresql-extensions.html)).

## Alternatives

- Dedicated vector database: từ chối V1 vì thêm consistency/security/operations surface; revisit khi benchmark không đạt.
- Redis as workflow/session truth: từ chối vì eviction/failover và domain durability.
- Object-only knowledge index: từ chối vì cần relational governance/versioning.

## Consequences

Transaction và backup đơn giản hơn, nhưng database chịu mixed OLTP/search load. Phải index/query budget, pool limit, partition/archive và benchmark. Scaling có thể yêu cầu read replica hoặc tách retrieval sau evidence.

## Constraints

- **MUST NOT** rely on Redis-only confirmation, ticket, consent, audit hoặc checkpoint.
- **MUST** use migrations, constraints và transaction boundaries.
- Vector/lexical schema **MUST** link tới immutable `document_version_id`.
- Redis outage **MUST** degrade, không corrupt truth.
- App **MUST** validate installed pgvector version before migration/deploy.

## Acceptance and failure

Required: restore drill, Redis-loss test, representative search benchmark, pool saturation test, migration rollback/forward plan. Nếu mixed workload làm OLTP SLO fail, mở ADR mới với measurements; agent không tự thêm database.

Traceability: `DEC-011`, `DEC-012`, `ARCH-002`, `ARCH-005`, `ARCH-007`; `SRC-POSTGRES-001`, `SRC-PGVECTOR-001`.

