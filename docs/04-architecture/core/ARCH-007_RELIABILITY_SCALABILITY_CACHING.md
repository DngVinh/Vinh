---
document_id: "DOC-ARCH-007"
version: "1.0.0"
status: "draft"
owner: "Reliability Architect"
approvers: ["Architecture Lead", "Operations Lead", "Security Lead", "Finance Owner"]
last_updated: "2026-09-21"
---

# ARCH-007 — Reliability, scalability và caching

## 1. Phạm vi và giả định tải

Đây là thiết kế theo capacity hypothesis, không phải cam kết hiệu năng. Baseline từ governance:

| ID | Giá trị thiết kế | Cách xác nhận |
|---|---:|---|
| `ASM-001` | 5,000 student, 100 staff, 200 concurrent users | Staging load test + pilot telemetry |
| `ASM-002` | 10,000 chat requests/day, 1,000 ticket actions/day | Traffic model và production metric |
| `ASM-003` | 150–300 documents, tối đa 100,000 parsed pages/chunks stress-test | Ingestion/retrieval benchmark |
| `ASM-006` | 99.9% monthly AI/read availability; RPO 15m; RTO 60m | SLO report + restore drill |

Agent **MUST NOT** chuyển các con số này thành hard-coded limits. Limit phải có config, error response, metric và owner.

## 2. Reliability principles

1. PostgreSQL là source of truth; cache/queue/provider đều có thể tạm thời mất hoặc duplicate.
2. Mọi dependency call **MUST** có timeout; retry **MUST** bounded, có jitter và phân loại lỗi.
3. Mọi side effect **MUST** idempotent hoặc có reconciliation state.
4. Hệ thống **MUST** degrade theo capability thay vì trả thông tin giả.
5. Readiness phản ánh khả năng nhận request; liveness chỉ phản ánh process health.
6. Retry budget **MUST** nằm trong end-to-end latency budget; không cho phép nested retries không kiểm soát.
7. Backpressure **MUST** ưu tiên giữ integrity: từ chối có cấu trúc tốt hơn nhận vô hạn rồi mất job.

## 3. Capability/degradation states

| State | Trigger | Capabilities allowed | Capabilities forbidden | Exit condition |
|---|---|---|---|---|
| `NORMAL` | Dependencies healthy | Tất cả capability được duyệt | None ngoài policy | Continuous health |
| `DEGRADED_NO_LLM` | Provider timeout/error/circuit open | Deterministic search, existing ticket/query, handover | Generated answer/tool planning mới | Probe success + cooldown |
| `DEGRADED_NO_INTEGRATION` | SIS/booking dependency down | FAQ, internal ticket, cached read nếu còn freshness | External write; stale schedule ngoài limit | Adapter health restored |
| `DEGRADED_ASYNC_BACKLOG` | Queue age/backlog vượt threshold | Synchronous read/write đã commit | New noncritical bulk ingestion nếu vượt quota | Backlog below recovery threshold |
| `READ_ONLY` | Risk với write path/audit/confirmation | Approved read operations | Tất cả write action | Operator clears incident after verification |
| `SEARCH_ONLY` | AI safety/quality kill switch | Approved knowledge search + citations | Generative answer và tool planning | Product/Security dual approval |
| `MAINTENANCE` | Planned migration hoặc unsafe schema | Health/status only | User operations | Migration/smoke accepted |

Capability state **MUST** được trả qua machine-readable endpoint cho UI và operations. UI **MUST NOT** suy đoán state chỉ từ HTTP error text.

## 4. Failure-mode matrix

| Dependency/failure | Detection | Immediate effect | Required behavior | Forbidden fallback |
|---|---|---|---|---|
| API task crash | ALB/ECS health | Một request có thể fail | Replace task; client retry only idempotent request | Retry write không key |
| PostgreSQL unavailable | DB timeout/readiness | Authoritative operations stop | Ready false; preserve queue; alert critical | Dùng Redis làm database |
| RDS failover | Connection reset/RDS event | Short read/write interruption | Reconnect bounded; idempotency protects retry | Infinite tight retry |
| Redis unavailable | Cache/lock error | Latency/rate limit impact | Bypass safe caches; fail security-sensitive controls theo security policy | Mặc định allow nếu rate-limit là security gate |
| SQS publish unavailable | Outbox age rises | Async effect delayed | Keep committed outbox; relay retries | Mark event published trước ACK |
| Worker poison message | Receive count/DLQ | One job blocked/repeated | Redrive to DLQ; quarantine; alert | Drop silently |
| S3 unavailable | Object error | Upload/ingestion blocked | Keep pending/failed state; retry bounded | Store durable object on container disk |
| DeepSeek outage | Timeout/error/circuit | Generative capability unavailable | `DEGRADED_NO_LLM` | Ungrounded template answer |
| DeepSeek malformed output | Schema validation | One inference invalid | Reject output; optional one repair within budget | Execute malformed tool args |
| External write unknown | Timeout after send | Outcome uncertain | Reconcile by provider key/status; mark unknown | Report success or resend blindly |
| Bad knowledge release | Eval/incident signal | Wrong retrieval risk | Roll back active corpus pointer | Delete old corpus/evidence |
| Audit write failure | Audit transaction error | Sensitive write blocked | Fail closed | Side effect then best-effort audit |

## 5. Scaling model

### 5.1 Web/API

- `web` và `api` **MUST** scale horizontally; session/workflow state ngoài process.
- Scale-out signal **SHOULD** kết hợp CPU/memory với request count/latency; một metric duy nhất phải được load-test chứng minh.
- Scale-in **MUST** cho phép connection drain. API task có SSE active **MUST** nhận shutdown signal, ngừng nhận stream mới và kết thúc/cancel stream trong grace period.
- Maximum task count **MUST** bị giới hạn bởi budget, DB connections và external-provider rate limit.

