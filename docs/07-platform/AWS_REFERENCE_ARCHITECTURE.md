---
document_id: "DOC-OPS-002"
version: "1.0.0"
status: "draft"
owner: "Principal Cloud Architect"
approvers: ["Architecture Lead", "Security Lead", "SRE Lead", "Data Owner"]
last_updated: "2026-09-22"
---

# AWS reference architecture

## 1. Phạm vi

Reference topology triển khai tại `ap-southeast-1`, single-region, ít nhất hai Availability Zones cho production. Nó hiện chỉ được phép dùng dữ liệu tổng hợp. Multi-region, EKS, NATless tuyệt đối, microservice và multi-tenancy không thuộc V1.

## 2. Request và event path

```text
Route 53 -> CloudFront -> WAF -> ALB
                            |-> ECS web (Next.js)
                            |-> ECS api (FastAPI + LangGraph request-time)

ECS api -> RDS PostgreSQL + pgvector
        -> ElastiCache Redis
        -> S3 private buckets
        -> transactional outbox in RDS
        -> DeepSeek through LLM Gateway + controlled NAT egress

Outbox relay -> SQS Standard queues -> ECS worker
ECS worker   -> RDS / S3 / approved adapters
All runtimes -> ADOT/OpenTelemetry -> CloudWatch/X-Ray
Security audit -> append-only log stream/archive outside application write authority
```

## 3. Exact resource inventory

Các logical IDs chuẩn nằm trong `infra/specs/stack-manifest.yaml`.

### Edge

- One Route 53 public hosted zone reference; zone MAY be pre-existing/imported.
- One ACM certificate in `us-east-1` for CloudFront và certificate regional cho ALB khi TLS end-to-end được chọn.
- One CloudFront distribution: static immutable cache; dynamic/authenticated/SSE behaviors `CachingDisabled`.
- One regional WAFv2 web ACL: AWS managed baseline, body-size, rate rules, explicit exception expiry.
- One internet-facing ALB across public subnets; HTTPS only; HTTP redirect; target groups `web` và `api`.
- Route `/api/*`, `/health/*`, `/v1/*` và SSE path tới API; other routes tới web. Route cuối phải khớp OpenAPI và web contract trước implementation.

### Network

- One VPC/environment, DNS enabled, two AZ minimum.
- Public subnets: ALB và NAT Gateway only.
- Private application subnets: ECS tasks, no public IP.
- Isolated data subnets: RDS/ElastiCache; no default Internet route.
- NAT: staging cost profile MAY dùng one NAT có documented AZ risk; production baseline one per AZ.
- Gateway endpoint: S3.
- Interface endpoints evaluated/defined for ECR API/DKR, CloudWatch Logs, Secrets Manager, SQS, KMS and STS. Enable when reliability/security/cost formula passes; endpoint policy MUST be scoped.
- Security groups reference source SG, không broad data-port CIDR.

### Compute and registry

- One ECS cluster/environment with Container Insights enhanced only when cost approved.
- ECR repositories: `web`, `api`, `worker`; immutable tags, scan-on-push, lifecycle policy preserving accepted rollback digests.
- ECS services: `web`, `api`, `worker`; deployment circuit breaker and rollback enabled.
- Production desired count: `web=2`, `api=2`, `worker=2` baseline; min/max and pool budget are config, validated by load test.
- One-off task definitions: `migration`, `administrative-job`; no public listener. Admin job requires explicit allowlist/approval.
- Separate task role per service and separate execution role. No shared wildcard application role.

### Data

- RDS PostgreSQL Multi-AZ production instance/cluster choice finalized by benchmark/cost review; encrypted, private, deletion protection, automated backup/PITR.
- pgvector extension version compatibility checked before migration; engine/parameter group pinned.
- RDS Proxy is `later/evidence-driven`, không baseline; add only if connection tests justify.
- ElastiCache for Redis/Valkey replication group production, encryption in transit/at rest, Multi-AZ automatic failover; cache data disposable.
- S3 buckets separated by policy/blast radius: `knowledge`, `artifacts`, `audit`, `access-logs`. All block public access, encrypt, version as required, deny insecure transport. `audit` has object-lock design only after retention/legal review and bucket created correctly from inception.

### Messaging

- SQS Standard queues `domain-jobs`, `knowledge-ingestion`, `notifications`, each with dedicated DLQ.
- KMS encryption; resource policy only allows named producer/consumer roles.
- Visibility timeout derives from measured p99 processing plus margin; worker extends visibility for bounded long jobs.
- Redrive disabled by default for operator action; runbook validates schema, idempotency and incident status first.
- Transactional outbox remains in PostgreSQL; SQS is transport, không audit store.

### Security/configuration

- KMS customer-managed keys per environment/purpose: `app-data`, `secrets`, `audit`, `backup`; production/nonprod never share keys.
- Secrets Manager named secrets only; app roles get `GetSecretValue` for exact ARN/version stage required.
- CloudTrail organization/account trail target; AWS Config/GuardDuty/Security Hub are production baseline when account governance is available, staged as `later` for synthetic MVP if budget blocks, with explicit readiness exception.
- AWS Backup vault with access policy, lock only after recovery/legal review; backup jobs for stateful resources.

### Observability

