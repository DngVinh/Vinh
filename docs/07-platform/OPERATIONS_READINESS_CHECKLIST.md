---
document_id: "DOC-OPS-011"
version: "1.0.0"
status: "draft"
owner: "Operational Readiness Review Chair"
approvers: ["Product Owner", "Architecture Lead", "Security Lead", "SRE Lead", "Privacy Owner"]
last_updated: "2026-09-22"
---

# Operations readiness checklist

## 1. Usage

Status values: `not_started`, `in_progress`, `passed`, `failed`, `blocked`, `not_applicable`. `passed` requires immutable/reproducible evidence and approver. Narrative intent is not evidence. Production result is `go` only when every blocking item passed or has a valid approved time-bound exception permitted by policy.

## 2. Governance and scope

| ID | Blocking | Check | Evidence |
|---|---:|---|---|
| `ORR-GOV-001` | Yes | Release is single-institution; no tenancy/billing paths | schema/source/IaC scan |
| `ORR-GOV-002` | Yes | HUCE Demo simulation disclosure present in synthetic environments | UI/API snapshots |
| `ORR-GOV-003` | Yes | Referenced requirement/ADR/contracts are approved or release explicitly limited to documentation/synthetic implementation | manifest/review |
| `ORR-GOV-004` | Yes | Open questions relevant to target environment closed; production requires `OQ-001..008` disposition | decision links |
| `ORR-GOV-005` | Yes | Named service, data, security, incident, release and finance owners with backups | roster evidence |

## 3. Build and supply chain

| ID | Blocking | Check | Evidence |
|---|---:|---|---|
| `ORR-BLD-001` | Yes | Toolchain/dependencies/actions/base images pinned; frozen locks | version report |
| `ORR-BLD-002` | Yes | Build once; web/api/worker image digest linked to source | provenance/manifest |
| `ORR-BLD-003` | Yes | SBOM, secret, dependency, SAST and image scans satisfy severity policy | scan artifacts |
| `ORR-BLD-004` | Yes | OpenAPI/events/tools backward compatibility and generated client drift pass | contract reports |
| `ORR-BLD-005` | Yes | Architecture/import boundary and deterministic fake-provider tests pass | commands/results |

## 4. Infrastructure and security

| ID | Blocking | Check | Evidence |
|---|---:|---|---|
| `ORR-INF-001` | Yes | CDK synth deterministic; diff reviewed; no unsafe replacement/delete | templates/diff |
| `ORR-INF-002` | Yes | ECS private/no public IP; RDS/Redis isolated; data SG source-scoped | IaC assertions/scan |
| `ORR-INF-003` | Yes | Encryption, KMS separation, TLS, S3 public block and insecure transport deny | policy tests |
| `ORR-INF-004` | Yes | Per-service task/execution roles least privilege; no unapproved wildcard | IAM tests/simulator |
| `ORR-INF-005` | Yes | Egress allowlist blocks arbitrary URL/metadata/nonapproved provider | negative test |
| `ORR-INF-006` | Yes | Production/nonprod accounts, secrets, keys, stores and identity configs separated | inventory |
| `ORR-INF-007` | Yes | WAF/origin protection/rate/body limits tested; no direct ALB bypass where control claims it | edge tests |
| `ORR-INF-008` | Yes | Drift detection clean or exceptions approved/expiring | drift report |

## 5. Identity, data and privacy

| ID | Blocking | Check | Evidence |
|---|---:|---|---|
| `ORR-DAT-001` | Yes | Synthetic manifest/provenance/reproducibility and no-real-PII scan pass | dataset evidence |
| `ORR-DAT-002` | Yes | Mock auth cannot start in production/real-data mode | config negative tests |
| `ORR-DAT-003` | Prod | Entra issuer/audience/tenant/role mapping, MFA/revocation/CSRF/session tests approved | identity evidence |
| `ORR-DAT-004` | Prod | Privacy/vendor/cross-border/DPIA/retention approvals complete | legal refs |
| `ORR-DAT-005` | Yes | Cross-user/object/field/function authz matrix passes | negative tests |
| `ORR-DAT-006` | Yes | Logging/tracing/model egress DLP/redaction tests pass | exporter capture |
| `ORR-DAT-007` | Prod | Data subject deletion/export and restore tombstone behavior tested | workflow evidence |

## 6. Reliability and recovery

