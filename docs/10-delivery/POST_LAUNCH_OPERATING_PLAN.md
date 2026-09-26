---
document_id: "DOC-DEL-009"
version: "1.0.0"
status: "reviewed"
owner: "Operations Readiness Lead"
approvers: ["Product Owner", "SRE Lead", "Security Lead", "AI Quality Lead", "Student Support Lead"]
last_updated: "2026-09-22"
---

# Post-launch operating plan

## 1. Scope

This is the operating handoff for an authorized synthetic pilot or future production release. It does not claim launch occurred. “Campus 24/7” means AI/self-service availability target, not 24/7 human staffing (`ASM-008`). Human hours/SLA remain configuration and must be approved before display.

## 2. Immediate post-deploy verification

Release Owner and SRE verify exact runtime manifest/digests/config/AI bundle; health/readiness; identity and default-deny authz; audit/correlation/alert delivery; synthetic P0 canaries; queue/outbox/backlog; citation/source resolution; external egress and cost caps. Any missing control invokes launch abort criteria.

No canary uses real student data or causes external notification. Write canaries use dedicated synthetic namespace and idempotency keys, and verify/reconcile exact resulting object.

## 3. Hypercare cadence

The following are planning review points, not human-response SLA:

| Window | Review |
|---|---|
| first 2 hours | continuous critical dashboard/alert ownership; verify every config/digest and P0 canary |
| first 24 hours | error/latency/backlog/authz/audit/AI hard metrics/cost and support queue review |
| days 2–7 | daily defect/risk/quality/source freshness/capacity review |
| weeks 2–4 | weekly KPI, AI subgroup, security anomaly, support outcomes and cost review |
| after four weeks | pilot outcome/production continuation review when applicable |

Actual staffed coverage and update cadence must be assigned in owner/on-call registry before production; `UNASSIGNED` blocks launch.

## 4. Operational dashboard contract

Each metric shows value, target, status, window, sample size, environment, freshness and data source. Missing data is `unknown/unavailable`, never zero/green.

Minimum views:

- availability, p50/p95/p99, error/timeout/retry/circuit and saturation;
- DB pool/failover, Redis health, SQS age/backlog/DLQ, outbox lag, worker throughput;
- grounded answer/abstain/citation/retrieval quality and model/prompt/corpus versions;
- preview→confirm→success/unknown funnel and hard-zero duplicate/unauthorized/unconfirmed writes;
- sensitive route/handover/queue status without raw sensitive content;
- auth deny/anomaly, audit completeness, secret/PII canary and egress destinations;
- AWS/LLM usage/cost with effective pricing date and 50/75/90% configured alerts;
- support backlog, assignment/transfer/reopen and SLA only when calendar approved.

## 5. Service modes and authority

| Mode | Trigger examples | Owner/action |
|---|---|---|
| `normal` | all required dependencies/quality healthy | OPS monitors |
| `degraded` / dependency-specific | noncritical dependency/latency/freshness issue | OPS disables affected capability and shows truthful state |
| `search_ticket_only` / `SEARCH_ONLY` | LLM/eval/prompt/corpus risk | AIQ/SEC/OPS disable generation/model routing |
| `READ_ONLY` | write/audit/confirmation integrity risk | OPS/SEC stop writes and reconcile |
| `maintenance` | approved maintenance | REL/OPS with abort/rollback owner |
| `suspended` | exposure/auth bypass/poisoning/unsafe systemic behavior | Incident Commander + SEC/PRIV contain; controlled recovery |

Mode change is versioned, confirmed/audited and verified through capability endpoint/UI. Restoration needs evidence, not elapsed time.

## 6. Incident and problem management

Use `SVC-ESC-001..004` and `SEC-IR-001..012`. Initial response: detect/classify, contain, preserve evidence, establish scope, communicate approved facts, eradicate/recover, verify controls and review. Case priority and incident severity stay separate.

SEV0/SEV1 or hard-zero event opens root-cause/problem record. Corrective action includes regression test, affected trace/gate update, owner/due date and effectiveness review. AI output is evidence signal, not incident decision-maker.

## 7. Daily/weekly operating work

Daily/shift when staffed:

- check P0/P1/unassigned/breach-risk cases, dependencies, source freshness, alerts and failed notifications;
- hand over every open high-priority case with current/receiving owner, verified fact, next action and acknowledgement;
- reconcile `unknown` writes and DLQ/outbox without blind replay;
- verify service mode and capability disclosure.

Weekly:

- review backlog/transfer/reopen/abstention/citation reports and unmet need;
- sample staff/AI answer quality and access/audit events using minimized synthetic or approved workflow;
- review model/source/dependency/config drift, vulnerabilities, cost and capacity;
- update risks/actions with owner/due/evidence.

## 8. AI and knowledge operations

Any prompt/model/provider/tool/retrieval/source change follows change control and reruns affected evaluation. Monitor versioned quality signals and reviewed false positive/negative samples; user feedback is not sole ground truth. Bad source release is rolled back by active corpus pointer while preserving history. No direct production prompt edit.

## 9. Security/privacy/data operations

Monitor access/deny anomalies, egress, secret/PII canaries, audit completeness, environment isolation and retention-policy state. Until real-data authorization, synthetic-only assertion remains active. Suspected real data is contained/quarantined and handled as privacy incident; never copied to debug lower environment.

Retention defaults and evidence retention remain configuration/governance items; agents do not delete shared/unknown data or evidence.

## 10. Release acceptance and hypercare exit

Hypercare exits only when:

- exact release remains deployed or a documented rollback superseded it;
- no unresolved Critical/High/S1 or hard-zero defect;
- SLO/quality/security/cost data is complete for declared observation window;
- queue/backlog/unknown writes are owned and within approved operating policy;
- alerts/runbooks/on-call and support/knowledge handoff work;
- post-launch defects/risks/actions have owner and target;
- Product, QE, Security/Privacy, AIQ, OPS and Service owners record acceptance for their domain.

Otherwise extend hypercare, disable affected capability or rollback; do not normalize unknown state.

## 11. Post-launch review

Review release outcome against objectives/KPIs, failed/near-miss cases, user/support feedback, performance/cost, security/privacy and operational burden. Record continue/adjust/rollback decision, root causes, action owners and whether assumptions `ASM-001..010` need governance change. Future expansion or SaaS remains separate discovery/change control.
