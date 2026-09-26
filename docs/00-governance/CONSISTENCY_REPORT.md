---
document_id: "DOC-GOV-CONSISTENCY-001"
version: "1.1.0"
status: "reviewed"
owner: "Documentation Chief Editor"
approvers: []
last_updated: "2026-09-22"
---

# Consistency report

## Scope and conclusion

This report reconciles the current filesystem inventory with the documentation index. It is an editorial/structural review only. It does **not** approve implementation, a simulated demo, a pilot, real personal data, institutional integrations, paid providers, or production.

## Exact successful validation observed

The current offline validation results are:

```text
VALID tasks=176 phases=10 approval_required=73
PHASES P00=10 P01=12 P02=16 P03=16 P04=29 P05=30 P06=17 P07=16 P08=18 P09=12

VALIDATION_OK
operations=32
requirements=125
security_controls=30
test_tasks=26
resolved_local_refs=290

VALIDATION_OK
schema_files=24
resolved_refs=464
jsonl_cases=28
red_team_scenarios=36
```

The following commands are offline and may be re-run from the repository root:

```powershell
$env:PYTHONDONTWRITEBYTECODE = '1'
python tasks/tools/validate_catalog.py
python contracts/tools/validate_openapi.py
python evals/validate_contracts.py
```

## Resolved former index defects

- Replaced the stale manifest entries that named paths absent from the filesystem with current paths and directory aggregates.
- Recorded document IDs, header statuses, owners, purposes and canonical-source flags for the indexed documentation package.
- Created the missing master traceability matrix and this consistency report.
- Corrected the index narrative from an all-`planned` picture to the actual mixed `approved`/`reviewed`/`draft` lifecycle state.
- Added the entry order, synthetic-only rule, offline validation commands, and no-automatic-commit/push rule to the root and documentation READMEs.
- Preserved the requirements catalog's stated recovery result: 125 requirements (77 functional, 48 non-functional), rather than the stale 121-count assertion described in that catalog.

## Current defects and blockers

| Area | Current fact | Effect |
|---|---|---|
| Task catalog and coverage | `task-index.yaml`, DAG and `tasks/items/` are synchronized at 176 draft tasks. `requirement-acceptance-bindings.yaml` covers 125/125 requirements and 125/125 acceptance criteria. | Structural traceability is complete; task execution remains blocked by lifecycle/approval gates. |
| Requirement approval | The canonical requirements catalog is `reviewed`, not `approved`. | No dependent task can infer readiness from it. |
| Design/security/platform approvals | Service design, UX, architecture/ADR, security/privacy and platform documentation are `draft`. | Their downstream tasks remain blocked from readiness. |
| Test/eval evidence | Synthetic plans, schemas and fixtures exist, but no immutable release-scoped evidence IDs are present. | All release decisions remain `not_verified`. |
| Real-data and launch authority | `OQ-001` through `OQ-008` remain open; launch blockers start `open`. | Real data, real users/identity, integrations, external-provider transfers, pilot and production are blocked as applicable. |

## Non-negotiable operating limits

- Use deterministic synthetic data, fake/local adapters and offline validation by default. Do not introduce real student/staff data, institutional credentials, official contacts, real integrations, or paid/live provider calls without the exact required approvals.
- A successful structural validator only demonstrates the checked structure. It does not satisfy task acceptance, security/privacy review, release evidence, human launch approval, or production authorization.
- Do not automatically commit, push, deploy, alter approval status, or resolve a governance discrepancy by changing a higher-authority source.
