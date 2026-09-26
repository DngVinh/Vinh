---
document_id: "DOC-QUAL-007"
version: "1.0.0"
status: "reviewed"
owner: "Performance and Resilience Engineering Lead"
approvers: ["SRE Lead", "Architecture Lead", "Security Lead", "Release Owner"]
last_updated: "2026-09-22"
---

# Performance and resilience test plan

## 1. Reference workload

All claims are hypotheses until a timestamped run passes in a production-like environment.

| Source | Reference value | Test interpretation |
|---|---:|---|
| ASM-001 | 5,000 students, 100 staff, 200 concurrent active users | identity/data cardinality and peak concurrency |
| ASM-002 | 10,000 chat requests/day, 1,000 ticket actions/day | soak volume plus documented peak multiplier |
| ASM-003 | 150–300 documents; up to 100,000 parsed pages/chunks | ingestion and retrieval stress profile |
| ASM-006 | 99.9% monthly AI/read availability | SLO report; not inferred from one load test |
| REQ-NF-REL-002 | RPO ≤15 min | timed restore point evidence |
| REQ-NF-REL-003 | RTO ≤60 min | timed recovery of P0 read/safe paths |

## 2. Performance gates

| Test ID | Scenario | Load/sample | Pass oracle | Trace |
|---|---|---|---|---|
| TEST-PERF-FAQ-001 | grounded FAQ completed response | ≥1,000 representative requests at declared reference mix | p95 ≤6s; p50/p95/p99/error reported; unsupported/failed responses not removed | REQ-NF-PERF-001; KPI-018 |
| TEST-PERF-READ-001 | schedule and ticket read | actor-scoped representative mix under reference load | p95 ≤4s including dependency latency; stale cache outside policy cannot pass | REQ-NF-PERF-002 |
| TEST-PERF-WRITE-001 | confirmed ticket/document/booking processing | valid confirmed writes; confirmation think time excluded | server p95 ≤10s; zero duplicate/false success; unknown timeout reconciles | REQ-NF-PERF-003; KPI-008 |
| TEST-PERF-HITL-001 | decision to queue acceptance | ≥500 synthetic handovers | p95 ≤5s; failures explicit and alerted | REQ-NF-PERF-004; KPI-011 |
| TEST-PERF-CAP-001 | mixed journey peak | ramp to 200 concurrent active users | all P0 latency/error SLOs hold; no hidden unbounded queue/saturation | REQ-NF-SCALE-001; ASM-001 |
| TEST-PERF-SOAK-001 | daily volume model | 10,000 chat + 1,000 ticket actions over compressed/realistic declared window | no data loss/duplicate, bounded backlog, stable resource trend | REQ-NF-SCALE-002; ASM-002 |
| TEST-PERF-RAG-001 | ingest/retrieve corpus | 150, 300 docs and stress up to 100,000 chunks | counts/checksums complete; no silent partial index; retrieval gates pass | REQ-NF-SCALE-003; REQ-NF-DATA-004 |
| TEST-PERF-BURST-001 | burst at declared multiplier | multiplier must be recorded, not hard-coded as product promise | bounded reject/backpressure, no integrity loss, recovery measured | ARCH-007 |
| TEST-PERF-COST-001 | model/embedding/rerank usage | same workload mix as AI run | usage/cost events complete; caps/alerts behave as configured | REQ-NF-COST-001..003 |

The load model MUST publish route percentages, payload sizes, cache state, corpus version, provider/fake mode, think time, concurrency pattern and arrival model. A run with a materially different mix cannot prove these gates.

## 3. Measurement rules

- Clock boundary is server receipt to terminal response/queue acceptance as defined per scenario; user think time is separate.
- Report successful and failed requests; do not drop timeouts, retries or warm path misses.
- Warm-up duration, test duration and cool-down are explicit run parameters. Results during warm-up are reported separately, not silently discarded.
- At least p50/p95/p99, max, throughput, outcome class, retry count, queue age, resource saturation and DB pool usage are recorded.
- Client and server clocks use a verified monotonic source for duration; timestamps retain timezone.
- One approved release tuple per comparison; changes between runs invalidate direct regression claim.
- No real DeepSeek call is required for infrastructure load; use latency/error-distribution fake. Separate approved live-provider tests measure provider-specific latency/cost without real data.

## 4. Resilience and degradation suites

