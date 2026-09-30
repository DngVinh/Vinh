---
document_id: "DOC-DEL-AUDIT-REMEDIATION-001"
version: "0.1.0"
status: "draft"
owner: "Delivery Governance Lead"
approvers: []
last_updated: "2026-09-27"
---

# Campus 24/7 audit remediation status — 2026-09-27

## 1. Purpose and authority

This document preserves the verified static-audit state and the remediation plan created from it. It is a planning and handoff artifact. It does not approve a requirement, architecture, security policy, task, release, provider, data transfer, migration, deployment, or production use.

The source revision inspected was `965702e9db7629174b0a6ccb12414db7372e7c01` on branch `main`. The working tree already contained 60 modified and 139 untracked paths before remediation authoring began. Those paths belong to the user or prior work and MUST be preserved. Every task in this remediation package starts as `draft`; only an authorized orchestrator or human reviewer may move it through `reviewed -> ready` after validating sources, approvals, dependencies, and write leases.

## 2. Executive state

The repository is not evidenced as ready for real users, real institutional data, live paid providers, pilot, or production. Static inspection found reachable or conditionally reachable paths that can mint a synthetic session in an unsafe composition, bypass the write-action protocol, reuse confirmation material, report success without durable effects, skip the real evidence gate, fabricate handover completion, and expose demo data as current operational data. Release and disaster-recovery manifests declare passed outcomes without independent run-scoped evidence.

The remediation package contains **38 draft micro-tasks**. They are registered in a 239-task catalog, but none of the 38 is `ready` or `accepted`. All reuse existing reviewed traceability authorities rather than inventing a new product requirement; 26 retain explicit human-approval gates for authentication, authorization, security-policy, legal/privacy, migration, dependency, infrastructure, or production-promotion impact, while 12 remain ordinary scoped implementation or verification tasks.

No P0 incident was proven because the audit did not access a running deployment, production data, credentials, providers, databases, or cloud resources. Runtime, browser, migration, concurrency, provider, restore, and deployment results remain `not_verified` until an authorized task produces reproducible evidence.

## 3. Non-negotiable remediation invariants

1. A model proposes; deterministic application code parses, validates, authorizes, previews, confirms, executes, reconciles, and audits.
2. User content, retrieved documents, tool output, provider output, and prior messages are untrusted data and cannot alter policy, tool registry, identity, authorization, confirmation, or evidence rules.
3. No write may occur without trusted actor context, normalized immutable payload, authorization, one-time confirmation, idempotency, atomic mutation, and durable audit.
4. A UI or agent may report success only from an authoritative persisted receipt. Timeout after dispatch is `result_unknown`, never success and never an invitation to blind retry.
5. Policy/procedure assertions require claim-level evidence from an authorized, published, effective source version. Missing, stale, revoked, conflicting, or injection-tainted evidence causes abstention or bounded clarification.
6. Sensitive and emergency paths use deterministic rules, minimized payloads, approved wording, and a real queue receipt. Missing contact or queue configuration must be disclosed; placeholders cannot look operational.
7. External model egress is default-deny without destination, data-classification, privacy/legal, budget, and environment authorization. Tests and CI use deterministic fakes and block network.
8. Logs, traces, evidence, and task outputs must not contain secrets, personal data, raw prompts, unrestricted context, provider reasoning, or chain-of-thought.
9. Release evidence is immutable, run-scoped, revision-bound, independently checkable, and fail-closed when missing.
10. No executor changes a higher-authority requirement, contract, security control, threshold, or expected test result to make implementation pass.

## 4. Finding-to-task ledger

