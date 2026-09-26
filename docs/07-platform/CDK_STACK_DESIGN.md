---
document_id: "DOC-OPS-003"
version: "1.0.0"
status: "draft"
owner: "Infrastructure as Code Owner"
approvers: ["Principal Cloud Architect", "Security Lead", "SRE Lead"]
last_updated: "2026-09-22"
---

# AWS CDK TypeScript stack design

## 1. Contract

Infrastructure code MUST nằm trong `infra/cdk/**`, dùng AWS CDK TypeScript và synthesize CloudFormation. Tài liệu này không tạo mã CDK; nó định nghĩa module, dependencies, input/output, policy và gate cho task sau.

IaC MUST:

- deterministic khi cùng source, lockfile, context và environment spec;
- không lookup account/VPC tùy ý trong synth;
- không đọc secret value ở synth;
- không tạo paid resource hoặc deploy production không approval;
- không xóa/replace stateful resource chỉ để diff sạch;
- ánh xạ một-một logical resource ID với `infra/specs/stack-manifest.yaml`.

## 2. Project layout target

```text
infra/cdk/
  bin/campus247.ts
  lib/config/
    environment-schema.ts
    load-environment.ts
  lib/constructs/
    secure-bucket.ts
    encrypted-queue.ts
    ecs-service.ts
    observability.ts
  lib/stacks/
    foundation-stack.ts
    network-stack.ts
    security-stack.ts
    data-stack.ts
    messaging-stack.ts
    compute-stack.ts
    edge-stack.ts
    observability-stack.ts
    backup-stack.ts
  test/
    assertions/
    snapshots/
  cdk.json
  package.json
  pnpm-lock.yaml
```

Construct chỉ đóng gói policy lặp lại; không che resource quan trọng sau generic map không test được. Stack API nhận typed config đã validate, không đọc `process.env` rải rác.

## 3. Stack DAG

```text
FoundationStack (tags, optional imported DNS/bootstrap refs)
  ├─ SecurityStack (KMS, secret definitions, audit policy)
  └─ NetworkStack (VPC, subnets, endpoints, security groups)
       ├─ DataStack (RDS, Redis, S3)
       ├─ MessagingStack (SQS/DLQ)
       └─ ComputeStack (ECS, ECR refs, task/service/autoscaling)
            └─ EdgeStack (ALB, CloudFront, WAF, DNS/cert refs)

ObservabilityStack consumes identifiers from all stacks.
BackupStack consumes stateful-resource ARNs and KMS refs.
```

CloudFormation export/import cross-stack SHOULD được giữ tối thiểu. Prefer explicit construct references trong một CDK app. Không tạo circular dependency bằng alarm/action hoặc bucket log destination; tách policy/resource theo documented pattern.

## 4. Stack responsibilities

| Stack | Creates | Must not create |
|---|---|---|
| `FoundationStack` | global tags/aspects, imported hosted-zone/cert refs, release metadata | VPC/data/application secret values |
| `SecurityStack` | KMS keys/aliases, Secrets Manager containers, IAM permission boundaries, audit archive policy | Application business roles/policy decisions |
| `NetworkStack` | VPC/subnets/NAT/endpoints/SG/flow logs | ECS task, RDS schema |
| `DataStack` | RDS/subnet group/parameter group, Redis, data buckets | DB migration, corpus publish |
| `MessagingStack` | queues, DLQs, KMS/resource/redrive policy | Business outbox table/consumer code |
| `ComputeStack` | ECS cluster/services/task defs/autoscaling/ECR policies/migration task definition | Route/domain schema/migration execution by default |
| `EdgeStack` | ALB/listeners/targets, CloudFront, WAF association, DNS records | Authz business logic |
| `ObservabilityStack` | log groups, alarms, dashboards, alert topics/destinations | Raw personal log content |
| `BackupStack` | vault/plan/selection/restore test role | Legal retention decision |

## 5. Configuration schema

CDK entrypoint accepts exactly:

```typescript
type EnvironmentConfig = {
  project: "campus247";
  environment: "development" | "staging" | "production";
  account: string;
  region: string;
  dataMode: "synthetic_only" | "approved_real_data";
  availabilityZones: number;
  network: { natGateways: number; interfaceEndpoints: string[] };
  compute: Record<"web" | "api" | "worker", {
    desired: number; min: number; max: number; cpu: number; memoryMiB: number;
  }>;
  database: { engineVersion: string; instanceClass: string; multiAz: boolean };
  cache: { engineVersion: string; nodeType: string; replicas: number; multiAz: boolean };
  budgetMonthlyUsd: number | null;
  approvals: Record<string, string | null>;
};
```

