---
document_id: "DOC-PROD-013"
version: "1.1.0"
status: "reviewed"
owner: "Product Requirements Recovery Lead"
approvers: ["Product Owner", "Architecture Lead", "Security/Privacy Lead", "AI Quality Lead"]
last_updated: "2026-09-22"
---

# Requirement dependency map

## 1. Purpose and authority

This document explains the implementation dependency DAG encoded by each
`depends_on` list in `docs/01-product/requirements.yaml`. It does not replace
requirement semantics, acceptance criteria, failure behavior, classification,
or trace links in the source Markdown.

Authority order for recovery and execution:

1. `docs/00-governance/**`;
2. `requirements.yaml` as the canonical requirement catalog;
3. `FUNCTIONAL_REQUIREMENTS.md` and `NON_FUNCTIONAL_REQUIREMENTS.md` as generated explanatory views;
4. this dependency map as an explanatory implementation view;
5. downstream design, contracts, tests, and atomic tasks.

An edge `A -> B` in this document means **A is an implementation prerequisite
of B**; in YAML, `B.depends_on` contains `A`. Dependency does not mean that A
changes the normative meaning of B.

## 2. Recovery count discrepancy

The original recovery request stated that the Markdown contained 77 FR and 44 NFR,
which would total 121 requirements. Direct parsing of the explanatory
Markdown tables found:

| Source | Rows | Unique IDs | Duplicates |
|---|---:|---:|---:|
| `FUNCTIONAL_REQUIREMENTS.md` | 77 | 77 | 0 |
| `NON_FUNCTIONAL_REQUIREMENTS.md` | 48 | 48 | 0 |
| **Combined authoritative set** | **125** | **125** | **0** |

Exact parity, zero missing IDs, and the prohibition on inventing or dropping a
requirement therefore require **125 YAML entries**, not 121. The four-ID delta
is not an inferred addition; all 48 NFR IDs are explicit catalog rows. Any move
back to 121 requires a separately approved change to the canonical YAML catalog
and its derived Markdown views.

## 3. Domain inventory

| Type/domain | Count | Delivery concern |
|---|---:|---|
| F-GOV | 2 | Demo identity, disclaimer, synthetic provenance |
| F-AUTH | 4 | Session and trusted actor context |
| F-CHAT | 7 | Conversation, response class, citations, feedback |
| F-RAG | 5 | Effective-source retrieval and grounded claims |
| F-SCHEDULE | 4 | Actor-owned schedule read and failure states |
| F-TICKET | 8 | Typed draft, authorization, preview, confirmation, receipt |
| F-DOC | 4 | Document-request catalog and ticket specialization |
| F-ROOM | 8 | Availability, eligibility, booking, cancellation |
| F-HITL | 9 | User handover and deterministic safety path |
| F-STAFF | 7 | Queue scope, claim, response, transition, audit, transfer |
| F-KNOW | 10 | Source ingestion, review, publication, supersession, retirement |
| F-OPS | 5 | KPI, cost, alert, and safe-mode operations |
| F-PRIV | 4 | Notice, consent, privacy requests, ownership |
| NF-REL | 5 | Availability, degraded mode, backup, RPO, RTO |
| NF-PERF | 4 | FAQ, tool, write, and handover latency |
| NF-SCALE | 3 | Concurrency, daily volume, corpus stress profile |
| NF-SEC | 8 | Encryption, authorization, secrets, audit, abuse, SDLC, validation |
| NF-PRIV | 5 | Synthetic-only, LLM minimization, retention, isolation, transfer |
| NF-A11Y | 4 | WCAG, keyboard, assistive state, zoom/reflow |
| NF-OBS | 5 | Correlation, sanitization, KPI events, alerting, AI versions |
| NF-MAINT | 4 | Documentation-led work, gateway boundary, dependencies, migrations |
| NF-PORT | 3 | Containers, typed adapters, Entra replaceability |
| NF-DATA | 4 | Reproducibility, provenance, time, idempotent ingestion |
| NF-COST | 3 | Usage ledger, hard limits, threshold alerts |
| **Total** | **125** | **77 functional + 48 non-functional** |

## 4. Phase DAG

The phases are execution gates, not calendar estimates. Work inside a phase may
run in parallel only when atomic-task write scopes are disjoint.

