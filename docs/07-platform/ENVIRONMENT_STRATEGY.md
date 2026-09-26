---
document_id: "DOC-OPS-001"
version: "1.0.0"
status: "draft"
owner: "Platform Lead"
approvers: ["Architecture Lead", "Security Lead", "Privacy Owner", "Finance Owner"]
last_updated: "2026-09-22"
---

# Environment strategy

## 1. Môi trường chuẩn

| Environment | Hạ tầng | Dữ liệu | Auth | LLM | HA | Mục đích |
|---|---|---|---|---|---|---|
| `local` | Docker Compose trên máy phát triển | Synthetic fixture nhỏ | Mock signed session | Fake | Không | Code/test nhanh, không AWS |
| `development` | Local mặc định; AWS ephemeral chỉ khi được duyệt | Synthetic | Mock | Fake; DeepSeek disabled | Không | Integration và preview branch |
| `staging` | Non-production AWS account, VPC riêng | Synthetic production-scale | Mock; Entra test adapter future | Fake mặc định; DeepSeek opt-in | Production-like có thể cost-sized | Contract/eval/load/restore/release rehearsal |
| `production` | AWS account riêng | Bị khóa tới approval | Entra target | Approved provider only | Multi-AZ | Dịch vụ thật; hiện `blocked` |

`demo` không phải environment độc lập. Demo dùng build của `staging` hoặc local profile `demo-synthetic`, vẫn có banner `HUCE Demo — dữ liệu mô phỏng, không phải dịch vụ chính thức`.

## 2. Promotion, không copy state

```text
source revision + lockfiles
  -> build/test once
  -> immutable image digests + SBOM + provenance
  -> deploy development (optional)
  -> deploy staging + full gates
  -> approve release manifest
  -> promote exact digests/config version to production
```

- MUST NOT rebuild artifact khi promote.
- MUST NOT copy database, Redis, bucket object, secret hoặc identity fixture giữa environments.
- Schema migration được chạy riêng bằng one-off ECS task với image digest cùng release.
- Config không bí mật được version hóa; secret chỉ copy bằng rotation/provisioning workflow, không export plaintext.

## 3. Account và network isolation

| Boundary | Baseline |
|---|---|
| Non-production | Một account có thể chứa `development` và `staging`, nhưng mỗi môi trường có VPC, KMS keys, database, cache, queues, buckets, secrets, log groups và CDK stacks riêng. |
| Production | Account riêng, AWS IAM Identity Center/federated short-lived access, SCP/guardrails khi organization có sẵn. |
| Security evidence | Audit bucket/vault tách quyền khỏi application roles; production SHOULD dùng logging/security account khi organization được phê duyệt. |
| Region | `ap-southeast-1` chỉ là tham chiếu synthetic. Production Region và transfer phải được Privacy/Legal phê duyệt. |

Không dùng peering/transit route giữa nonprod và production trong MVP. Nếu sau này cần, phải có data-flow review và egress rule rõ.

## 4. Data guard

Mỗi environment MUST có startup/deploy assertions:

```yaml
data_guard:
  environment: "staging"
  data_mode: "synthetic_only"
  real_personal_data_allowed: false
  synthetic_manifest_required: true
  simulation_banner_required: true
  external_llm_direct_identifier_allowed: false
```

Process MUST fail startup nếu:

- `AUTH_PROVIDER=mock` trong production;
- `DATA_MODE` khác `synthetic_only` khi real-data approval chưa tồn tại;
- synthetic dataset thiếu manifest/provenance;
- provider external bật nhưng egress/privacy policy không được duyệt;
- config chứa environment/account/region không khớp release manifest.

## 5. Environment lifecycle

### Local

- Không cần cloud credential.
- Dịch vụ phụ thuộc dùng container/fake adapter; secret là placeholder không dùng được bên ngoài.
- Volumes có thể reset chỉ bằng task test được xác định disposable; không có quyền xóa dữ liệu người dùng ngoài workspace.

### Development

- Branch/PR environment AWS là **opt-in**, TTL bắt buộc, owner/tag bắt buộc và cần approval chi phí.
- Không tạo RDS/ElastiCache riêng cho mỗi PR trong baseline; ưu tiên local hermetic test.
- Nếu tạo ephemeral stack, deletion chỉ qua approved cleanup workflow, target được liệt kê và không chứa state ngoài synthetic fixture.

### Staging

- Cấu trúc tương đương production ở boundary và service type; kích thước có thể nhỏ hơn.
- Multi-AZ của RDS/cache có thể bật cho failover/restore drill; mọi khác biệt production phải có `parity_exception` với owner và expiry.
- Chỉ staging được dùng cho performance, resilience, security integration và release rehearsal.

### Production

- Provision/deploy luôn manual approval; destructive CDK replacement bị chặn.
- Không có mock auth, debug endpoint, role picker, fake admin hoặc synthetic shortcut.
- Trước real-data launch phải đóng open question, retention, Entra, legal transfer, vendor, support và incident contacts.

## 6. Naming và tagging

Logical name:

```text
campus247-<environment>-<component>[-<purpose>]
```

Không nhúng account ID, secret, student identifier hoặc tenant ID vào tên. Required tags:

| Tag | Ví dụ/luật |
|---|---|
| `Project` | `campus247` |
| `Environment` | `development|staging|production` |
| `ManagedBy` | `aws-cdk` |
| `Owner` | stable role, không email cá nhân |
| `CostCenter` | `UNRESOLVED` tới Finance approval; production gate |
| `DataClassification` | `PUBLIC|INTERNAL|CONFIDENTIAL|RESTRICTED` |
| `DataMode` | `synthetic_only|approved_real_data` |
| `Criticality` | `low|medium|high|critical` |
| `BackupPolicy` | policy ID hoặc `none-approved` |
| `Release` | immutable release ID cho compute/config |

## 7. Drift và access

- CDK/CloudFormation là authority; manual changes tạo drift incident.
- Drift detection chạy sau deploy và theo lịch; drift security/stateful resource block promotion.
- Developer không có long-lived AWS access key. CI dùng OIDC short-lived role; human dùng federated role + MFA.
- Permission set tách `ReadOnly`, `DeveloperNonProd`, `PlatformDeployNonProd`, `ProductionRelease`, `SecurityAudit`, `BreakGlass`.
- Production break-glass time-bound, reason/approver/alert bắt buộc; không dùng làm vận hành thường ngày.

## 8. Promotion gates

| Gate | Dev | Staging | Production |
|---|---|---|---|
| Lock/version/deterministic build | Required | Required | Same accepted artifact |
| Synthetic data guard | Required | Required | Required cho tới real-data approval |
| Unit/contract/security fast suite | Required | Required | Evidence reused + smoke |
| CDK synth/diff/policy | Khi có AWS | Required | Required + manual review |
| AI regression sample/full | Sample | Full affected suites | Accepted staging evidence |
| Load/failure/restore | Optional | Required trước release | Latest valid evidence |
| Cost estimate/budget | AWS only | Required | Finance approval |
| Human deploy approval | Paid mutation | Infra/cost/security change | Always |

## 9. Machine source

`infra/specs/environments.yaml` là cấu hình môi trường chuẩn. CDK implementation MUST validate file đó, không tự suy diễn production defaults. Unknown environment MUST fail closed.

