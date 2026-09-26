---
document_id: "DOC-DEL-005"
version: "1.0.0"
status: "reviewed"
owner: "Program Risk Lead"
approvers: ["Product Owner", "Security Lead", "AI Quality Lead", "SRE Lead", "Release Owner"]
last_updated: "2026-09-22"
---

# Risk register

## 1. Scoring and use

Likelihood (`L`) and impact (`I`) are `Low/Medium/High/Critical`; these are planning assessments, not observed incidents. Owner reviews trigger and residual risk at each milestone. A risk without owner/response blocks the affected gate. Risk acceptance never overrides a non-waivable quality/security gate.

## 2. Active planning risks

| ID | Risk event | L / I | Trigger / early signal | Preventive mitigation | Contingency | Owner | Gate |
|---|---|---|---|---|---|---|---|
| RSK-001 | Synthetic corpus does not represent real HUCE queries | H / H | low coverage, subgroup misses, many abstentions | taxonomy from approved public sources; balanced/natural datasets; human review | keep simulation claim; expand reviewed synthetic cases before pilot | Product + AI Quality | GATE-REL-005,010 |
| RSK-002 | Public content provenance/licensing unclear | M / H | source owner/license missing | source register, minimal derived metadata, approval/quarantine | exclude source; use synthetic equivalent | Knowledge + Legal | GATE-REL-004,010 |
| RSK-003 | Hallucinated or weakly cited policy answer | M / C | citation precision/recall/correctness regression | hybrid retrieval, evidence gate, claim-level citation, abstain | `SEARCH_ONLY`, rollback AI/corpus bundle | AI Quality | GATE-REL-005 |
| RSK-004 | Prompt injection/source poisoning controls graph/tool | M / C | red-team bypass or unreviewed source publish | quarantine/approval, data-as-untrusted, strict tools, egress limits | disable generative/tool route; incident review | Security + AI | GATE-REL-004,005 |
| RSK-005 | Unauthorized/cross-user access | M / C | IDOR/authz negative failure or anomalous access | server actor context, default deny, scoped cache/cursor | suspend route, contain, security incident | Security | GATE-REL-004 |
| RSK-006 | Duplicate/unconfirmed side effect | M / C | replay/concurrency/confirmation hard-zero >0 | bound preview token, explicit control, idempotency, audit | `READ_ONLY`, reconcile, notify per approved plan | Architecture + Service owner | GATE-REL-003..006 |
| RSK-007 | Unknown write result creates false receipt | M / C | timeout after dispatch, status mismatch | provider key/status reconciliation and truthful state | stop affected writes; manual synthetic reconciliation | Service owner + Ops | GATE-REL-006,008 |
| RSK-008 | Sensitive case missed or unsafe contact invented | M / C | critical case fail/unconfigured contact | deterministic rules + classifier; sealed must-pass; config-only contacts | disable generative flow, approved fallback, SEV1 | Safety + Security | GATE-REL-005,009,012 |
| RSK-009 | External LLM receives prohibited data | M / C | egress canary/redaction test fail | minimization/de-identification, deny on policy outage, allowlisted egress | stop provider calls; rotate/investigate | Privacy + Security | GATE-REL-004,005 |
| RSK-010 | DeepSeek availability/quality/API drift | H / H | timeout, malformed output, model/version change | provider-neutral gateway, pinned allowlist, fake contract, circuit breaker | `DEGRADED_NO_LLM`, rollback provider bundle | AI Platform + Ops | GATE-REL-003,005,008 |
| RSK-011 | Cost exceeds unapproved budget | M / H | 50/75/90% alerts, unknown price/usage | hard caps, usage ledger, routing/caching policy, finance approval | block paid calls; deterministic fallback | Product/Finance + Ops | GATE-REL-009,012 |
| RSK-012 | Load exceeds 200-user/reference model | M / H | p95/saturation/backlog breach | load/soak, bounded autoscale/backpressure, capacity caps | degrade/queue/disable noncritical ingestion | SRE | GATE-REL-007 |
| RSK-013 | RDS/queue/cache/provider failure causes data loss | M / C | recovery/fault tests fail, backlog age | PostgreSQL truth, outbox/idempotency, backup/PITR, bounded retries | degraded/read-only, restore/reconcile | SRE + Data owner | GATE-REL-008 |
| RSK-014 | Backup exists but restore/RPO/RTO fails | M / C | drill >15m RPO or >60m RTO | release-candidate restore drill and runbook | no production promotion; remediate capacity/process | SRE | GATE-REL-008,011 |
| RSK-015 | Schema migration breaks rolling old/new tasks | M / C | compatibility test/dry-run failure | expand-contract, separate destructive step, rollback target | abort deployment; restore/forward fix under approval | Data + Release | GATE-REL-003,011 |
| RSK-016 | AWS IAM/network/config exposes service/data | M / C | IaC/runtime scan finds public/wildcard/drift | private networking, scoped IAM, encryption, policy as code | block/rollback; rotate secret if exposure suspected | Cloud Security | GATE-REL-004 |
| RSK-017 | Observability leaks PII/secrets or misses critical signal | M / C | canary leak, broken correlation/alert | structured allowlist, redaction, independent alert path | quarantine sink, incident, affected write fail-close | SRE + Security | GATE-REL-004,009 |
| RSK-018 | Accessibility blocks P0 journey | M / H | keyboard/screen-reader/zoom Critical/Serious | semantic components, early automated/manual tests | block route/release until fixed | UX + Product | GATE-REL-006 |
| RSK-019 | Gemini agent changes scope/contract or weakens test | H / H | out-of-scope diff, changed oracle/threshold | atomic tasks, allowed paths, upstream IDs, review/evidence | reject task, restore via patch preserving user work, refine task | Engineering + QE | GATE-REL-001,002 |
| RSK-020 | Parallel agents collide or overwrite user work | M / H | overlapping paths/dirty status changes | max four disjoint tasks, pre/post status/diff, no destructive Git | stop affected agents; manual merge/review | Orchestrator/Release | GATE-REL-001 |
| RSK-021 | Contract/document inconsistency leads wrong implementation | H / H | duplicate/unknown ID or contradictory MUST | canonical manifest, trace/orphan checks, change control | block downstream tasks; governance resolution | Architecture Governance | GATE-REL-001,003 |
| RSK-022 | Missing university owner/contact/calendar creates false promise | H / C | `UNASSIGNED`/`UNCONFIGURED`, OQ open | launch blockers, truthful UI, no official SLA/contact | simulation-only; disable affected feature | Product + Support | GATE-REL-009,012 |
| RSK-023 | Mock auth leaks into production profile | M / C | switch-user/demo endpoint in prod config | adapter boundary and startup assertion | abort/rollback, security incident assessment | Identity + Security | GATE-REL-004,012 |
| RSK-024 | Real data accidentally enters lower environment | M / C | provenance/PII scan or unapproved import | synthetic-only guard, isolated stores/credentials, import deny | quarantine/contain, privacy incident; do not copy further | Privacy + Security | GATE-REL-004,010 |
| RSK-025 | Single maintainer bottleneck/key-person loss | H / H | undocumented task, manual unreproducible step | executable docs, IaC, scripts, evidence, decision log | pause promotion; reconstruct from immutable artifacts | Product + Engineering | GATE-REL-001,011 |
| RSK-026 | Test flakiness/nondeterminism hides regression | M / H | rerun-only green, variance, time/order failure | fake provider, injected time/randomness, quarantine rules, 3 repeats | mark `not_verified`; block required gate | QE + AI Quality | all quality gates |
| RSK-027 | Supply-chain compromise/vulnerable dependency | M / C | scan/signature/SBOM drift or unreviewed package | pins, provenance, review, SCA/SAST/image scan | block artifact, patch/rebuild, rotate as needed | Security + Release | GATE-REL-002,004,011 |
| RSK-028 | Production approval inferred from demo success | M / C | request to remove disclaimer/go live with OQ open | separate `MS-PROD-*`, explicit RACI and gate 12 | reject launch; remain synthetic | Product Owner | GATE-REL-012 |

## 3. Risk review cadence

Review at task planning for linked risks, each milestone, every release candidate, after failed gate/incident and before/after launch. Change in likelihood/impact/owner/response creates a new risk-register revision and links evidence; do not delete closed risks—set status `closed`, reason and date in the operational register.

## 4. Escalation

Critical impact or trigger observed becomes defect/incident, not merely an accepted risk. Security/Privacy, AI Safety, data integrity and destructive-action risks require respective owner approval and cannot be accepted by Product alone.