| Test ID | Injected condition | Expected behavior | Forbidden behavior | Trace |
|---|---|---|---|---|
| TEST-RES-API-001 | API task termination during read/write | ECS replaces task; idempotent client retry only | duplicate write; success without receipt | ARCH-007; REQ-NF-REL-004 |
| TEST-RES-DB-001 | PostgreSQL unavailable/connection reset/failover | readiness false or bounded reconnect; authoritative operations stop; alert | Redis as database; infinite retry | ARCH-007; REQ-NF-REL-004 |
| TEST-RES-REDIS-001 | Redis unavailable | safe cache bypass; risk-sensitive rate/auth control follows deny-safe policy | allow-by-default security bypass | ADR-011; SEC-CTRL-006 |
| TEST-RES-SQS-001 | publish outage, duplicate/out-of-order, poison message | committed outbox retained; idempotent worker; DLQ/quarantine/alert | mark published before ACK; silent drop | ADR-008; REQ-NF-DATA-004 |
| TEST-RES-S3-001 | object storage unavailable | upload/ingest remains pending/failed and retries bounded | durable data on container disk; partial publish | ARCH-007 |
| TEST-RES-LLM-001 | DeepSeek timeout/error/circuit open | `DEGRADED_NO_LLM`; deterministic approved fallback | ungrounded generated answer; unapproved provider switch | DEC-008; ARCH-007 |
| TEST-RES-LLM-002 | malformed provider output | strict reject; at most permitted repair within budget | tool execution from malformed args | EVAL-RED-033; EVAL-METRIC-015 |
| TEST-RES-WRITE-001 | timeout after external dispatch | `unknown/reconciling`, lookup by provider/idempotency key | blind retry or false success | ADR-016; REQ-NF-REL-004 |
| TEST-RES-CORPUS-001 | bad knowledge release | switch active pointer to previous verified corpus; preserve evidence | delete prior corpus/history | ARCH-007; REQ-F-KNOW-009 |
| TEST-RES-AUDIT-001 | audit store failure | high-impact write fails closed | side effect then best-effort audit | REQ-NF-SEC-005 |
| TEST-RES-BACKLOG-001 | queue backlog/oldest-age pressure | bulk ingest throttles before critical handover; alerts and recovery | critical starvation; unbounded accept | ARCH-007 |
| TEST-RES-CACHE-001 | stale/mis-keyed cache attempts | auth/content dimensions isolate users/roles/corpus versions | cross-user/policy stale response | ADR-011; SEC-AUTHZ-* |

Fault injection is authorized only in disposable/local or approved staging scope. Production chaos requires a separate explicit change approval.

## 5. Recovery tests

### TEST-RES-RPO-001 — Restore point objective

Given synthetic writes with known timestamps and a selected encrypted backup/PITR point, when restore runs in an isolated environment, then newest durably restored business event is no older than 15 minutes relative to failure point. Evidence includes backup IDs, checksums, selected point, latest restored event and calculated loss window. `>15m`, unknown timestamps or unverified checksum fails.

### TEST-RES-RTO-001 — Recovery time objective

Given a declared disaster start and approved runbook, when recovery begins, then P0 readiness, identity, grounded read/search and safe handover/fallback smoke tests pass within 60 minutes. Timer ends only after functional probes pass, not when infrastructure creation completes.

### TEST-RES-BACKUP-001 — Release backup restore

Each production release candidate requires one restore test. “Backup enabled” is not evidence. Restore must verify relational constraints, source/chunk provenance, audit/event continuity and absence of secret/PII in exported report.

## 6. Cache and connection safety

Run cross-user/role/corpus tests at cold/warm cache; verify private/no-store on authenticated responses, authorization on hits, version/freshness metadata and invalidation on source/config change. Load test must show database pool formula plus reserve and that autoscaling cannot exceed tested DB/provider/budget limits.

## 7. Acceptance and evidence

`GATE-REL-007` requires all applicable performance thresholds; `GATE-REL-008` requires declared failure modes, RPO/RTO, restore and rollback drills. Evidence includes scripts hash, environment topology/config, image/dataset/provider-mode hashes, raw result location/hash, summary statistics, failed sample IDs, dashboards/traces, start/end times and owner approval.

If capacity or degradation cannot be proved, capability remains disabled or status `unverified`; documentation numbers are never increased to make a run pass.
