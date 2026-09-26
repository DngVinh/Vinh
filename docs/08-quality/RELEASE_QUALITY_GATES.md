---
document_id: "DOC-QUAL-010"
version: "1.0.0"
status: "reviewed"
owner: "Release Quality Lead"
approvers: ["Product Owner", "Release Owner", "Security Lead", "AI Quality Lead", "SRE Lead"]
last_updated: "2026-09-22"
---

# Release quality gates

## 1. Decision model

Gate states: `passed`, `failed`, `blocked`, `not_verified`. Mandatory gate must be `passed`; every other state blocks promotion. A release decision is valid only for one immutable candidate tuple and one target phase/environment.

No agent may mark a gate passed from prose, historical evidence, a different revision/config, skipped tests or a rerun that hides the original failure.

## 2. Gate catalog

| Gate ID | Gate | Pass criteria | Owner |
|---|---|---|---|
| GATE-REL-001 | Scope, governance and traceability | approved/reviewed inputs appropriate to phase; no unknown/duplicate/orphan IDs; change impact bounded; no out-of-scope changes | Product + Quality Governance |
| GATE-REL-002 | Build and deterministic verification | reproducible install/build; format/lint/type/unit/property/architecture fitness pass; zero required-test collection anomaly | Engineering Lead |
| GATE-REL-003 | Contract and migration | schemas/refs/fixtures/provider-consumer tests pass; no unapproved breaking change; migration compatibility/rollback evidence | Architecture Lead |
| GATE-REL-004 | Security and privacy | applicable `SEC-SDLC-*`; zero non-waivable/unknown Critical/High; synthetic-only/egress/authz/audit/supply-chain/IaC tests pass | Security/Privacy Lead |
| GATE-REL-005 | AI/RAG/tool safety and quality | all hard-zero/critical must-pass and `EVAL-METRIC-*` thresholds/regression rules pass on versioned dataset | AI Quality Lead |
| GATE-REL-006 | Functional, UX and accessibility | all applicable P0/P1 acceptance scenarios pass; WCAG P0 audit has 0 Critical/Serious open issue; no false-success state | QE + Product Owner |
| GATE-REL-007 | Performance and capacity | all applicable p95 thresholds and 200-user/reference-volume/corpus tests pass with raw evidence | Performance QE/SRE |
| GATE-REL-008 | Resilience, recovery and data integrity | declared dependency failures degrade safely; no loss/duplicate; RPO ≤15m, RTO ≤60m, backup restore and rollback drills pass | SRE Lead |
| GATE-REL-009 | Observability and operations | correlation, redaction, KPI events, alerts, dashboards, owners/runbooks and safe-mode operation verified | Operations Lead |
| GATE-REL-010 | Test data and reproducibility | generator/seed/manifest/checksum reproducible; provenance/split/isolation/synthetic-only scans pass | Test Data + Privacy Leads |
| GATE-REL-011 | Release artifact and rollback readiness | signed/content-addressed image/config/contract/evidence inventory; deployment/rollback plan rehearsed; previous artifact available | Release Owner |
| GATE-REL-012 | Production launch authorization | OQ-001..008 and security/privacy/vendor/identity/contact/retention/budget blockers closed; independent reviews and explicit go/no-go recorded | Product Owner + mandatory domain approvers |

## 3. Phase applicability

| Gate | Foundation | MVP | Pilot readiness | Production |
|---|---|---|---|---|
| GATE-REL-001 | mandatory | mandatory | mandatory | mandatory |
| GATE-REL-002 | mandatory | mandatory | mandatory | mandatory |
| GATE-REL-003 | mandatory for existing contracts | mandatory | mandatory | mandatory |
| GATE-REL-004 | design/static baseline | mandatory affected scope | full staging | full + independent review |
| GATE-REL-005 | framework/sample fake | full fake affected scope | full sealed + live candidate | full approved candidate |
| GATE-REL-006 | component smoke | all P0 MVP | all P0/P1 pilot + manual a11y | all launch scope |
| GATE-REL-007 | benchmark harness | affected smoke | full reference workload | full + baseline comparison |
| GATE-REL-008 | failure-unit subset | integration failures | restore/rollback/incident drills | full current candidate |
| GATE-REL-009 | schema/telemetry baseline | correlation/audit | alerts/runbooks/on-call rehearsal | full owners/SLO operation |
| GATE-REL-010 | mandatory | mandatory | mandatory | mandatory |
| GATE-REL-011 | artifact manifest | deployable demo artifact | pilot deployment rehearsal | production artifact approval |
| GATE-REL-012 | not applicable; remain blocked | not applicable; remain blocked | gap-closure review | mandatory |

“Not applicable” is not `passed`; record rationale and target phase. Production always requires all 12 gates.

## 4. Hard-stop conditions

Promotion stops immediately on:

- unauthorized/unconfirmed/duplicate side effect;
- cross-user/role disclosure, auth bypass, secret/PII egress;
- missed critical safety case, invented contact/intervention, critical injection bypass;
- unsupported material policy claim/citation corruption above gate policy;
- real or unproven personal data in any lower environment/evidence;
- missing audit for high-impact write or false success on dependency failure;
- destructive/unrecoverable migration without explicit human authorization;
- missing/invalid rollback or restore proof;
- evidence mismatch, tampering, unknown test scope or required suite unavailable;
- production launch while any `OQ-001`–`OQ-008` remains open.

## 5. Waiver policy

A waiver is never implicit. It must state `WVR-*`, affected candidate/gate/test/route, severity, rationale, compensating control, owner, start/expiry, verification plan and approvals. Expired waiver automatically fails gate. Waiver cannot authorize production for R0/S1/hard-zero, real-data, auth bypass, cross-user leak, secret/PII egress, unconfirmed/duplicate write, critical safety miss or destructive migration.

Preferred response is disable the affected capability and rerun all impacted gates. A disabled route must be verified inaccessible and have truthful fallback/operations alert.

## 6. Gate execution algorithm

1. Freeze candidate tuple and target phase.
2. Compute changed scope and applicable test/gate IDs.
3. Validate evidence schema, hashes, freshness and trace graph.
4. Evaluate hard-stop conditions first.
5. Aggregate deterministic suites, then AI/security/performance/manual approvals.
6. Validate waivers and capability-disable evidence.
7. Produce one gate result per ID with reasons and evidence refs.
8. Release Owner records `GO`, `NO_GO` or `CONDITIONAL_NON_PRODUCTION` only. Production cannot be conditional on a failed mandatory gate.
9. Any candidate/config change invalidates affected results and returns decision to `NO_GO/not_verified` until rerun.

## 7. Gate result schema

```yaml
gate_result:
  gate_id: GATE-REL-001
  candidate_id: RC-...
  target_phase: foundation|mvp|pilot|production
  status: passed|failed|blocked|not_verified
  evaluated_at: <RFC3339>
  required_test_ids: []
  evidence_ids: []
  failed_test_ids: []
  blocker_ids: []
  waiver_ids: []
  owner_role: <role>
  reviewer_role: <role>
  reason: <sanitized-text>
```

## 8. Current status

All gates are `not_verified` because no implementation release candidate or evidence bundle is asserted by this documentation. `GATE-REL-012` is additionally `blocked` for production by the recorded open questions. This statement is intentional and must not be changed by a coding task.