```text
P0 Governance and immutable baselines
  GOV-001, HITL-005, NF-MAINT-001, NF-PORT-001, NF-DATA-001,
  NF-A11Y-002/003/004
       |
       v
P1 Identity, adapters, data lineage, supply chain
  GOV-002, AUTH-001, NF-PORT-002, NF-PORT-003,
  NF-DATA-002/003/004, NF-MAINT-003/004,
  NF-SEC-001/002/003/004/007, NF-A11Y-001
       |
       v
P2 Cross-cutting controls and telemetry
  AUTH-002/003/004, NF-SEC-005/006/008,
  NF-OBS-001/002/003/004/005, NF-PRIV-001..005,
  NF-REL-004/005, NF-COST-003
       |
       +----------------------+-----------------------+
       |                      |                       |
       v                      v                       v
P3 Student/service core  P3 Knowledge core      P3 Operations quality
  CHAT base              KNOW-001..010          PERF-001..004
  SCHEDULE-001..004             |               SCALE-001..003
  TICKET-001..008               v               REL-001..003
  ROOM-001..008           RAG-001..005          COST-001/002
  HITL-001..009                 |
  STAFF-001..007                v
  PRIV-001..004           CHAT-003/005
       |                  DOC-002
       v
P4 Composed workflows and operational surfaces
  DOC-001..004, OPS-001..005, final chat/citation presentation
       |
       v
P5 Acceptance and release evidence
  Contract, security, accessibility, AI quality, load, recovery,
  cost-control, and source-trace gates
```

### Phase entry gates

| Phase | Mandatory entry evidence |
|---|---|
| P0 | Governance decisions accepted; catalog IDs stable; synthetic-only boundary visible. |
| P1 | P0 requirement artifacts reviewed; adapter and data contracts selected; dependency allowlist available. |
| P2 | Typed adapter boundary exists; correlation and audit schemas can be tested; environment isolation is defined. |
| P3 | Authorization is default-deny; synthetic fixtures exist; cross-cutting failure, audit, redaction, and trace controls are testable. |
| P4 | Required domain state machines and contracts pass; no composed flow bypasses preview, confirmation, idempotency, or authorization. |
| P5 | All P0 upstream requirements and downstream design/contracts are approved; reproducible test evidence is attached. |

## 5. Cross-domain dependency rules

| Upstream domain | Downstream domain | Reason |
|---|---|---|
| GOV | AUTH, PRIV, SCHEDULE | A user-facing surface and synthetic data must carry the correct demo representation. |
| AUTH | CHAT, SCHEDULE, TICKET, DOC, ROOM, HITL, STAFF, KNOW, OPS, PRIV | Actor, roles, and scopes must originate from trusted server context. |
| KNOW | RAG | Retrieval can use only published, effective, immutable source versions. |
| RAG | CHAT, DOC | Grounded answers and cited eligibility conditions require validated evidence. |
| TICKET | DOC | A document request is a typed specialization of the confirmed ticket workflow. |
| SEC | REL, OBS, STAFF, OPS | Failure behavior, audit, alerting, and privileged actions depend on security controls. |
| PORT | SEC, OBS, integrations | Typed boundaries and externalized configuration precede provider-specific adapters and telemetry. |
| DATA | KNOW, SCALE, PRIV | Reproducible fixtures, provenance, time semantics, and idempotency precede evidence and scale tests. |
| OBS | REL, PERF, SCALE, COST, OPS | Thresholds cannot pass without complete, sanitized, versioned measurement events. |
| PRIV | LLM, OBS, COST | Egress minimization and data handling constrain model and telemetry payloads. |

## 6. Critical paths

### 6.1 Longest catalog path: grounded citation presentation

This is the longest current DAG path, containing 16 requirement nodes and 15
edges:

```text
REQ-F-GOV-001
 -> REQ-F-AUTH-001
 -> REQ-F-AUTH-002
 -> REQ-F-KNOW-001
 -> REQ-F-KNOW-002
 -> REQ-F-KNOW-003
 -> REQ-F-KNOW-005
 -> REQ-F-KNOW-006
 -> REQ-F-KNOW-007
 -> REQ-F-KNOW-008
 -> REQ-F-KNOW-009
 -> REQ-F-RAG-001
 -> REQ-F-RAG-002
 -> REQ-F-RAG-003
 -> REQ-F-RAG-004
 -> REQ-F-CHAT-003
```

The path is intentionally conservative: a citation UI is not considered ready
before identity, source governance, current-version resolution, hybrid
retrieval, claim evidence, and citation detail are implementable and testable.

### 6.2 Confirmed ticket and document-request path

```text
REQ-F-GOV-001 -> REQ-F-AUTH-001 -> REQ-F-AUTH-002
 -> REQ-F-TICKET-001 -> REQ-F-TICKET-002 -> REQ-F-TICKET-003
 -> REQ-F-TICKET-004 -> REQ-F-TICKET-005
 -> REQ-F-DOC-003 -> REQ-F-DOC-004
```

`REQ-F-TICKET-008` is also a prerequisite of ticket creation so that execution
has idempotent semantics before it can claim a successful receipt.

### 6.3 Staff mutation path

```text
REQ-F-GOV-001 -> REQ-F-AUTH-001 -> REQ-F-AUTH-002
 -> REQ-F-STAFF-006
 -> REQ-F-STAFF-002 / REQ-F-STAFF-004 / REQ-F-STAFF-005
 -> REQ-F-STAFF-007
```

Audit is deliberately upstream of high-impact staff mutations. Audit failure
therefore blocks, rather than merely annotates, a mutation.

### 6.4 Operations and resilience path

