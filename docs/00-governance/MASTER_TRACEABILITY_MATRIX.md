---
document_id: "DOC-GOV-MATRIX-001"
version: "1.1.0"
status: "reviewed"
owner: "Architecture and Quality Governance"
approvers: []
last_updated: "2026-09-22"
---

# Master traceability matrix

## Baseline

This is a documentation coverage baseline, not implementation evidence. The canonical requirement catalog (`DOC-PROD-012`) contains **125 reviewed requirements** — 77 functional and 48 non-functional — and **125 acceptance criteria**. Every requirement has at least one acceptance criterion. The task index, DAG and task directory are synchronized at **176 draft tasks**; no task is `ready`, `accepted`, implemented, or verified.

`tasks/requirement-acceptance-bindings.yaml` is the canonical machine-readable requirement-to-task and acceptance-to-task binding. It covers **125/125 requirements** and **125/125 acceptance criteria**. Direct task traceability additionally covers every high-risk P0 AUTH/KNOW/STAFF/PRIV requirement and every NFR; the binding exists so an executor can resolve all remaining upstream requirements before work starts.

```text
REQ (125) -> AC (125) -> design -> contract -> control -> test/eval -> task -> evidence
                         planned/reviewed/draft links        no execution evidence
```

## Requirement-profile coverage

The requirement catalog assigns a trace profile to 77 functional requirements. A profile supplies the intended design, contract and verification-plan path; it does not itself prove an ID-level control, task, or executed test.

| Profile | REQs | Design path | Contract path | Test/eval plan | Control basis | Task coverage state |
|---|---:|---|---|---|---|---|
| TP-GOV | 2 | `docs/03-ux/CONTENT_STYLE_VI.md` (draft) | `contracts/json-schema/config/disclaimer.schema.json` | `docs/08-quality/ACCEPTANCE_TEST_CATALOG.md` | `docs/06-security/12_SECURITY_CONTROLS.md` (draft) | binding complete; execution draft |
| TP-AUTH | 4 | `docs/06-security/06_AUTHENTICATION_AND_ENTRA_MIGRATION.md` (draft) | `contracts/json-schema/identity/synthetic-identity-claims.schema.json` | acceptance catalog (reviewed) | security authorization/authentication controls (draft) | binding complete; execution draft |
| TP-CHAT | 7 | `docs/05-ai/AI_SYSTEM_SPEC.md` (reviewed) | `contracts/openapi/v1/openapi.yaml` | acceptance catalog (reviewed) | AI/tool and security controls | partial/planned |
| TP-RAG | 5 | `docs/05-ai/RAG_PIPELINE.md` (reviewed) | `contracts/json-schema/citations/citation.schema.json` | `docs/08-quality/AI_EVALUATION_GATES.md` (reviewed) | AI and security controls | partial/planned |
| TP-SCHEDULE | 4 | `docs/04-architecture/contracts/INTEGRATION_CATALOG.md` (reviewed) | `contracts/tools/student-schedule-get.schema.yaml` | acceptance catalog (reviewed) | authorization/integration controls | partial/planned |
| TP-TICKET | 8 | `docs/04-architecture/contracts/ENTITY_LIFECYCLES.md` (reviewed) | `contracts/openapi/v1/openapi.yaml` | acceptance catalog (reviewed) | write-action controls | partial/planned |
| TP-DOC | 4 | entity lifecycles (reviewed) | `contracts/tools/document-request-create.schema.yaml` | acceptance catalog (reviewed) | write/privacy controls | partial/planned |
| TP-ROOM | 8 | integration catalog (reviewed) | `contracts/openapi/v1/openapi.yaml` | acceptance catalog (reviewed) | authorization/write controls | partial/planned |
| TP-HITL | 9 | `docs/02-service-design/HANDOVER_AND_EMERGENCY_PLAYBOOK.md` (draft) | `contracts/json-schema/handover/handover.schema.json` | acceptance catalog (reviewed) | sensitive-case/privacy controls | partial/planned |
| TP-STAFF | 7 | `docs/02-service-design/QUEUES_AND_ROUTING.md` (draft) | `contracts/openapi/v1/openapi.yaml` | acceptance catalog (reviewed) | queue authorization controls | partial/planned |
| TP-KNOW | 10 | `docs/05-ai/RAG_PIPELINE.md` (reviewed) | `contracts/openapi/v1/openapi.yaml` | acceptance catalog (reviewed) | provenance and authorization controls | partial/planned |
| TP-OPS | 5 | `docs/07-platform/OBSERVABILITY.md` (draft) | `infra/specs/dashboards.yaml` | acceptance catalog (reviewed) | operational/security controls | partial/planned |
| TP-PRIV | 4 | `docs/06-security/03_DATA_FLOW_AND_PRIVACY.md` (draft) | `contracts/json-schema/privacy/privacy-request.schema.json` | `docs/08-quality/SECURITY_TEST_PLAN.md` (reviewed) | privacy controls | partial/planned |
| Unprofiled non-functional | 48 | Requirement-specific downstream paths are resolved in `tasks/requirement-acceptance-bindings.yaml` | task-bound contract/design references | quality/security plans and task verification | task-bound controls | binding complete; execution draft |

## Coverage interpretation

| Chain segment | Current source | Observed state |
|---|---|---|
| Requirement → AC | `docs/01-product/requirements.yaml` | 125/125 requirements have acceptance criteria. |
| AC → design/contract/test plan | `trace_profiles` plus `tasks/requirement-acceptance-bindings.yaml` | 77 functional requirements have profile paths; all 48 non-functional requirements have explicit task bindings. |
| Design/contract → controls | security/privacy control catalog and individual task traceability | The canonical requirement rows do not contain control IDs. Controls are planned in draft security/privacy sources and must be bound before a task becomes ready. |
| Tests/evals → evidence | quality/evaluation specifications and `evals/` fixtures | Plans and synthetic fixtures exist; no release-scoped evidence IDs are recorded. Status: `not_verified`. |
| Requirement → task | `tasks/requirement-acceptance-bindings.yaml`, task index and item files | 125/125 requirements and 125/125 acceptance criteria have canonical task bindings; high-risk P0 domains and all NFR additionally have direct task traceability. |

## Controls and verification rules

For every write behavior, the mandatory chain includes authorization, authoritative preview, explicit confirmation, idempotency and audit. For personal data it includes classification, purpose, retention and authorized roles. For LLM tools it includes deterministic backend authorization and schema validation. These rules come from `DOC-GOV-TRACE-001`, `DOC-TOOL-001`, `DOC-SEC-007`, and the reviewed quality package; they remain planned until approved sources, task bindings and evidence are present.

Tests and evaluations are synthetic-only. Validators, fixtures, schemas and plans do not constitute test-run evidence, implementation completion, real-data approval, pilot approval, or production approval.

## Limits that block completion

- Requirements are `reviewed`, not approved; essential downstream architecture, service, UX, security/privacy and platform sources are still `draft`.
- All 176 indexed tasks are `draft`; none may be started until dependencies and required human approvals satisfy the executor contract.
- `OQ-001` through `OQ-008` remain open. They block real data, real identity, institutional integrations, live provider/data transfer, retention commitments, budgeted services, pilot and production as applicable.
- There are no immutable, release-scoped test/eval/approval evidence records. Therefore every release gate remains `not_verified` and no implementation or production approval is implied.