Actual implementation MAY adjust type syntax but semantics MUST match `environments.yaml`. Unknown key, missing required value hoặc production unsafe override MUST fail before synth.

## 6. Version pinning strategy

| Item | Rule | Evidence |
|---|---|---|
| Node.js | Exact supported major/minor/patch in toolchain file; CI verifies | release manifest |
| Package manager | Exact `packageManager` + Corepack; frozen lock | lockfile hash |
| `aws-cdk-lib`, `constructs` | Exact versions, no caret/tilde for release | dependency report |
| CDK CLI | Same compatible version as library, invoked from project | synth metadata |
| GitHub Actions | Pin immutable commit SHA; record upstream tag as comment | workflow policy test |
| Base images | Pin image digest, not `latest` or mutable major tag | SBOM/provenance |
| RDS engine/pgvector | Exact approved engine version; extension compatibility check | pre-deploy check |
| Redis/Valkey | Approved engine family/version from environment config | runtime inventory |
| CDK bootstrap | Approved qualifier, template version and trusted accounts | bootstrap evidence |

Version values chưa được kiến trúc phê duyệt MUST là `null`/`PIN_REQUIRED` trong spec và block staging/prod, không được agent chọn theo “latest”. Dependency update là task riêng, có changelog/security/compatibility/test evidence.

## 7. Aspects and policy assertions

Synth MUST fail với:

- S3 public access hoặc thiếu deny-insecure-transport;
- ECS task `assignPublicIp=ENABLED`;
- public RDS/Redis hoặc data SG inbound broad CIDR;
- unencrypted RDS/cache/queue/bucket/log where classification requires;
- production stateful resource thiếu deletion protection hoặc retain/snapshot policy;
- IAM wildcard không có allowlisted exception ID;
- secret plaintext/dynamic value xuất hiện trong template/output;
- container image mutable tag;
- log group không có retention/KMS policy;
- queue không có DLQ/redrive policy;
- resource thiếu required tags;
- production desired count <2 cho web/api;
- production mock auth hoặc `synthetic_only=false` khi approval refs trống.

Policy tools MAY gồm CDK assertions và cdk-nag/security scanner, nhưng suppressions MUST có ID, reason, owner, expiry và review. Suppression rộng theo stack bị cấm.

## 8. Stateful resource lifecycle

| Resource | Nonprod default | Production default |
|---|---|---|
| RDS | Snapshot/retain khi stack change; disposable only with explicit test ID | deletion protection + retain/snapshot |
| S3 data/audit | Retain; lifecycle policy controls objects | Retain; object/version lifecycle reviewed |
| KMS | Retain; no automatic key deletion | Retain; deletion separate human protocol |
| Secrets | Retain or explicitly rotate; never output value | Retain; rotation/revoke runbook |
| SQS | Retain while messages/evidence unresolved | Retain/recreate only through migration runbook |
| Log groups | Retain according to retention policy | Retain/lifecycle; audit separate |

`cdk destroy` không phải operational workflow. Cleanup ephemeral resources phải liệt kê exact stack/resources, xác nhận synthetic/disposable và tuân thủ destructive authorization policy.

## 9. Deployment wave

1. Validate YAML/schema and required approvals.
2. Typecheck/unit test constructs.
3. Synth with explicit account/region; scan template.
4. Diff against deployed stack; classify create/update/replace/delete/IAM change.
5. Stop on replacement/delete stateful, broad IAM/network, KMS/key, secret or budget-impacting change.
6. Deploy network/security/data/messaging.
7. Run connectivity/preflight; migration plan and backup check.
8. Run gated migration task.
9. Deploy worker, API, web; then edge.
10. Deploy alarms/dashboards/backup; run smoke/security/telemetry checks.
11. Record stack IDs, template hash, image digests, config version and evidence.

## 10. Tests

- Snapshot only for reviewed stable subsets; assertions remain primary.
- Per-resource positive + prohibited-pattern negative tests.
- Environment matrix tests for local/nonprod/prod guards.
- IAM exact-action/resource assertion and permission simulator tests.
- `cdk synth` twice with same input MUST produce semantically identical template.
- Diff parser MUST classify CloudFormation replacement (`UpdateReplacePolicy`, `DeletionPolicy`) and stop unsafe change.
- Restore/recreate test MUST prove CDK source can reconstruct stateless topology without console state.