- CloudWatch log group per service/audit class, KMS encryption where required, explicit retention.
- CloudWatch metrics/alarms/dashboards from `alarms.yaml` and `dashboards.yaml`.
- ADOT collector sidecar or library export over private path; X-Ray tracing optional by environment but trace schema/redaction mandatory.
- Route 53/CloudWatch Synthetics external health canary is production/later depending budget; staging smoke provides equivalent evidence.

## 4. Network access matrix

| Source | Destination | Port/protocol | Rule |
|---|---|---|---|
| Internet | CloudFront | 443 | Public; WAF attached |
| CloudFront/origin protection | ALB | 443 | Secret/custom origin header or managed prefix strategy; test bypass denial |
| ALB SG | web/api SG | container port | Exact target SG only |
| api/worker SG | RDS SG | PostgreSQL TLS | Exact task SGs; distinct DB roles |
| api/worker SG | Redis SG | TLS | Exact task SGs |
| tasks | AWS endpoints | 443 | Endpoint policies/named services |
| api/worker | DeepSeek endpoint | 443 | LLM gateway only, destination control, timeout/circuit |
| worker | Internet | 443 | Deny arbitrary URL; adapter allowlist only |
| Internet | RDS/Redis/tasks | any | MUST be impossible |

CloudFront-to-ALB origin restriction MUST có test. ALB DNS không được coi là secret; nếu direct origin cannot be reliably blocked, record residual risk và use AWS-supported origin control pattern.

## 5. Least-privilege ownership

| Principal | Allowed | Explicitly denied/not granted |
|---|---|---|
| `webTaskRole` | Log/metric emit; call internal API if architecture requires signed service path | DB, Redis, S3 private content, SQS, DeepSeek secret |
| `apiTaskRole` | Named knowledge object read/write prefixes, named queues send, exact secrets, telemetry | Queue consume, bucket list-all, IAM/KMS admin |
| `workerTaskRole` | Named queues receive/delete/change visibility; named S3 prefixes; exact secrets | Public ingress, IAM admin, unrelated queues/buckets |
| `migrationTaskRole` | Schema migration secret and DB network path for bounded job | Runtime queue/provider access |
| `ciBuildRole` | ECR push, artifact write, synth metadata | CloudFormation deploy production |
| `nonProdDeployRole` | CloudFormation/CDK actions bounded by stack/tag/permission boundary | Production account |
| `prodReleaseRole` | Approved stack update and ECS deploy | KMS key admin, audit deletion, interactive app data read |
| application DB roles | Per-runtime schema/table privileges | Superuser, ownership of audit archive |

IAM implementation MUST include policy assertions and simulator/negative tests. Wildcard is allowed only for AWS actions that technically require it, documented by `iam_exception_id`, condition-scoped và Security approval.

## 6. Availability and scaling

- ALB/CloudFront managed multi-AZ; ECS spreads across AZs.
- RDS Multi-AZ; application handles connection reset with bounded jittered reconnect.
- Redis Multi-AZ production; outage degrades cache/rate-limit according to security policy, never becomes truth.
- API/web target tracking uses CPU/memory/request metrics after load evidence. Worker scales on queue age/backlog per task.
- Maximum task count is constrained by DB connection formula, provider quota and budget; not only CPU.
- SSE uses connection draining, heartbeat below tested idle timeout, no-store and exactly one terminal event.

## 7. Failure behavior

| Failure | Automatic | Operator |
|---|---|---|
| ECS task unhealthy | ECS replacement/circuit breaker | Investigate crash loop and release |
| One AZ impaired | Remaining targets + managed data failover | Freeze change, verify capacity |
| RDS failover | Bounded reconnect; writes remain idempotent | Validate data/outbox/backlog |
| Redis outage | Safe cache bypass; sensitive rate guard may fail closed | Restore/replace cache, verify no truth loss |
| SQS unavailable | Outbox retains committed events | Monitor outbox age; no dual-write workaround |
| Queue poison | DLQ after bounded receives | Quarantine/repair/redrive with idempotency evidence |
| DeepSeek outage | Circuit open, `DEGRADED_NO_LLM` | Approved recovery/degrade; no silent provider switch |
| Audit sink outage | High-risk writes/admin/C2-C3 fail closed | Restore audit path or hold service read-only |
| Bad release | Deployment circuit/alarms stop rollout | Roll back image/config; schema forward-fix |
| Regional outage | No automatic cross-region failover | Invoke DR plan; target remains unverified until cross-location backup approved |

## 8. Acceptance evidence

- CDK assertions: no public tasks/data store; no broad data port; encrypted buckets/queues/data; deletion protection production.
- Deterministic `cdk synth`, reviewed diff, no stateful replacement.
- IAM policy tests for each service and denied cross-service action.
- Two-AZ task placement/failure, RDS/Redis failover, queue duplicate/DLQ and SSE drain tests.
- Egress test blocks metadata/internal/user URL and non-allowlisted provider.
- Restore drill with measured RPO/RTO and checksum/smoke.
- Cost model and budget alarms configured from approved budget; no fabricated price.
- Runtime inventory matches image digest, config version and release manifest.

## 9. Source of truth

Resource IDs, stage, owner and properties: `infra/specs/stack-manifest.yaml`. Environment variance: `infra/specs/environments.yaml`. Implementation MUST stop if a required property is `null` at its `required_before` gate.

