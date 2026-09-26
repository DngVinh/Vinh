---
document_id: "DOC-PROD-010"
version: "1.0.0"
status: "reviewed"
owner: "Product Lead"
approvers: ["Product Owner", "Architecture Lead", "Finance Owner"]
last_updated: "2026-09-21"
---

# Capability roadmap

## 1. Nguyên tắc

Roadmap là capability-gated, không phải date promise. Một phase chỉ bắt đầu khi exit gate phase trước đạt. Agent MUST NOT triển khai phase sau vì “còn thời gian” hoặc “dễ làm”.

## 2. Phases

### Phase 0 — Governance and executable specification

**Deliverables:** docs 00–10, source register, requirements YAML, contracts, eval datasets, task schema/DAG.

**Exit:** product package approved; không có normative conflict; P0 requirements có downstream design/test owners.

### Phase 1 — Simulated vertical foundations

**Capabilities:** disclaimer, demo identity, synthetic data generator, audit/telemetry skeleton, deterministic fake LLM/integrations.

**Exit:** role isolation pass; no real data; repeatable environment; observability evidence.

### Phase 2 — Grounded assistance

**Capabilities:** knowledge lifecycle, hybrid retrieval/rerank, grounded chat, citation viewer, abstention, feedback, baseline eval.

**Exit:** KPI-001..004 và KPI-012 đạt; prompt-injection/evidence failure paths pass.

### Phase 3 — Student read and write workflows

**Capabilities:** schedule read, ticket, document request, room search/booking, preview/confirmation/idempotency.

**Exit:** KPI-006..008 bằng 0; UC-SCHEDULE/TICKET/DOC/ROOM acceptance pass; load and retry tests pass.

### Phase 4 — HITL and staff operations

**Capabilities:** safety routing, user-requested handover, staff queue, assignment, transfer, SLA/queue metrics.

**Exit:** KPI-005, KPI-009..011 đạt; missing-contact and after-hours behavior accepted.

### Phase 5 — Production readiness on AWS

**Capabilities:** approved AWS topology/IaC, CI/CD, secret management, backup/restore, DR, SLO, security/privacy review, cost controls.

**Exit:** KPI-017..021 đạt; restore and incident drills pass; no unresolved Critical/High issue.

### Phase 6 — Controlled real-integration pilot (future, blocked)

**Capabilities:** Microsoft Entra, approved source integrations, real support roster, real-data governance.

**Entry blockers:** OQ-001..OQ-008 closed; contracts and legal/privacy approvals; real-data test plan; university authorization to remove/alter demo disclaimer.

**Exit:** live KPI-013..016 đạt tối thiểu bốn tuần; sponsor go/no-go accepted.

### Phase 7 — Same-university expansion (future)

**Candidates:** English, mobile native, proactive notification, more departments, additional workflows.

Mỗi candidate cần discovery và change request; không có quyền kế thừa tự động từ V1.

### Phase 8 — SaaS/multi-tenancy exploration (explicitly not committed)

Chỉ được nghiên cứu sau bằng chứng thương mại của ít nhất một deployment và accepted decision thay thế `DEC-001`. V1 code/task MUST NOT xây tenant billing/onboarding/isolation trước.

## 3. Promotion checklist

Mỗi phase promotion MUST có:

- requirement acceptance evidence;
- KPI report và raw evidence location;
- security/privacy impact review;
- operational owner và rollback/safe-mode path;
- cost delta và budget approval nếu có;
- open risk/waiver với expiry;
- human approval record.

