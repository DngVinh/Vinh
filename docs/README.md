---
document_id: "DOC-INDEX-001"
version: "1.0.0"
status: "approved"
owner: "Documentation Chief Editor"
approvers: ["Product Owner", "Architecture Owner", "Security Owner", "Quality Owner"]
last_updated: "2026-09-22"
---

# Documentation map

The documentation set is both a human review package and the normative instruction system for implementation agents. Human-readable Markdown explains intent and decisions; YAML/JSON/OpenAPI artifacts express machine-checkable contracts.

## Entry order and package status

Read `00-governance/DOCUMENT_CONTROL.md`, `00-governance/DECISION_REGISTER.md`, `00-governance/DOCUMENT_MANIFEST.yaml`, `00-governance/MASTER_TRACEABILITY_MATRIX.md`, and `00-governance/CONSISTENCY_REPORT.md` before opening a domain package. Then use the applicable approved product requirement, reviewed/draft design and contract material, and finally the atomic task.

The package has mixed status: governance and selected product documents are `approved`; product recovery, contracts, AI, quality, delivery and agent-execution packages are generally `reviewed`; service design, UX, architecture/ADRs, security/privacy and platform/operations packages are `draft`. A document's presence, a successful structural validator, or a task's existence never promotes it to `approved`, `ready`, implemented, pilot-approved or production-approved.

All examples, fixtures, evaluation cases and local validation are synthetic-only. Real personal data, institutional credentials/integrations, live provider calls, pilots and production require the specific human approvals described in governance and security documentation.

## Documentation domains

| Directory | Purpose | Primary IDs |
|---|---|---|
| `00-governance` | Decisions, assumptions, terminology, source control, traceability rules | `DEC`, `ASM`, `SRC` |
| `01-product` | Vision, business case, PRD, personas, use cases, KPI definitions | `OBJ`, `KPI`, `REQ`, `UC` |
| `02-service-design` | Student/staff journeys, handover, SLA, operating model | `SVC`, `SLA`, `HITL` |
| `03-ux` | Information architecture, interaction and content specifications | `UX` |
| `04-architecture` | C4 views, domain boundaries, APIs, data, integrations, ADRs | `ARCH`, `ADR`, `API`, `DATA`, `INT` |
| `05-ai` | RAG, agent graph, tools, memory, prompts, guardrails and evaluation | `AI`, `RAG`, `TOOL`, `EVAL` |
| `06-security` | Threat model, privacy, authorization and security controls | `SEC`, `PRIV`, `THR` |
| `07-platform` | AWS, environments, CI/CD, observability, reliability and cost | `SLO`, `ENV`, `OPS`, `COST` |
| `08-quality` | Test strategy, release gates and acceptance evidence | `TEST`, `GATE` |
| `09-agent-execution` | Gemini execution protocol, task schema and orchestration rules | `AGENT`, `TASK` |
| `10-delivery` | Roadmap, RAID, RACI, rollout and operational readiness | `PLAN`, `RISK` |

## Normative order

When two artifacts conflict, the following precedence applies:

1. Applicable law and approved security/privacy policy.
2. Accepted decision records.
3. Approved product requirements and non-functional requirements.
4. Approved API, event, data and tool contracts.
5. Architecture and detailed design.
6. Atomic implementation task.

An implementation agent must stop and raise a change request rather than silently choosing between conflicting sources.

## Language

- Explanatory documentation and user-facing copy: Vietnamese.
- IDs, paths, APIs, schemas, code symbols and task outputs: English.
- Normative terms such as MUST, MUST NOT, SHOULD and MAY retain their RFC-style meaning.

## Local validation

From the repository root, run offline checks with bytecode writes disabled:

```powershell
$env:PYTHONDONTWRITEBYTECODE = '1'
python tasks/tools/validate_catalog.py
python contracts/tools/validate_openapi.py
python evals/validate_contracts.py
```

Record command output as structural evidence, then follow the task/evidence protocol. Agents must not automatically commit, push, deploy, change approval status, or infer a release decision from these commands.
