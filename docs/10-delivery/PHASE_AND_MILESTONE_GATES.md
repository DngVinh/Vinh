---
document_id: "DOC-DEL-002"
version: "1.0.0"
status: "reviewed"
owner: "Program Delivery Lead"
approvers: ["Product Owner", "Release Owner", "Quality Lead", "Security Lead", "Operations Lead"]
last_updated: "2026-09-22"
---

# Phase and milestone gates

## 1. Promotion rule

Milestones are evidence states, not dates. Entry needs every listed dependency `accepted`; exit needs every mandatory quality gate `passed` for the same artifact tuple plus signed promotion record. A later phase cannot begin merely because implementation appears complete.

## 2. Foundation

### MS-FOUND-001 — Executable specification

Entry: user scope decisions recorded; source register available.

Exit:

- docs 00–10 and machine-readable requirement/contract/task artifacts exist and have no unresolved normative conflict;
- P0/P1 requirements map to owner, design/contract and planned test/gate;
- V1 single-institution/synthetic-only/non-goal boundaries are explicit;
- `GATE-REL-001`, documentation portion of `GATE-REL-003`, and trace checks pass;
- open questions remain explicit blockers, not fabricated values.

### MS-FOUND-002 — Reproducible build and test foundation

Dependencies: `MS-FOUND-001`.

Exit:

- pinned runtime/dependencies and reproducible install/build for Next.js, FastAPI and worker;
- deterministic fake LLM/integration ports and synthetic profiles;
- local/CI health, schema, unit, integration and evidence reporters operational;
- immutable container artifacts and SBOM created without secret;
- `GATE-REL-002`, `GATE-REL-003`, `GATE-REL-010` pass for foundation scope.

### MS-FOUND-003 — Trust and observability foundation

Dependencies: `MS-FOUND-002`.

Exit:

- simulation disclosure and synthetic marker enforced;
- identity adapter/actor context, default-deny role/resource/action authz and logout pass;
- correlation, append-only audit, structured redacted logs and capability-state endpoint pass;
- high-impact mutation fails closed when auth/audit unavailable;
- relevant `GATE-REL-004`, `006`, `009` pass.

## 3. MVP

### MS-MVP-001 — Grounded assistance increment

Dependencies: all Foundation milestones.

Exit:

- knowledge ingest/review/publish/version/retire and provenance are functional;
- hybrid lexical/vector retrieval, rerank, evidence gate, citations, abstention/clarification and feedback pass;
- provider-neutral gateway uses fake by default and approved DeepSeek candidate mode only in isolated staging;
- `EVAL-METRIC-001..007`, `013..015` and affected EVAL-RED cases meet `GATE-REL-005`;
- performance/citation/security acceptance applicable to read path pass.

### MS-MVP-002 — Student service workflow increment

Dependencies: `MS-MVP-001`, generic action contracts.

Exit:

- schedule read, ticket/document request and room workflows cover success/empty/deny/conflict/failure;
- every write uses authorize → preview → explicit confirm → idempotent execute → receipt/reconcile → audit;
- `EVAL-METRIC-010..012` are zero; cross-user and replay/concurrency tests pass;
- REQ-NF p95/load thresholds for implemented routes pass;
- relevant `GATE-REL-003..008` pass.

### MS-MVP-003 — HITL, staff and operations increment

Dependencies: `MS-MVP-002`, queue/state/event contracts.

Exit:

- explicit/insufficient-evidence/rights-impact/tool-uncertainty/safety handover routes pass;
- staff scope, claim, reply, transition, transfer, history and audit pass;
- knowledge and operations administration, metric metadata, alerts and safe modes pass;
- critical safety must-pass is 100%, critical recall ≥0.98 and no invented contact/intervention;
- missing official contact/calendar/owner remains truthful `launch_blocked` rather than hidden;
- all `GATE-REL-001..010` applicable to MVP pass.

MVP acceptance does not authorize public HUCE production; it is a commercial-grade simulated product increment.

## 4. Pilot readiness

### MS-PILOT-001 — Production-like synthetic AWS readiness

Dependencies: all MVP milestones; approved non-production AWS account/budget.

Exit:

- CDK-provisioned ECS/Fargate, RDS PostgreSQL/pgvector, Redis, SQS/outbox, S3, secrets, network and observability match approved architecture;
- immutable images/configs deploy with no real data and no public DB/cache/task exposure;
- 200 concurrent/reference-volume/corpus tests meet thresholds;
- dependency failure/degraded states, backup restore, RPO ≤15m, RTO ≤60m and rollback drills pass;
- full synthetic `GATE-REL-001..011` pass.

### MS-PILOT-002 — Operational rehearsal

Dependencies: `MS-PILOT-001`.

Exit:

- assigned rehearsal owners use role labels; runbooks/tabletops for SEV0/SEV1, `search_ticket_only`, `suspended` and rollback pass;
- support/knowledge/operations training and shift-handover exercises complete on synthetic cases;
- accessibility manual audit and live-provider isolated eval/red-team pass;
- gate evidence bundle and go/no-go process are rehearsed;
- limitations/disclaimer remain visible; no real users/data or official SLA claim.

## 5. Production and controlled real-integration pilot

### MS-PROD-001 — Authorization to prepare real integration

Entry/exit are blocked until all are evidenced:

- `OQ-001`–`OQ-008` closed by named authorized owners;
- university sponsor/data-owner approval; privacy/legal/DPIA/vendor/cross-border/retention/budget approvals;
- official contacts, support hours, business calendar, queue owners/on-call/runbooks;
- Entra tenant/claim/group contract and real integration sandbox contracts;
- production data classification/minimization/real-data test/migration plans;
- independent security/penetration review scope approved.

No synthetic implementation evidence may be used to claim this milestone passed.

### MS-PROD-002 — Controlled launch

Dependencies: `MS-PROD-001`; explicit production change approval.

Exit:

- all `GATE-REL-001..012` pass on exact production candidate;
- launch, rollback, incident, communication and data-recovery owners acknowledge;
- production deploy and post-deploy verification complete inside approved window;
- required observation window closes with no unresolved hard-stop issue;
- sponsor records final release acceptance.

## 6. Promotion record

```yaml
milestone_decision:
  milestone_id: MS-...
  candidate_id: RC-...
  decision: promote|reject|blocked
  gate_results: []
  evidence_bundle_hash: sha256:<64-hex>
  open_risks: []
  waivers: []
  approvals: []
  decided_at: <RFC3339>
  next_allowed_milestone: <id-or-null>
```

Missing approval, hash or mandatory gate sets decision `blocked`; an agent cannot infer approval from silence.