### 5.2 Worker

- Worker scale theo `ApproximateAgeOfOldestMessage`, backlog per active task và processing duration.
- Mỗi message class có concurrency/rate limit riêng; bulk ingestion **MUST NOT** starve critical handover/notification.
- Visibility timeout **MUST** lớn hơn expected processing hoặc worker phải extend heartbeat; SQS message có thể xuất hiện lại nếu chưa delete trước timeout ([SQS ReceiveMessage](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/APIReference/API_ReceiveMessage.html)).

### 5.3 PostgreSQL và retrieval

- Pool sizing formula:

```text
total_app_connections =
  web_db_connections
  + api_max_tasks * api_pool_size
  + worker_max_tasks * worker_pool_size
  + migration_and_admin_reserve
```

`total_app_connections` **MUST** nhỏ hơn tested database limit với safety reserve. `web_db_connections` phải bằng `0` trong baseline vì web không direct DB.

- Lexical/vector query **MUST** có query timeout, candidate cap và metadata filter trước/đồng thời phù hợp với index plan.
- HNSW index parameters và rerank candidate count chỉ thay đổi qua benchmark/eval, không bằng cảm tính. pgvector mô tả trade-off speed/recall và filtering/index behavior tại `SRC-PGVECTOR-001`.

## 6. Cache policy

### 6.1 Cache matrix

| Data | Layer | Key scope | TTL/invalidation | Allowed |
|---|---|---|---|---|
| Hashed static assets | CloudFront/browser | Build hash | Immutable/versioned | Yes |
| Public approved knowledge page | CDN/Next remote cache | `document_version_id` + locale | Purge/tag on corpus publish | Yes |
| Authenticated HTML/API | Shared CDN | N/A | `private/no-store` | No shared cache |
| Feature/config non-secret | Process/Redis | config version | Version change | Yes |
| Retrieval candidates | Redis optional | normalized query hash + corpus version + access scope + algorithm version | Short TTL; corpus publish invalidates | Yes nếu không chứa PII query/result |
| Final AI answer | Shared cache | N/A | N/A | No trong V1 |
| Personal schedule | Redis optional | opaque subject hash + date + source version | Very short TTL + explicit freshness | Only encrypted transport and no shared/public scope |
| Confirmation/action | PostgreSQL | action ID | Domain expiry | Redis không phải truth |
| Rate-limit counters | Redis | actor/IP/capability | Window TTL | Yes |
| Authorization decision | Process/Redis optional | actor claims version + resource + action + policy version | Very short; invalidate role/policy change | Only deny-safe design |
| LangGraph checkpoint | PostgreSQL | thread ID | Retention policy | Not Redis-only |

### 6.2 Mandatory cache rules

1. Cache key **MUST** include every dimension that changes authorization/content; nếu không chứng minh được, **MUST NOT** cache.
2. Cache entry **MUST** carry schema/version/freshness metadata.
3. Cache hit **MUST NOT** bypass authorization.
4. Negative caching chỉ cho deterministic not-found, TTL ngắn; **MUST NOT** cache transient denial/outage như permanent result.
5. Stale-while-revalidate **MUST NOT** dùng cho personal schedule hoặc policy có ngày hiệu lực nếu chưa có explicit business approval.
6. Next.js dynamic/user-specific pages **MUST** be private/no-store. Next.js official self-hosting guidance notes dynamic pages use private no-cache semantics and multi-instance cache needs shared coordination ([Next.js self-hosting](https://nextjs.org/docs/app/guides/self-hosting)).

## 7. Circuit breaker và retry budget

Mỗi outbound adapter config tối thiểu:

```yaml
timeout_ms: 5000
max_attempts: 2
backoff: "exponential_jitter"
circuit_failure_threshold: 5
circuit_open_seconds: 30
overall_deadline_ms: 8000
```

Đây là schema ví dụ, không phải giá trị production cố định. Giá trị thực phải theo endpoint và load test. Adapter **MUST** expose metrics: latency, outcome class, retry count, circuit state, rate-limit response. Secrets/PII **MUST NOT** nằm trong label.

## 8. Data recovery

- RDS PITR/backup, S3 versioning và application-level export phải có owner và retention.
- Redis restore không phải điều kiện phục hồi business truth.
- Queue DLQ redrive **MUST** kiểm tra idempotency và schema compatibility trước khi chạy.
- Restore drill **MUST** dùng môi trường tách biệt, đo từ backup selection tới end-to-end smoke pass.
- RPO/RTO chỉ được báo đạt khi có timestamped drill evidence; IaC/backup enabled không đủ.

## 9. Acceptance evidence

- Load model, scripts, environment configuration và raw result cho peak/soak/burst.
- Failure-injection evidence cho DB, Redis, queue, S3, LLM và external integration.
- Cache isolation tests giữa hai synthetic students và hai role scopes.
- Queue duplicate/out-of-order test và DLQ/redrive evidence.
- Restore drill report đo RPO/RTO.
- Dashboard/alerts cho availability, p95/p99 latency, error rate, queue age, DB pool saturation, cache hit, LLM failure/cost.

Nếu test không chứng minh capacity hoặc degradation, implementation **MUST** giữ feature flag off hoặc capacity status `unverified`; không được tăng con số trong tài liệu để “pass”.

## 10. Traceability

- Upstream: `ASM-001`–`ASM-009`, `DEC-003`, `DEC-009`, `DEC-012`–`DEC-016`.
- ADR: `ADR-002`, `ADR-004`, `ADR-005`, `ADR-008`, `ADR-011`, `ADR-012`.
- Downstream: SLOs, runbooks, load/chaos tests, cost controls.

