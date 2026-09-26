---
document_id: "DOC-OPS-004"
version: "1.0.0"
status: "draft"
owner: "Delivery Platform Owner"
approvers: ["Platform Lead", "Security Lead", "QA Lead", "Release Manager"]
last_updated: "2026-09-22"
---

# CI/CD pipeline specification

## 1. Nguyên tắc

- Contract-first, build once, promote immutable artifact.
- CI mặc định hermetic: fake provider, synthetic fixtures, no paid/network call.
- GitHub Actions (hoặc runner tương đương) dùng OIDC short-lived AWS role; không lưu AWS key dài hạn.
- Pull request không có cloud mutation.
- Failed gate không được bypass bằng sửa test/control ngoài task hoặc suppress scanner.
- Production deploy luôn manual approval bởi người không phải tác giả duy nhất của thay đổi security/infra nhạy cảm.

## 2. Pipeline graph

```text
PR Validate
  -> Source/Docs/Contract gates
  -> Web/API/Worker unit + architecture tests
  -> AI sample eval + security negative tests
  -> Container build test + SBOM/scan
  -> CDK synth/assert/scan (no deploy)

Merge main
  -> Re-run required gates
  -> Build immutable images
  -> SBOM + provenance + image signing/attestation
  -> Push ECR by digest
  -> Create release candidate manifest
  -> [approval for paid mutation] deploy staging
  -> migration preflight/task
  -> smoke/integration/eval/load/failure/restore gates
  -> approve release
  -> [manual production approval] promote same digests
  -> post-deploy verification
```

## 3. Stage catalog

| ID | Stage | Required evidence | Failure |
|---|---|---|---|
| `PIPE-001` | Checkout/trust | exact commit, clean generated workspace, action SHAs | stop |
| `PIPE-002` | Version policy | toolchain pins, frozen lockfiles, no floating image/action | stop |
| `PIPE-003` | Documentation/contracts | headers/IDs/links/YAML/JSON/OpenAPI compatibility | stop |
| `PIPE-004` | Static quality | format/lint/typecheck/import boundary | stop |
| `PIPE-005` | Unit/component tests | deterministic tests, coverage policy | stop |
| `PIPE-006` | Security fast gate | secret/SAST/dependency/IaC/container scan; negative auth tests | severity policy |
| `PIPE-007` | AI fast gate | fake-provider graph/tool/RAG/safety sample | stop on regression |
| `PIPE-008` | Build | reproducible `web/api/worker` images, non-root, health contract | stop |
| `PIPE-009` | Supply-chain evidence | SBOM, digest, provenance/attestation, scan result | stop |
| `PIPE-010` | IaC plan | CDK synth, policy assertions, diff classification, cost units | stop unsafe diff |
| `PIPE-011` | Staging deploy | approved role, migration gate, exact digests/config | rollback/hold |
| `PIPE-012` | Staging verification | API/OpenAPI, authz, SSE, queues, full affected eval, telemetry | block promotion |
| `PIPE-013` | Operational verification | load, chaos, failover, restore, runbook/alert drill | mark not verified; block prod |
| `PIPE-014` | Production approval | change record, approvers, OQ/readiness closure, rollback | no deploy |
| `PIPE-015` | Production deploy | maintenance/canary/rolling, alarms, smoke | stop/rollback |
| `PIPE-016` | Post-deploy | digest/config/drift/authz/audit/egress/cost checks | incident/rollback |

## 4. Trigger policy

| Trigger | Allowed stages |
|---|---|
| Pull request | `PIPE-001`–`010`, no cloud writes/push to release repos |
| Main merge | `PIPE-001`–`010`, build/push release candidate |
| Manual staging | `PIPE-011`–`013` after approval if paid mutation |
| Release tag | Create immutable release record; no automatic production deploy |
| Manual production | `PIPE-014`–`016` with protected environment approval |
| Schedule | dependency drift, full AI eval, backup/restore/alert tests as separately approved; no destructive cleanup |

Untrusted fork PR MUST không nhận cloud OIDC role, secret, signing key hoặc write token.

## 5. Release manifest

```yaml
release:
  release_id: "immutable-id"
  source_revision: "git-sha"
  contract_versions:
    openapi: "1.0.0"
    events: "resolved-version"
    tools: "resolved-version"
  images:
    web: "registry/repo@sha256:..."
    api: "registry/repo@sha256:..."
    worker: "registry/repo@sha256:..."
  sbom_refs: []
  provenance_refs: []
  config_version: "immutable-ref"
  cdk_template_hashes: {}
  migration_plan: "none|artifact-ref"
  evidence_refs: []
  exceptions: []
  approved_by: []
```

Manifest MUST không chứa secret/value, real identifiers hoặc mutable tag.

## 6. Migration gate

1. Generate migration SQL/plan and classify `expand`, `migrate`, `contract`, `destructive`.
2. Contract/destructive phase không chạy cùng release nếu old/new code compatibility chưa chứng minh.
3. Verify backup/PITR and restore evidence age.
4. Run migration on restored/staging dataset; record duration/locks/query impact.
5. Production migration needs explicit approval and one-off task role.
6. Deploy backward-compatible app; observe.
7. Contract old schema only in later approved release.

Auto rollback MUST NOT chạy reverse migration phá hủy. Bad schema release dùng forward-fix hoặc compatible app rollback.

## 7. Deployment strategy

- Default ECS rolling deployment with minimum healthy percent keeping capacity and deployment circuit breaker.
- Blue/green MAY be introduced later after cost/ALB/SSE behavior review.
- API stops accepting new SSE on termination and drains within configured grace.
- Worker stops polling, finishes/extends visibility for bounded in-flight messages, then exits.
- Health: liveness only process; readiness verifies required dependencies without exposing topology.
- Smoke uses synthetic canary actor and never privileged real account.

## 8. Rollback criteria

Automatic rollout stop/manual rollback is triggered by:

- no healthy target/readiness regression;
- elevated 5xx/latency beyond `alarms.yaml`;
- authz/cross-user negative smoke failure;
- audit delivery or synthetic-only guard failure;
- queue/outbox rapidly increasing due release;
- AI safety/citation release gate failure;
- image/config digest mismatch.

Rollback target MUST be previous accepted digest/config pair. If migration incompatible, traffic remains held/read-only until forward-fix; pipeline MUST không force previous app onto incompatible schema.

## 9. Security and approvals

- Branch protection: required checks, reviewed changes, signed/verified provenance where platform supports.
- Environments: `staging` and `production` protected; production requires designated Release + Operations/Security approver for relevant change.
- OIDC trust binds repository, protected ref/environment and workflow identity; deploy role session short-lived.
- CI log redacts secrets; commands MUST không dump environment/token/CloudFormation secret dynamic refs.
- Scanner exception includes finding, evidence, compensating control, owner, expiry and independent approval.

## 10. Evidence retention

Retain release manifest, test summaries, SBOM, image/template digests, approval record, deploy events, smoke/rollback result and exception decisions according to approved audit retention. Raw prompt, token, secret and C2/C3 payload MUST không trở thành generic CI artifact.

