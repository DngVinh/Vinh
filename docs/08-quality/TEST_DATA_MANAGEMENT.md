---
document_id: "DOC-QUAL-008"
version: "1.0.0"
status: "reviewed"
owner: "Test Data Management Lead"
approvers: ["Privacy Lead", "AI Quality Lead", "Knowledge Governance Lead", "Security Lead"]
last_updated: "2026-09-22"
---

# Test data management

## 1. Non-negotiable boundary

Development, test, demo, staging and evaluation MUST use deterministic synthetic operational/personal data. Real student records, real staff credentials, production exports, directly contactable identities and unapproved confidential HUCE content are prohibited. Public HUCE material may inform taxonomy/provenance but must not imply endorsement and must respect source/licensing controls.

Discovery of suspected real data changes the run to `blocked`, quarantines the artifact without copying it further, and opens security/privacy triage. Agent MUST NOT redact in place and continue as though provenance were proven.

## 2. Dataset classes

| ID | Dataset | Required contents | Prohibited |
|---|---|---|---|
| TEST-DATA-ID-001 | synthetic identities/roles | four roles, active/disabled, ownership/queue scopes, `SYN########` marker | real names/emails/phones/student IDs |
| TEST-DATA-OPS-001 | schedules/tickets/docs/rooms/handovers | success/empty/conflict/expired/foreign/unknown-outcome states | copied production records |
| TEST-DATA-KNOW-001 | knowledge corpus | synthetic policies plus approved public-source metadata, versions/effective dates/locators/checksums | claim that synthetic policy is official |
| TEST-DATA-AI-001 | AI evaluation | gold answer/evidence, tools, abstain, safety, injection, route cases | sealed split in coding context; raw sensitive text |
| TEST-DATA-LOAD-001 | volume corpus | 5,000 students, 100 staff, 10,000 chat/day model, 1,000 actions/day, up to 100,000 chunks | uncontrolled random data without manifest |
| TEST-DATA-SEC-001 | abuse/canary corpus | fake secret/PII markers, injection payloads, role attacks | functional credentials or live exploit target |

## 3. Reproducibility contract

Every materialized dataset MUST have:

```yaml
dataset_manifest:
  dataset_id: TEST-DATA-...
  version: 1.0.0
  generator_revision: <git-sha-or-artifact-hash>
  schema_version: <version>
  seed: <integer-or-named-seed>
  locale: vi-VN
  timezone: Asia/Bangkok
  record_counts: {}
  source_refs: []
  classification: synthetic
  generated_at: <RFC3339>
  canonical_checksum: sha256:<64-hex>
  pii_scan_report_ref: <artifact-ref>
  approved_by: []
```

Canonical serialization must define field order, timestamps and volatile-field normalization. Same generator revision/schema/seed MUST produce identical canonical checksum (`REQ-NF-DATA-001`).

## 4. Synthetic identity rules

- Names are clearly fictional; identifiers use reserved synthetic patterns.
- Email/phone values use non-routable/reserved patterns and cannot reach a real person.
- Every object includes `is_synthetic: true` or equivalent schema marker and human-facing disclaimer where rendered/exported.
- Relationships intentionally include own/foreign actor, role boundaries, orphan prevention, concurrency and state edges.
- Sensitive/emergency cases are artificial labels and phrases reviewed to avoid real-person narratives.

## 5. Knowledge and evaluation data

Each knowledge source retains source type, canonical reference, owner/issuer, authority, approval status, effective interval, version, checksum, locator map and simulation marker. Parsed chunks are immutable children of a source version. Draft/future/expired/retired content exists in fixtures specifically to test exclusion.

Evaluation splits are assigned before candidate tuning. Near-duplicate detection and leakage report are required. Gold label change requires independent reviewer/change record; failing cases cannot be removed or relabeled after seeing output solely to pass.

## 6. Data profiles

| Profile | Purpose | Minimum characteristics |
|---|---|---|
| `tiny` | unit/local | one object per state + negative edges |
| `integration` | DB/API/queue | multi-user/role, concurrency, version history, failures |
| `acceptance` | browser/E2E | all P0 journeys and accessibility copy |
| `ai-dev` | nonsealed iteration | dev split only, reviewed gold evidence |
| `ai-sealed` | release evaluation | inaccessible to implementation prompt; controlled runner |
| `performance` | load/capacity | reference cardinality/volume with deterministic sharding |
| `security` | adversarial | canaries, malformed boundaries and benign controls |

Profile/version/seed must be part of test report. Tests must not silently fall back from requested profile.

## 7. Isolation and lifecycle

Every run receives a unique namespace and least-privilege credentials. Data stores, queues, object prefixes, cache keys and traces include run ID. Cleanup may operate only on resources bearing the exact disposable run label and only after evidence capture; inability to prove exact scope leaves resources quarantined for human review rather than broad deletion.

Conversation data defaults to 90-day simulated retention (`REQ-NF-PRIV-003`), but automated destructive deletion remains disabled until approved retention workflow exists. Test teardown does not authorize destructive operations against shared or unknown environments.

## 8. Privacy/quality validation

| Test ID | Oracle |
|---|---|
| TEST-DATA-REPRO-001 | two clean generations with same inputs have identical canonical checksum |
| TEST-DATA-SCHEMA-001 | every record validates; referential/state/date constraints hold |
| TEST-DATA-PROV-001 | every source/chunk/citation reverse-resolves to immutable source version |
| TEST-DATA-PII-001 | scanner and sampled review find no unmanifested real/contactable identifiers |
| TEST-DATA-SPLIT-001 | no exact/near duplicate or provenance leak across eval splits beyond approved threshold documented in plan |
| TEST-DATA-ISOLATE-001 | run namespace cannot read another run/user/role data |
| TEST-DATA-IDEM-001 | repeated generation/import produces same objects/counts and no duplicate current records |
| TEST-DATA-TIME-001 | before/start/end/after and timezone boundaries are explicit and deterministic |

All eight checks feed `GATE-REL-010`. Missing scanner provenance or sample review is `not_verified`.

## 9. Ownership

QE owns fixture usability; Privacy/Security owns prohibited-data policy and incident triage; AI Quality owns eval splits/gold labels; Knowledge Governance owns source provenance; Performance QE owns volume shape. No coding agent may approve its own change to a critical gold label or privacy allowlist.
