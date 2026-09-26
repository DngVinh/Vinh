---
document_id: "DOC-GOV-IDS-001"
version: "1.0.0"
status: "approved"
owner: "Documentation Chief Editor"
approvers: ["Architecture Owner", "Quality Owner"]
last_updated: "2026-09-22"
---

# Identifier conventions

Identifiers are immutable. Deleted or superseded IDs are never reused.

## Normative identifier families

The following are the complete identifier families currently used as normative IDs in the repository. A family may have a scoped subfamily; its example is an existing ID, not a template for a new policy.

| Family / pattern | Meaning | Existing example |
|---|---|---|
| `DOC-<DOMAIN>-...-<NNN>` | Controlled document artifact; domains include `GOV`, `PROD`, `SVC`, `UX`, `ARCH`, `ADR`, `API`, `DATA`, `EVT`, `INT`, `AI`, `RAG`, `TOOL`, `SEC`, `PRIV`, `THR`, `OPS`, `QUAL`, `AGENT`, `DEL`, `INDEX` | `DOC-SEC-010` |
| `DEC-*` | Decision register decision | `DEC-015` |
| `ASM-*` / `OQ-*` | Assumption / open question | `ASM-003`, `OQ-008` |
| `OBJ-*` / `KPI-*` | Product objective / metric | `OBJ-001`, `KPI-015` |
| `REQ-F-*` / `REQ-NF-*` | Functional / non-functional requirement | `REQ-F-CHAT-001`, `REQ-NF-SEC-001` |
| `AC-REQ-*` / `AC-TASK-*` | Requirement or task acceptance criterion | `AC-REQ-F-CHAT-001-01` |
| `UC-*` / `TP-*` | Use case / requirement trace profile | `UC-TICKET-003`, `TP-CHAT` |
| `SVC-*` / `SLA-*` / `HITL-*` | Service blueprint, journey, queue, role, escalation or SLA rule | `SVC-QUE-001`, `SLA-SYS-001`, `HITL-002` |
| `UX-IA-*`, `UX-SCR-*`, `UX-INT-*`, `UX-STATE-*`, `UX-TRUST-*`, `UX-ACT-*`, `UX-A11Y-*`, `UX-CONTENT-*`, `UX-EMR-*` | UX information architecture, screen, interaction, state, trust, action, accessibility, content or emergency rule | `UX-SCR-001`, `UX-STATE-001` |
| `UI-MATRIX-VAL-*` | UI state-matrix validation | `UI-MATRIX-VAL-001` |
| `ARCH-*` / `ADR-*` | Architecture specification / architecture decision record | `ARCH-001`, `ADR-015` |
| `API-BASE-*`, `API-CONV-*`, `API-ACTION-*`, `API-BOOKING-*`, `API-DOC-*`, `API-ERR-*`, `API-IDENTITY-*`, `API-KNOW-*`, `API-OPS-*`, `API-POLICY-*`, `API-TICKET-*` | REST/SSE API contract rule | `API-CONV-001` |
| `EVT-*` / `MSG-*` | Event / event-message contract | `EVT-TICKET-001`, `MSG-TICKET-001` |
| `DATA-*` / `INT-*` | Data-model, lifecycle or integration contract | `DATA-DOC-004`, `INT-LLM-001` |
| `AI-SYS-*`, `AI-GW-*`, `AI-NODE-*`, `AI-PROMPT-*` | AI system, provider gateway, graph node or governed prompt | `AI-GW-001`, `AI-PROMPT-ANSWER-001` |
| `RAG-*` / `TOOL-*` | Retrieval/ingestion rule or tool policy/contract | `RAG-ING-001`, `TOOL-TICKET-001` |
| `EVAL-*` / `RUBRIC-*` | Evaluation case, suite, gate or scoring rubric | `EVAL-RAG-001`, `RUBRIC-GROUNDED-ANSWER` |
| `SEC-*` / `PRIV-*` / `THR-*` | Security control, privacy control or threat/abuse case | `SEC-AUTHZ-006`, `PRIV-DPIA-001`, `THR-ABUSE-001` |
| `SLO-*` / `OPS-*` / `COST-*` | Reliability objective, operational specification or cost rule | `SLO-API-001`, `OPS-ENV-SPEC-001` |
| `ALM-*` | Operational alarm | `ALM-API-001` |
| `DASH-*` | Operational dashboard | `DASH-OVERVIEW-001` |
| `RB-*` | Executable operational runbook | `RB-API-001` |
| `ORR-*` | Operations-readiness requirement | `ORR-GOV-001` |
| `GATE-*` / `TEST-*` | Release gate or test/evidence identifier | `GATE-REL-003`, `TEST-SEC-AUTHZ-001` |
| `TASK-<LAYER>-<DOMAIN>-<NNN>` | Atomic implementation task | `TASK-API-IDENTITY-001` |
| `MS-*` / `RSK-*` | Delivery milestone / delivery risk | `MS-MVP-001`, `RSK-001` |
| `CR-*` / `RELDEC-*` | Reserved governance namespace for an approved change request / release decision; no instance is allocated in the current baseline | — |
| `SRC-*` | Registered external source | `SRC-AWS-001` |

## Non-canonical names that MUST NOT be minted

`ALARM-*` and `RBK-*` do not exist as IDs in the completed documentation. Use `ALM-*` for alarms and `RB-*` for runbooks. `ENV-*` and `RUN-*` likewise are descriptive terms, not standalone canonical prefixes: environment specifications use `OPS-ENV-*` and runbooks use `RB-*`. This avoids creating parallel, untraceable identifier namespaces.

## Requirement format

Each requirement MUST contain:

- one testable behavior;
- actor and preconditions;
- normative statement using MUST/MUST NOT;
- acceptance examples;
- failure behavior;
- security/privacy classification;
- links to design, contract, tests and metrics.

## Task ID domains

Use: `TASK-<LAYER>-<DOMAIN>-<NNN>`.

Layers include `DOC`, `DATA`, `DB`, `API`, `AGENT`, `WEB`, `INFRA`, `TEST`, `EVAL`, `OPS`.
