---
document_id: "DOC-OPS-009"
version: "1.0.0"
status: "draft"
owner: "Data Resilience Owner"
approvers: ["SRE Lead", "Security Lead", "Privacy Owner", "Product Owner"]
last_updated: "2026-09-22"
---

# Backup, restore and disaster recovery

## 1. Objectives and truth status

| Objective | Target | Current evidence status |
|---|---:|---|
| RPO | ≤15 minutes | `not_verified` until PITR/restore drill |
| RTO | ≤60 minutes | `not_verified` until full application recovery drill |
| Availability | single-region Multi-AZ | architecture target; staging tests required |
| Regional DR | backup/restore, no automatic failover | `blocked` until approved cross-location target/privacy/budget |

RPO measures maximum business data loss from selected recovery point; RTO starts at formal recovery invocation and ends only when end-to-end smoke, integrity, authz and audit pass. Backup enabled is not proof.

## 2. Recovery classes

| Class | Scenario | Mechanism | Target |
|---|---|---|---|
| `REC-1` | Task/process failure | ECS replace/rollback | minutes; no data restore |
| `REC-2` | AZ/data node failure | ECS spread, RDS/Redis Multi-AZ failover | service recovery; no intended data loss |
| `REC-3` | Logical corruption/bad migration | RDS PITR/new instance, S3 version, app reconciliation | RPO/RTO target subject to drill |
| `REC-4` | Account/region disaster | approved backup copy + IaC reconstruction | unverified; no auto cross-region write failover |
| `REC-5` | Security compromise | clean-room rebuild from trusted artifacts/backups | incident-specific, integrity over speed |

## 3. Backup matrix

| Resource | Authoritative | Protection | Simulation retention | Restore validation |
|---|---:|---|---:|---|
| RDS PostgreSQL/pgvector | Yes | automated backup + PITR, Multi-AZ, AWS Backup snapshot as approved | 35 days (`PRIV-RET-011`) | isolated instance, schema/checksum/query/app smoke |
| S3 knowledge/artifacts | Yes for objects | versioning, encryption, lifecycle; optional replication only after approval | purpose-specific | restore version/prefix, checksum/provenance |
| S3 audit | Yes for evidence | versioning + append-only/object-lock design, dedicated KMS/access | 400 days simulation audit policy | read/integrity/access negative test |
| ElastiCache Redis | No | managed failover; snapshot optional for warm cache only | not business recovery | rebuild empty; verify source-of-truth behavior |
| SQS/DLQ | Transport | retention + DLQ, not backup | queue policy | schema/idempotent replay test |
| Secrets Manager | Required config | versioning/rotation; recovery procedure | security policy | resolve current/previous permitted stage, no value logging |
| KMS | Critical control | key policy/replica strategy only after approval; retain | indefinite/control policy | decrypt authorized backup in isolated recovery role |
| ECR images | Release artifact | immutable digest, lifecycle preserves active/rollback releases | release policy | pull by digest, signature/SBOM/provenance verify |
| CDK/templates/config | Rebuild source | version control + immutable release artifact | release/audit policy | synth/hash and stack reconstruction |
| Logs/traces | Operational | explicit log retention/archive | per classification | query/access test |

No Redis snapshot, SQS message or container filesystem is accepted as source of truth.

## 4. Backup controls

- Backup/vault/KMS roles separate from application runtime; app cannot delete recovery points.
- Production RDS deletion protection and CloudFormation retain/snapshot policy required.
- Backup jobs/age/failure have alarms and owner.
- Recovery point metadata includes environment, resource, encryption key, creation/expiry, release/schema/corpus version where relevant.
- Backup copy across Region/account is disabled until Privacy/Legal, Security and Finance approve destination/transfer/retention.
- Vault lock/object lock only enabled after policy and break-glass recovery are tested; immutability must not create unlawful retention.
- Backup must not silently extend C2/C3 retention. Deletion tombstones/ledger must be replayed after restore.

## 5. Standard restore procedure

### Prepare