| ID | Blocking | Check | Evidence |
|---|---:|---|---|
| `ORR-REL-001` | Yes | Load model covers `ASM-001..003`, burst/soak/SSE/queue; capacity approved | load report |
| `ORR-REL-002` | Yes | ECS drain/replacement and deployment rollback pass | drill |
| `ORR-REL-003` | Prod | RDS/Redis failover and one-AZ reduced-capacity pass | timestamps/metrics |
| `ORR-REL-004` | Yes | Duplicate/out-of-order/DLQ/outbox crash points pass | integration evidence |
| `ORR-REL-005` | Prod | Isolated full restore meets RPO 15m/RTO 60m | restore drill |
| `ORR-REL-006` | Prod | Regional recovery claim either tested/approved or explicitly not claimed with business acceptance | DR decision |
| `ORR-REL-007` | Yes | Degraded modes DB/Redis/SQS/S3/LLM/audit/integration behave as documented | chaos report |

## 7. AI and tool safety

| ID | Blocking | Check | Evidence |
|---|---:|---|---|
| `ORR-AI-001` | Yes | Affected full eval gates pass for prompt/model/retrieval/tool/provider versions | eval run |
| `ORR-AI-002` | Yes | Citation/evidence gate, abstention and stale/poisoned source tests pass | RAG report |
| `ORR-AI-003` | Yes | Sensitive/injection/no-diacritic/adversarial suites pass | safety report |
| `ORR-AI-004` | Yes | Preview/confirm/expiry/replay/cross-user/idempotency/uncertain outcome pass | tool tests |
| `ORR-AI-005` | Yes | Provider outage enters declared mode; no silent switch/direct DB/tool access | chaos/dependency tests |

## 8. Observability and operations

| ID | Blocking | Check | Evidence |
|---|---:|---|---|
| `ORR-OPS-001` | Yes | Logs/metrics/traces correlate and contain release/config identity without prohibited data | telemetry samples |
| `ORR-OPS-002` | Yes | Every critical alarm transitions and reaches acknowledged destination | alarm drill |
| `ORR-OPS-003` | Yes | Every paging alarm maps to tested runbook and named primary/backup | catalog/drill |
| `ORR-OPS-004` | Yes | Audit append-only sink, access and outage fail-closed tested | IAM/chaos evidence |
| `ORR-OPS-005` | Prod | On-call hours, escalation, student-facing status/communications approved | roster/playbook |
| `ORR-OPS-006` | Yes | Retention lifecycle/backlog/backup jobs monitored | dashboard/alerts |
| `ORR-OPS-007` | Prod | Incident, secret, bad release, queue, provider, restore and security tabletop complete | reports |

## 9. Cost and release

| ID | Blocking | Check | Evidence |
|---|---:|---|---|
| `ORR-COST-001` | AWS | Current-region/provider estimate uses measured units and timestamped prices | calculator/model |
| `ORR-COST-002` | Prod | `OQ-008` closed; budget owner/amount/currency approved | approval |
| `ORR-COST-003` | AWS | 50/75/90/100% budget/forecast/anomaly alerts configured/tested | alarm evidence |
| `ORR-RELSE-001` | Yes | Migration expand/contract, lock duration, backup and rollback/forward-fix plan accepted | migration evidence |
| `ORR-RELSE-002` | Prod | Protected environment approvers and OIDC deploy role tested | CI/IAM evidence |
| `ORR-RELSE-003` | Yes | Post-deploy smoke includes health, authz denial, audit, queue, AI safety and digest/config match | smoke report |

## 10. Exception schema

```yaml
readiness_exception:
  id: "ORR-EXC-..."
  checklist_id: "ORR-..."
  reason: "bounded evidence-based reason"
  environment: "staging"
  risk: "..."
  compensating_controls: []
  owner: "role"
  approved_by: []
  expires_at: "RFC3339"
  production_allowed: false
```

Critical security/privacy, real-data approval, auth bypass, cross-user disclosure, unconfirmed write, destructive replacement and missing restore evidence are not waivable by an implementation agent.

## 11. Decision record

```yaml
operational_readiness_review:
  release_id: "..."
  environment: "staging|production"
  reviewed_at: "RFC3339"
  results: []
  exceptions: []
  blockers: []
  decision: "go|no_go|conditional_nonproduction_only"
  approved_by: []
```

