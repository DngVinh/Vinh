---
document_id: "DOC-OPS-000"
version: "1.0.0"
status: "draft"
owner: "Platform and SRE Lead"
approvers: ["Architecture Lead", "Security Lead", "Application Lead", "Finance Owner"]
last_updated: "2026-09-22"
---

# Campus 24/7 — Platform & Operations package

## 1. Mục đích

Gói này là đặc tả triển khai và vận hành cho Campus 24/7 V1. Phạm vi là **một trường duy nhất**, nhãn `HUCE Demo`, dữ liệu tổng hợp, ba runtime `web`, `api`, `worker`, AWS Region tham chiếu `ap-southeast-1`. Tài liệu không cấp quyền tạo tài nguyên trả phí, đưa dữ liệu thật lên AWS hoặc deploy production.

Các tài liệu hiện ở trạng thái `draft` vì `OQ-001`–`OQ-008`, ngân sách, identity, pháp lý dữ liệu và nhiều ADR còn chưa được phê duyệt. Chúng đủ chi tiết để triển khai synthetic/local và chuẩn bị IaC; task triển khai chỉ được dùng artifact đã chuyển `approved` theo `DOCUMENT_CONTROL.md`.

## 2. Invariant bắt buộc

| ID | Quy tắc |
|---|---|
| `OPS-BASE-001` | V1 MUST là single-institution; không `tenant_id`, tenant router, billing hoặc shared-tenant runtime. |
| `OPS-BASE-002` | `local`, `development`, `staging` và mọi demo MUST chỉ dùng dữ liệu tổng hợp, có nhãn mô phỏng không chính thức. |
| `OPS-BASE-003` | Production reference MUST dùng ECS Fargate trong private subnets; task không có public IP. |
| `OPS-BASE-004` | PostgreSQL/pgvector là source of truth; Redis là ephemeral; SQS là at-least-once; object bền nằm ở S3. |
| `OPS-BASE-005` | Mọi image production MUST pin bằng digest; dependency/action/base image MUST không dùng floating tag. |
| `OPS-BASE-006` | Mọi cloud mutation MUST qua CDK TypeScript, review `synth/diff`, policy gate và approval phù hợp. Click-ops chỉ cho break-glass có audit. |
| `OPS-BASE-007` | Browser, Next.js và LLM MUST không nhận AWS/database/provider secret. Workload dùng task role và named secret reference. |
| `OPS-BASE-008` | Log/metric/trace MUST redact trước khi rời process; label/dimension MUST không chứa prompt, token, student ID hoặc payload. |
| `OPS-BASE-009` | RPO 15 phút/RTO 60 phút là design target chưa được chứng minh cho tới khi restore drill đạt. |
| `OPS-BASE-010` | Production deploy, paid resource, real secret, destructive replacement và security/auth change MUST dừng chờ human approval theo `DEC-020`. |
| `OPS-BASE-011` | Real personal data và external LLM production MUST bị khóa tới khi privacy/legal/vendor approval hoàn tất. |
| `OPS-BASE-012` | Rollback application MUST dùng artifact cũ bất biến; stateful migration MUST dùng expand/contract hoặc forward-fix, không destructive reset. |

## 3. Thứ tự đọc

1. `docs/00-governance/**` và `docs/04-architecture/**`.
2. `ENVIRONMENT_STRATEGY.md` và `AWS_REFERENCE_ARCHITECTURE.md`.
3. `CDK_STACK_DESIGN.md`, `CONFIGURATION_AND_SECRETS.md`, `CI_CD_PIPELINE.md`.
4. `OBSERVABILITY.md`, `SLO_SLI_ERROR_BUDGETS.md`, `RUNBOOKS.md`.
5. `BACKUP_RESTORE_DR.md`, `CAPACITY_AND_COST_MODEL.md`.
6. `OPERATIONS_READINESS_CHECKLIST.md`.
7. `infra/specs/*.yaml` là phần máy đọc tương ứng.

## 4. Artifact map