1. Open change/incident; identify exact environment/resource, reason, target recovery point and authority.
2. Confirm restore uses isolated target names/VPC/account; never overwrite production source.
3. Verify artifact/image/template/config/schema versions and KMS/secret access.
4. Record expected RPO from last committed event vs recovery timestamp.

### Restore

5. Provision isolated network/security via accepted CDK.
6. Restore RDS to new endpoint; restore object versions/prefix into new bucket/prefix as policy permits.
7. Run schema compatibility check; do not automatically apply latest destructive migration.
8. Deploy exact compatible API/worker/web digests with provider external disabled initially.
9. Rebuild Redis empty. Recreate queues; reconcile outbox from database. Preserve old queue/DLQ evidence.
10. Reapply deletion tombstones/legal holds/retention state before user access.

### Validate

11. Integrity: schema, row/entity counts by safe aggregate, checksums, FK/domain invariants, knowledge provenance/vector counts.
12. Security: IAM/SG/KMS/authz negative tests, mock/real-data guard, audit append-only, no public data service.
13. Application: liveness/readiness, synthetic login, schedule, grounded citation, action preview/confirm/idempotent replay, ticket, queue worker.
14. Operations: alarms/dashboard/trace, backup schedule, release/config identity.
15. Data/Security/Product approve; only then controlled traffic change.

### Close

16. Measure RPO/RTO with UTC timestamps; document exclusions and residual risk.
17. Keep restored drill environment only for approved evidence duration; cleanup is a separate exact-target authorized task.

## 6. RDS PITR and migration recovery

- Restore PITR into new RDS; never rewind in place.
- Choose recovery time using audit/outbox/application evidence, not guess.
- Compare source/restored transaction boundary, idempotency records and outbox state.
- Events committed but not published are safely republished through relay; consumers deduplicate.
- External write with uncertain outcome must reconcile provider-side; restore does not authorize blind replay.
- Bad migration: prefer compatible app rollback if schema supports; otherwise forward-fix. Reverse destructive SQL is prohibited without explicit plan/approval.

## 7. Knowledge/object recovery

- `DocumentVersion` metadata/checksum and S3 object version must match.
- Restore active corpus pointer only to an eval-accepted corpus version.
- Quarantined/malicious/withdrawn sources remain quarantined after restore.
- Rebuild chunks/embeddings deterministically from approved source version when needed; do not treat vector index as irreplaceable truth.
- Citation resolver smoke verifies stored historical versions still resolve.

## 8. Regional DR limitation

V1 has no automatic cross-region failover. Before `REC-4` can claim the target:

- destination Region/account and data transfer approved;
- cross-location RDS/S3/audit/KMS strategy implemented and tested;
- DNS/certificate/provider/secret dependencies available;
- infrastructure and artifacts accessible without failed Region;
- restore drill meets RPO/RTO;
- operations/on-call/runbook and cost approved.

Without these, regional outage status is `unverified` and production readiness MUST fail; documentation MUST not imply Multi-AZ solves Region loss.

## 9. Drill schedule

| Drill | Staging cadence | Production readiness |
|---|---|---|
| RDS PITR isolated restore | before first release and quarterly target | required current evidence |
| S3 version/checksum restore | quarterly target | required |
| RDS/Redis Multi-AZ failover | before release and major engine change | required |
| Full application restore | before production and at least semiannual target | required |
| Regional clean-room tabletop/technical | before production; annual target | required if regional target claimed |
| Secret/KMS recovery | before production and after policy change | required |

Cadence is proposed operational policy; final owner/budget approval required. Failed drill opens tracked finding and invalidates prior `verified` claim for affected path.

## 10. Evidence schema

```yaml
restore_drill:
  drill_id: "DRILL-..."
  environment: "staging"
  scenario: "REC-3"
  source_resource_ref: "opaque"
  recovery_point_at: "RFC3339"
  invoked_at: "RFC3339"
  service_accepted_at: "RFC3339"
  measured_rpo_seconds: 0
  measured_rto_seconds: 0
  release_id: "immutable"
  checks: []
  data_real: false
  destructive_actions: []
  result: "passed|failed|partial"
  approved_by: []
  residual_risks: []
```

Numbers are populated by execution, never prefilled as success.

