---
document_id: "DOC-GOV-TRACE-001"
version: "1.0.0"
status: "approved"
owner: "Architecture and Quality Governance"
approvers: ["Product Owner", "Architecture Owner", "Security Owner", "Quality Owner"]
last_updated: "2026-09-21"
---

# Traceability policy

## Required chain

Every implemented behavior MUST be traceable across this chain:

```text
Objective/KPI
  -> Product requirement
    -> Use case and acceptance criterion
      -> Architecture/design decision
        -> API, data, event or tool contract
          -> Security/privacy control
            -> Atomic task
              -> Automated test or AI eval
                -> Release gate
                  -> Production metric
```

No `ready` task may omit its upstream requirement and acceptance criteria. No requirement may be considered delivered without downstream verification evidence.

## Trace link schema

Machine-readable artifacts SHOULD use the following shape:

```yaml
traceability:
  objectives: ["OBJ-..."]
  kpis: ["KPI-..."]
  requirements: ["REQ-F-...", "REQ-NF-..."]
  use_cases: ["UC-..."]
  design: ["ARCH-...", "ADR-..."]
  contracts: ["API-...", "DATA-...", "TOOL-..."]
  controls: ["SEC-...", "PRIV-..."]
  tasks: ["TASK-..."]
  verification: ["TEST-...", "EVAL-..."]
  release_gates: ["GATE-..."]
  metrics: ["KPI-...", "SLO-..."]
```

Empty arrays are allowed only when the artifact explains why the link is not applicable.

## Coverage rules

- Every P0/P1 functional requirement MUST have positive, negative, authorization and failure-path verification where applicable.
- Every write action MUST link to confirmation, idempotency, authorization and audit controls.
- Every personal-data field MUST link to a data class, purpose, retention rule and authorized roles.
- Every LLM tool MUST link to its deterministic backend API and must not bypass that API.
- Every emergency/sensitive behavior MUST link to classifier eval cases and handover service rules.
- Every SLO MUST link to telemetry and an operational response.
- Every architectural decision MUST identify affected requirements and migration consequences.

## Orphan detection

The documentation validation suite MUST fail when it finds:

- an unknown referenced ID;
- a duplicate ID;
- a P0/P1 requirement with no acceptance criterion;
- an accepted task with no verification evidence;
- a write tool without confirmation/idempotency controls;
- a personal-data field without classification or retention;
- a release gate with no executable or reviewable evidence source.

## Change impact

A changed requirement or contract MUST identify all affected downstream artifacts. If impact cannot be bounded, implementation tasks depending on the artifact revert to `blocked` until the traceability graph is reviewed.

