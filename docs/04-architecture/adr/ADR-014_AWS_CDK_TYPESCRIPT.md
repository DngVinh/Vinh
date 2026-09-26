---
document_id: "DOC-ADR-014"
version: "1.0.0"
status: "draft"
owner: "Platform Architect"
approvers: ["Architecture Lead", "Platform Lead", "Security Lead"]
last_updated: "2026-09-21"
decision_status: "proposed"
---

# ADR-014 — AWS CDK TypeScript cho infrastructure as code

## Context

AWS topology có VPC, ECS, RDS, ElastiCache, S3, SQS, IAM, edge và observability. Infrastructure phải repeatable/reviewable. Solo builder đã dùng TypeScript cho Next.js; thêm HCL/toolchain khác cần lý do.

## Decision

AWS CDK bằng TypeScript **MUST** là IaC tool baseline, synthesize CloudFormation. Infrastructure code nằm ở `infra/cdk/**`, có reusable constructs giới hạn và environment stacks rõ. Không click-ops tạo production resource ngoài break-glass runbook.

## Alternatives

- Terraform/OpenTofu: lựa chọn tốt cho multi-cloud/team standard nhưng chưa có requirement; revisit nếu organization mandates.
- Raw CloudFormation: verbose và khó reuse/type-check.
- Console/manual: từ chối vì drift/audit/recovery.

## Consequences

Một ngôn ngữ TypeScript, AWS-native và synth diff; đổi lại CDK version/bootstrap/assets cần quản lý, generated template lớn và có AWS coupling phù hợp target hiện tại.

## Constraints

- Pin CDK/dependency versions và lockfile.
- `cdk synth`/diff + policy assertions trước deploy.
- No wildcard IAM nếu scope possible; no public data resources.
- Resource removal policy production phải retain/snapshot theo data policy.
- Context lookup không được làm synth nondeterministic; account/region explicit per environment.
- Production deploy, paid resource và destructive replacement cần human approval.

## Acceptance and failure

Fresh account bootstrap/runbook, deterministic synth, security assertions, drift detection, destroy protection và restore-from-IaC evidence. Nếu CDK diff đề xuất replace stateful resource, pipeline **MUST** stop; agent không deploy để “xem có chạy không”.

AWS ECS documentation lists AWS CDK as supported provisioning through CloudFormation ([ECS provisioning](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/)). Traceability: `DEC-009`, `DEC-020`, `ARCH-005`.

