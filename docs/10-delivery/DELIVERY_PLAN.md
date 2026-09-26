---
document_id: "DOC-DEL-001"
version: "1.0.0"
status: "reviewed"
owner: "Delivery Lead"
approvers: ["Product Owner", "Engineering Lead", "Quality Lead", "Security Lead", "Operations Lead"]
last_updated: "2026-09-22"
---

# Delivery plan

## 1. Delivery model

Delivery is incremental, contract-first and gate-driven. “Done” means verified behavior/evidence, not generated code volume. There is no calendar commitment; each wave starts only after dependencies and previous exit criteria pass.

Product roadmap alignment:

- Foundation = Roadmap Phase 0–1;
- MVP increments = Roadmap Phase 2–4;
- Pilot readiness = Roadmap Phase 5 in production-like synthetic AWS staging;
- Production/controlled real-integration pilot = Roadmap Phase 6, future and blocked;
- Phases 7–8 are excluded from this delivery plan.

## 2. Workstreams

| Workstream | Scope | Hard dependencies | Primary outputs |
|---|---|---|---|
| WS-01 Governance/product | decisions, requirements, KPI, scope, trace graph | stakeholder assumptions | approved executable specification |
| WS-02 Contracts/data | OpenAPI, JSON/tool/event schemas, model/migrations, synthetic generator | WS-01, ADRs | validated contracts/fixtures |
| WS-03 Platform/CI | monorepo/build, test runners, containers, local dependencies, AWS CDK/ECS pipeline | WS-02 security baseline | reproducible environments/artifacts |
| WS-04 Identity/security/privacy | mock adapter, actor context, authz, audit, secret/egress/retention controls | WS-02, security docs | deny-safe boundary and evidence |
| WS-05 Knowledge/RAG/AI | ingestion, hybrid retrieval, rerank, evidence gate, gateway, graph, eval | WS-02–04 | grounded assistant candidate |
| WS-06 Student services | schedule, tickets, document requests, room booking, preview/confirm/idempotency | WS-02–05 | typed read/write journeys |
| WS-07 HITL/staff/ops | safety route, handover, queues, staff workspace, dashboards/safe mode | WS-04–06 | operable simulated service |
| WS-08 Quality/release | tests, evals, security/load/recovery, evidence, promotion/rollback | all affected streams | gate decisions/release bundle |

## 3. Dependency spine

```text
requirements/ADRs
 -> API/data/tool/event contracts
 -> synthetic fixtures + test/eval oracles
 -> build/CI/runtime skeleton
 -> identity/authz/audit/observability
 -> knowledge + AI read path
 -> controlled write primitives
 -> service workflows + HITL/staff
 -> AWS production-like deployment
 -> full quality/security/recovery gates
 -> authorized promotion
```

A downstream task cannot compensate for an unapproved upstream contract by inventing behavior.

## 4. Execution waves

### Wave F0 — Specification closure

Deliver governance/product/service/UX/architecture/AI/security/platform/quality/delivery docs; machine-readable requirements/contracts/task schemas; resolve normative conflicts. Exit: `MS-FOUND-001`.

### Wave F1 — Reproducible engineering foundation

Deliver pinned toolchains, Next.js/FastAPI/worker skeletons, local container dependencies, CI lanes, synthetic generator, fake providers/adapters, health/readiness, correlation/audit skeleton. Exit: `MS-FOUND-002`.

### Wave F2 — Trust boundary

Deliver mock identity through internal claims contract, role/resource/action authz, session/logout, environment separation, secret injection, audit failure-close, simulation disclaimer. Exit: `MS-FOUND-003`.

### Wave M1 — Grounded assistance

Deliver source lifecycle, scanning/quarantine, parse/chunk/provenance, PostgreSQL FTS + pgvector, reranking, citation detail, abstention/clarification, DeepSeek gateway behind fake/live modes, evaluation harness. Exit: `MS-MVP-001`.

### Wave M2 — Student read/write workflows

Deliver schedule read and generic action preview/confirmation/idempotency/execution/reconciliation, then ticket, document request, room search/book/cancel. Exit: `MS-MVP-002`.

### Wave M3 — Human and operations workflow

Deliver deterministic safety rules/classifier boundary, handover preview/queue, staff queue/claim/transfer/respond/state machine, knowledge admin and operations dashboard/safe modes. Exit: `MS-MVP-003`.

### Wave P1 — Production-like synthetic pilot readiness

Deliver AWS CDK reference deployment to approved non-production account, immutable ECS images, RDS/pgvector, ElastiCache, SQS/outbox, S3, network/secrets/observability/cost controls, backup/restore/rollback and full gate execution. Exit: `MS-PILOT-001`.

### Wave P2 — Synthetic pilot rehearsal

Run operational training/tabletops, queue/business-calendar/contact placeholder truthfulness, load/AI/security/accessibility tests, release and rollback rehearsals. No real users/data. Exit: `MS-PILOT-002`.

### Wave R1 — Production authorization and real integrations (future)

Close `OQ-001`–`OQ-008`; obtain HUCE sponsor/data/legal/vendor/identity/operations approvals; contract Entra/SIS/LMS/service adapters; create separate real-data test plan and change set. Exit: `MS-PROD-001`; no coding agent can self-start this wave.

### Wave R2 — Controlled production launch (future)

Execute approved migration/integration validation, full production candidate gates, go/no-go, staged deployment, post-launch verification and monitored rollback window. Exit: `MS-PROD-002`.

## 5. Micro-task design

Default task: one testable behavior, one layer, 1–3 product files, approximately 150 added lines, one explicit write scope, 15–45 minute agent unit. Split database, backend, frontend, infrastructure, fixtures and tests unless a tiny atomic change requires co-location. Up to four tasks may run concurrently only with disjoint write paths and accepted shared dependencies.

Task sequence for one capability:

1. contract/schema fixture;
2. domain state/value rule;
3. repository/adapter fake;
4. application use case;
5. API handler/serialization;
6. frontend state/view;
7. audit/telemetry;
8. positive test;
9. auth/validation negative test;
10. dependency/failure test;
11. acceptance/evidence wiring.

## 6. Integration cadence

Trunk remains releasable. Integrate small tasks after `GATE-REL-001..003` task-applicable checks; use short-lived branches/worktrees as orchestrated. Merge is not release. Nightly assembles cross-stream evidence; only a frozen candidate triggers full gates. Agent must preserve unrelated dirty work and never force-clean/reset to integrate.

## 7. Deliverable control

Every wave has a manifest listing requirement/task IDs, files/artifacts, contract/config/data versions, test/evidence IDs, open risks and rollback target. Missing artifact or owner makes the wave `not_verified`. Handover between workstreams includes interface version and acceptance evidence; verbal agreement is insufficient.

## 8. Progress reporting

Report counts by state (`planned`, `ready`, `in_progress`, `blocked`, `verified`, `accepted`) and by requirement/gate coverage. Code lines, token usage or task count are not progress outcomes. Dashboard must distinguish zero from unknown and synthetic from pilot/production.

## 9. Stop conditions

Stop a wave when dependency is not accepted, contract conflicts, data/secret provenance is unknown, required reviewer/owner is missing, Critical/High/S1 issue is open, evidence is invalid, cost approval is absent, or task requires production/destructive authority. Record blocker and safe next action; never expand scope into future/SaaS capability.