| Finding ID | Type | Severity | Description | Primary Task | Supporting Tasks | Wave | Status | Closure Evidence |
|---|---|---|---|---|---|---|---|---|
| FINDING-001 | observed fact | medium | Governance reports and task acceptance do not match current catalog/evidence | `TASK-GOV-AUD-001` | `TASK-GOV-AUD-002` | W0 | open | Current snapshot is reproducible; `accepted` cannot exist without schema-valid evidence and approval chain. |
| FINDING-002 | observed fact | critical | Synthetic auth can remain mounted in an unsafe composition | `TASK-API-AUTHFIX-001` | - | W1 | open | Production matrix proves mock adapter and demo-session route are absent and startup fails closed. |
| FINDING-003 | observed fact | critical | Logout revocation is disconnected from request authentication | `TASK-API-SESSFIX-001` | - | W1 | open | Replaying bearer or cookie after logout returns the same unauthorized response across restart/multi-worker cases. |
| FINDING-004 | observed fact | critical | Direct ticket/room writes bypass approved action contract | `TASK-API-WRITEFIX-001` | - | W1 | open | Uncontracted routes are unavailable; all writes enter the canonical action protocol. |
| FINDING-005 | observed fact | critical | Confirmation token is reusable and confirm accepts replacement payload | `TASK-API-CONFFIX-001` | `TASK-AGENT-CONFIRM-002` | W1 | open | Preview is immutable, consumed once, re-authorized, and replay/concurrency safe. |
| FINDING-006 | observed fact | critical | Core repositories and audit are in-memory, split, or non-atomic | `TASK-DB-REPOFIX-001` | `TASK-DB-AUDITFIX-001` | W1 | open | Read-after-write, restart, multi-worker, rollback, audit immutability, and idempotency evidence pass. |
| FINDING-007 | observed fact | high | Privacy receipt and retention semantics are not durable | `TASK-API-PRIVFIX-001` | `TASK-WORKER-RETENTION-002` | W2 | open | Stable notice identity, idempotent receipts, approved retention config, dry-run and legal-hold paths pass. |
| FINDING-008 | observed fact | high | Database does not enforce no-overlap booking invariant | `TASK-DB-BOOKFIX-001` | - | W2 | open | Concurrent confirmed intervals allow exactly one winner and return stable conflict for the loser. |
| FINDING-009 | observed fact | high | Object existence, abuse limits, and readiness are unsafe or misleading | `TASK-API-CONCEAL-001` | `TASK-API-CONCEAL-002`, `TASK-API-ABUSE-001`, `TASK-API-HEALTHFIX-001` | W2 | open | Central policy and route-inventory rollout conceal unauthorized existence; bounded bodies/rates/budgets and real dependency probes pass negative tests. |
| FINDING-010 | observed fact | high | Agent graph does not pause and execute through authoritative services | `TASK-AGENT-CONFIRM-002` | `TASK-AGENT-EXEC-001` | W1 | open | No decision/no token/expired/cancelled path executes; confirmed execution produces one durable receipt and audit. |
| FINDING-011 | observed fact | high | Emergency path invents contact and handover completion | `TASK-AGENT-HITL-004` | - | W1 | open | User wording reflects actual queue/contact state and no terminal handover without a receipt. |
| FINDING-012 | observed fact | high | Evidence gate is disconnected and citations receive invented confidence/validity | `TASK-AGENT-EVIDENCE-002` | `TASK-WEB-CITE-003` | W2 | open | Claim-level support and source lifecycle gate every policy assertion; unknown remains unknown in UI. |
| FINDING-013 | observed fact | high | Retrieved content can influence prompts without an indirect-injection boundary | `TASK-AGENT-INJECT-001` | - | W2 | open | Injection-bearing sources cannot change policy, tool selection, arguments, output rules, or authorization. |
| FINDING-014 | observed fact | high | Live provider egress and paid fallback are not explicitly authorized | `TASK-AGENT-EGRESS-001` | - | W2 | open | Demo/test are network-denied; missing transfer or budget approval disables live routes and paid fallback. |
| FINDING-015 | observed fact | high | Provider budget, deadlines, stream terminal states, and reasoning redaction are incorrect | `TASK-AGENT-BUDGET-001` | `TASK-AGENT-STREAM-001`, `TASK-AGENT-TRACE-002` | W2 | open | Hard caps use remaining budget, malformed/incomplete streams fail safely, traces are complete and privacy-safe. |
| FINDING-016 | observed fact | high | Existing evals do not prove production AI paths | `TASK-EVAL-AUD-001` | - | W4 | open | Hermetic end-to-end suites cover confirmation, evidence, injection, safety, egress, degradation, and false-success. |
| FINDING-017 | observed fact | high | Staff, schedule, privacy, knowledge, home, and admin surfaces present fabricated or local-only state | `TASK-WEB-STAFF-003` | `TASK-WEB-SCHED-004`, `TASK-WEB-PRIV-003`, `TASK-WEB-KNOW-003`, `TASK-WEB-HOME-003`, `TASK-WEB-ADMIN-001` | W3 | open | Empty/error/unknown are distinct; only server receipts produce success; demo data is explicit and isolated. |
| FINDING-018 | observed fact | high | Dialog/role boundaries and result-unknown recovery are incomplete | `TASK-WEB-A11Y-003` | `TASK-WEB-RESULT-001` | W3 | open | Server authorization remains authoritative; keyboard/focus works; reconciliation prevents blind duplicate retry. |
| FINDING-019 | observed fact | high | Release evidence, CI, dependencies, and IaC claims are not reproducible | `TASK-OPS-RELEASE-002` | `TASK-TEST-CI-002`, `TASK-REPO-DEP-002`, `TASK-INFRA-CDK-002` | W4 | open | Locked clean build, full gates, real or honestly labelled IaC, and evidence-backed release/DR status pass. |