| Artifact | Quyền sở hữu | Nguồn máy đọc |
|---|---|---|
| `ENVIRONMENT_STRATEGY.md` | Platform Lead | `infra/specs/environments.yaml` |
| `AWS_REFERENCE_ARCHITECTURE.md` | Cloud Architect | `infra/specs/stack-manifest.yaml` |
| `CDK_STACK_DESIGN.md` | IaC Owner | `stack-manifest.yaml` |
| `CI_CD_PIPELINE.md` | Delivery Platform Owner | stage/gate tables trong tài liệu |
| `CONFIGURATION_AND_SECRETS.md` | Platform + Security | environment/secret sections trong manifests |
| `OBSERVABILITY.md` | SRE + Security Operations | `dashboards.yaml`, `alarms.yaml` |
| `SLO_SLI_ERROR_BUDGETS.md` | Service Owner + SRE | SLO/alert IDs |
| `RUNBOOKS.md` | Incident/Operations Owner | `runbooks.yaml` |
| `BACKUP_RESTORE_DR.md` | Data/Operations Owner | resource backup policy trong stack manifest |
| `CAPACITY_AND_COST_MODEL.md` | Platform + Finance | capacity profiles/formulas |
| `OPERATIONS_READINESS_CHECKLIST.md` | Release Manager | checklist IDs/evidence |

Markdown giải thích intent và quy trình; YAML là input máy đọc. Nếu hai dạng xung đột, deployment MUST dừng với `PLATFORM_SPEC_CONFLICT`; không tự chọn một bản.

## 5. Ownership model

| Role | Accountable cho | Không được tự làm |
|---|---|---|
| Platform Lead | Network, ECS, CDK, delivery runtime | Duyệt security exception của chính mình |
| SRE/Operations | SLO, alert, incident, capacity, restore drill | Thay đổi product correctness/eval threshold |
| Security Lead | IAM, KMS, audit, egress, control gates | Đọc content C2/C3 chỉ vì là system admin |
| Data Owner | RDS, backup, retention mapping, restore validation | Phê duyệt cross-border/legal basis |
| Application Lead | Image, migration, health, telemetry instrumentation | Sửa cloud control ngoài task scope |
| AI Quality Lead | LLM/RAG quality, provider degradation, eval gate | Dùng SRE availability để thay quality gate |
| Finance Owner | Budget và cost variance | Hạ security/HA để pass ngân sách không có ADR |
| Release Manager | Promotion, evidence, rollback decision | Bỏ qua failed gate |

## 6. MVP và future

### MVP synthetic

- Local Compose; deterministic fake provider mặc định.
- Một non-production AWS account cho staging synthetic, tách VPC/secret/data theo environment.
- ECS Fargate, RDS PostgreSQL/pgvector, ElastiCache Redis, S3, SQS/DLQ, CloudWatch, WAF/ALB/CloudFront.
- CDK synth/diff, least privilege assertions, image/SBOM/secret/dependency scans.
- Restore, failover, queue, provider và bad-release drills bằng dữ liệu tổng hợp.

### Production baseline sau approval

- AWS production account riêng; Multi-AZ cho app/RDS/cache.
- Immutable audit archive ngoài quyền sửa của application role.
- Microsoft Entra OIDC adapter, workload identity và production secrets.
- Approved DeepSeek terms/data flow hoặc provider khác qua cùng gateway.
- On-call, legal/privacy/vendor approvals, tested RTO/RPO và budget.

### Future, không thuộc V1

- Multi-region active-active, EKS, microservices, multi-tenancy/SaaS, dedicated vector database, automatic provider switching và real institutional integrations.

## 7. Traceability

Upstream: `DEC-001`–`DEC-021`, `ASM-001`–`ASM-010`, `OQ-001`–`OQ-008`, `ADR-001`–`ADR-016`, `ARCH-004`–`ARCH-009`, `SEC-ARCH-*`, `SEC-CRYPTO-*`, `SEC-AUDIT-*`, `SEC-SDLC-*`, `PRIV-RET-*`.

Contract: `contracts/openapi/v1/openapi.yaml`, đặc biệt `API-SYS-001`, `API-SYS-002`, `API-CONV-004`, `API-ACTION-*`, `API-OPS-001`.

