---
document_id: "DOC-QUAL-009"
version: "1.0.0"
status: "reviewed"
owner: "Quality Governance Lead"
approvers: ["Architecture Governance Lead", "Release Owner", "Security Lead", "AI Quality Lead"]
last_updated: "2026-09-22"
---

# Traceability and evidence

## 1. Required graph

```text
OBJ/KPI
 -> REQ-F/REQ-NF
 -> UC/acceptance criterion
 -> ARCH/ADR
 -> API/EVT/DATA/TOOL contract
 -> SEC/PRIV/AI/OPS rule
 -> TASK
 -> TEST/EVAL
 -> evidence run
 -> GATE-REL
 -> release decision/runtime metric
```

A link may be `not_applicable` only with reason and reviewer. Unknown or duplicate ID, orphan P0/P1 requirement, accepted task without evidence, write tool without confirmation/idempotency, or gate without reproducible evidence fails traceability.

## 2. Evidence record schema

```yaml
evidence:
  evidence_id: EVD-<run>-<sequence>
  test_id: TEST-...
  result: passed|failed|blocked|not_run|not_verified|inconclusive
  executed_at: <RFC3339>
  duration_ms: <integer>
  source_revision: <git-sha>
  release_candidate_id: <id-or-null>
  image_digests: []
  environment_id: <nonsecret-id>
  config_hash: sha256:<64-hex>
  contract_hashes: []
  dataset_manifest_id: <id>
  dataset_hash: sha256:<64-hex>
  model_prompt_index_tool_versions: {}
  command: <sanitized-command>
  exit_code: <integer-or-null>
  assertions:
    total: <integer>
    passed: <integer>
    failed: <integer>
  artifact_refs: []
  artifact_hashes: []
  traces_to: []
  defects: []
  waivers: []
  executor: <agent-or-runner-id>
  reviewer: <role-or-null>
  notes: <sanitized-text>
```

Required field absent makes evidence invalid. A zero exit code with zero required tests, incomplete assertions or missing artifact is not pass.

## 3. Evidence types and minimums

| Evidence type | Minimum content | Not sufficient alone |
|---|---|---|
| Static/unit | command, exit, case list, report hash, coverage by requirement | terminal screenshot |
| API/contract | contract + fixture hashes, validator version, operation/case matrix | schema parses without negative fixtures |
| Mutation | before/after state, invocation count, audit/event/correlation | HTTP 2xx |
| UI/E2E | browser/runtime/version, DOM/accessibility artifact, backend state oracle | screenshot only |
| AI eval | dataset/model/prompt/index/tool/policy hashes, metrics/subgroups/cases/review | aggregate score without cases |
| Security | scanner/signature version, scope, findings/suppressions, sanitized reproducer | “no issues observed” prose |
| Performance | workload/script/env/raw result hashes and percentiles/errors/saturation | average latency |
| Recovery/rollback | timeline, artifact IDs/checksums, functional probes and witness | infrastructure reports healthy |
| Manual review | checklist version, exact candidate, reviewer role/time/findings | informal approval message |

## 4. Trace matrix row

Each implemented behavior must produce a row:

```yaml
- requirement_id: REQ-F-TICKET-005
  acceptance_ids: [AC-REQ-F-TICKET-005-01]
  design_ids: [ARCH-006, ADR-016]
  contract_ids: [API-ACTION-002, API-ACTION-003]
  control_ids: [SEC-CTRL-003]
  task_ids: [TASK-...]
  verification_ids: [TEST-ACC-TICKET-003, TEST-CON-IDEM-001]
  gate_ids: [GATE-REL-003, GATE-REL-004, GATE-REL-006]
  evidence_ids: []
  status: planned
```

Until real evidence IDs exist, status is `planned`/`not_verified`; documentation must not fabricate run IDs.

## 5. Gate aggregation

A gate engine reads only evidence matching exact release tuple and applicable test IDs. Aggregation rules:

1. any required `failed` -> gate `failed`;
2. no failure but any required `blocked` -> gate `blocked`;
3. any missing/`not_run`/`not_verified`/`inconclusive` -> gate `not_verified`;
4. all required `passed`, no expired waiver and approvals complete -> `passed`;
5. evidence from another revision/config/dataset cannot be inherited unless the gate declares an approved unaffected proof with impact analysis.

All non-`passed` states block promotion for mandatory gates.

## 6. Integrity, privacy and retention

Evidence artifacts are immutable/content-addressed where possible. Reports exclude secrets, raw tokens, direct identifiers, full prompts/transcripts and sensitive payloads; use synthetic case IDs, hashes and redacted excerpts. Corrections create a new artifact linked by `supersedes`; never overwrite a failed report.

Retention duration for release evidence is `UNCONFIGURED` pending records policy. Until approved, evidence must be preserved and not deleted by agents. Production evidence storage, signing and legal retention require human approval.

## 7. Orphan and consistency checks

| Test ID | Check |
|---|---|
| TEST-TRACE-001 | every referenced ID resolves to one canonical definition |
| TEST-TRACE-002 | no duplicate immutable ID or reused superseded ID |
| TEST-TRACE-003 | every P0/P1 requirement has positive, negative, auth and failure verification where applicable |
| TEST-TRACE-004 | every write path maps confirmation, idempotency, authorization and audit tests |
| TEST-TRACE-005 | every AI/sensitive path maps eval dataset/case/gate and service handover rule |
| TEST-TRACE-006 | every SLO/NFR maps measurement method, telemetry and operational response |
| TEST-TRACE-007 | every accepted task has evidence and no out-of-scope file changes |
| TEST-TRACE-008 | every release gate has owner, applicability, oracle and evidence source |

## 8. Review protocol

Release Engineering assembles; QE verifies completeness; each domain gate owner validates interpretation; Release Owner signs aggregation. Security/Privacy, AI Quality and SRE approvals are mandatory for their gates and cannot be replaced by Product acceptance. Reviewer records exact candidate and conflicts of interest.