## 5. Wave order

### Wave 0 — governance and authority

Run `TASK-GOV-AUD-001` and `TASK-GOV-AUD-002`. Human owners then review the approved sources required by security, privacy, action-contract, AI, and release tasks. No code task becomes `ready` merely because its YAML exists.

### Wave 1 — security, false success, and data integrity

Prioritize authentication/session boundaries, disabling direct writes, one-time confirmation, durable repositories/audit, and the agent confirmation/execution/handover chain. Keep affected write and emergency capabilities disabled until their failure-path evidence passes.

### Wave 2 — AI correctness and privacy

Connect evidence gating, indirect prompt-injection controls, default-deny egress, budget/stream controls, safe trace semantics, privacy receipts, retention, and booking concurrency. These tasks must use deterministic fakes and synthetic data.

### Wave 3 — truthful frontend and accessibility

Remove local-only operational success and fabricated current data. Add result reconciliation, authoritative role/session handling, focus management, and explicit simulation labelling.

### Wave 4 — independent evidence and operations

Build hermetic AI evals, locked CI, dependency verification, honest IaC classification, real readiness probes, and run-scoped release/DR evidence. A manifest is an index to evidence, not evidence by itself.

## 6. Scheduling and conflict policy

At most four tasks may run concurrently. A pair may run together only when all dependencies are accepted, required approvals are attached, resolved write paths do not overlap, conflict keys are disjoint, and neither task changes a shared migration, lockfile, generated contract, task catalog, or release manifest. AI graph, confirmation, execution, evidence, and trace tasks are intentionally serialized through dependencies because they share state-machine semantics even where file paths differ.

## 7. Definition of closure

A finding closes only when the assigned task output validates against `tasks/task-output.schema.json`, every acceptance criterion maps to reproducible evidence, every verification command exits as expected, the exact diff stays inside scope, no prior working-tree state is overwritten, and an independent reviewer confirms that negative paths cause no unauthorized side effect or fabricated success. Documentation, fixtures, test names, screenshots, and self-attested manifests alone do not close a finding.

## 8. Authoring verification and open blocker

At authoring time, `python -B tasks/tools/validate_catalog.py` passed with `VALID tasks=239 phases=10 approval_required=106`. The report references 38 unique remediation IDs and every referenced YAML exists. All 38 tasks are `draft`; no readiness or acceptance transition was performed.

`python -B -m pytest -q tests/delivery/test_task_catalog.py` currently has one failing assertion because the pre-existing test hard-codes `VALID tasks=201` while the validated catalog now contains 239 tasks. The existing test file was already modified before this package and is outside the authorized documentation/catalog-only mutation scope, so this authoring pass did not overwrite it. `TASK-GOV-AUD-002` owns replacement of the brittle constant with a catalog-derived assertion after review. Global `git diff --check` also reports pre-existing trailing blank lines in web files outside this package; the scoped catalog diff check is clean.