```text
REQ-NF-MAINT-001 -> REQ-NF-PORT-002 -> REQ-NF-OBS-001
 -> REQ-NF-OBS-003 -> REQ-NF-OBS-004
 -> REQ-NF-REL-005 -> REQ-NF-REL-002 / REQ-NF-REL-003
```

RPO and RTO remain `not_verified` until a restore drill produces evidence; the
existence of backup configuration is not sufficient.

## 7. Domain implementation prerequisites

| Domain | Requirement prerequisites | Required reviewed downstream artifacts before coding |
|---|---|---|
| Governance | REQ-F-GOV-001 first | `CONTENT_STYLE_VI.md`; `contracts/json-schema/config/disclaimer.schema.json`; acceptance catalog. |
| Identity | GOV-001, then AUTH-001/002 | Authentication/Entra design; synthetic identity schema; authorization matrix. |
| Conversation | AUTH-002, OBS-001/005 | AI system spec; OpenAPI conversation contract; response-class and trace tests. |
| Knowledge/RAG | AUTH-002, DATA-002/003/004, SEC-008 | RAG pipeline; knowledge API; citation schema; AI evaluation gates. |
| Schedule | AUTH-002, PORT-002 | Integration catalog; schedule tool schema; ownership/failure acceptance tests. |
| Ticket/document | AUTH-002, SEC-003/005, REL-004 | OpenAPI; action preview/confirmation schemas; ticket lifecycle; idempotency contract. |
| Room | AUTH-002, PORT-002, SEC-003/005 | Room OpenAPI/tool schemas; conflict and cancellation state tests. |
| HITL/safety | HITL-005 before normal routing | Handover playbook; handover schema; sensitive-case evaluation and alert evidence. |
| Staff | AUTH-002, STAFF-001/006 | Queue routing; state lifecycle; audit/authorization controls. |
| Privacy | GOV-001, AUTH-002, NF-PRIV controls | Data-flow/privacy and retention designs; `contracts/json-schema/privacy/privacy-request.schema.json`; security test plan. |
| Operations | OBS-003/004, COST-003, SEC-005 | Observability design; dashboard/alarms specs; acceptance and resilience tests. |
| Platform/release | PORT, SEC, OBS, REL, MAINT NFRs | Environment, CI/CD, backup/DR, SLO, release-gate, and evidence documents. |

## 8. Cycle policy

The requirement graph MUST remain a directed acyclic graph.

1. Every `depends_on` value MUST resolve to exactly one requirement ID in the
   same YAML catalog.
2. Self-dependencies and duplicate edges are invalid.
3. A P0 requirement MUST NOT gain a P1/P2 prerequisite unless an approved
   requirement change explicitly changes the release plan.
4. Trace references such as KPI, decision, use case, design, contract, or test
   IDs MUST NOT be interpreted automatically as implementation dependency
   edges.
5. A proposed edge is accepted only after full-graph topological validation.
6. Any cycle makes every involved implementation task `blocked`; an agent MUST
   NOT remove an edge or weaken a requirement to make the graph pass.
7. Breaking a cycle requires Product and Architecture approval and a recorded
   change impact across contracts, tasks, and tests.

Kahn topological validation is the canonical mechanical check: initialize the
queue with all zero-indegree nodes, remove nodes and outgoing edges, and require
the visited count to equal the requirement count.

## 9. Implementation-agent preflight

Before an atomic task consumes a requirement, the executor MUST verify:

- the requirement exists once in `requirements.yaml` and is not superseded;
- all `depends_on` requirements have accepted implementation evidence, not only
  reviewed prose;
- every required trace-profile design, contract, and test artifact exists and
  has the status required by the task;
- any `planned:` reference is treated as missing and blocks work that depends on
  it;
- the task references the exact acceptance-criterion ID;
- the task has disjoint write scope from parallel tasks;
- synthetic-only data, trusted actor context, default-deny authorization,
  redaction, audit, and correlation controls remain active;
- write actions include preview, explicit confirmation, token expiry,
  idempotency, reconciliation, and immutable receipt behavior;
- dependency failure and negative/authorization tests exist where applicable;
- the verification result can be attached without changing a requirement or
  expected result.

Catalog status is currently `reviewed`, not `approved`. Therefore this recovery
establishes a complete planning DAG but does not itself authorize an
implementation task to become `ready`.

## 10. Validation baseline

The 2026-09-22 recovery validation produced:

| Check | Result |
|---|---:|
| YAML parse | PASS |
| YAML requirement entries | 125 |
| Functional entries | 77 |
| Non-functional entries | 48 |
| Unique YAML IDs | 125 |
| Duplicate YAML IDs | 0 |
| Missing source IDs | 0 |
| Extra YAML IDs | 0 |
| Unknown dependency references | 0 |
| DAG cycle nodes | 0 |
| Trace-profile paths resolve to canonical artifacts | PASS — 13 profiles / 39 path references resolved on 2026-09-22 |
