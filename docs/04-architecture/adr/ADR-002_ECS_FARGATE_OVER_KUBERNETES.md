---
document_id: "DOC-ADR-002"
version: "1.0.0"
status: "draft"
owner: "Platform Architect"
approvers: ["Architecture Lead", "Operations Lead", "Finance Owner", "Security Lead"]
last_updated: "2026-09-21"
decision_status: "proposed"
---

# ADR-002 — Amazon ECS on Fargate thay Kubernetes cho V1

## Context

`DEC-009` chọn AWS và container-first. Workload gồm ba service, không có yêu cầu custom scheduler/operator/service mesh. Nhóm hiện tại là một người, nên control-plane và cluster operations phải tối thiểu nhưng production vẫn cần health replacement, autoscaling, private networking và rolling deployment.

## Decision

Production baseline **MUST** dùng Amazon ECS services trên Fargate. Kubernetes/EKS **MUST NOT** là dependency V1. Local development dùng Docker Compose; image contract giống production.

AWS mô tả ECS là managed container orchestration và Fargate là serverless compute không yêu cầu quản lý host; ECS Service Auto Scaling hỗ trợ scale service từ CloudWatch/SQS signals ([ECS](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/), [Auto Scaling](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/service-auto-scaling.html)).

## Alternatives

- EKS: từ chối vì chưa có use case cần Kubernetes API/operator và thêm patching/add-on/RBAC/networking burden.
- ECS on EC2: để tương lai nếu sustained load/cost hoặc specialized hardware chứng minh lợi ích.
- Single VPS Compose: chỉ cho demo/local; không đáp ứng production Multi-AZ/managed recovery baseline.

## Consequences

Ít vận hành host và phù hợp scale nhỏ; đổi lại phụ thuộc AWS task/service model, cần xử lý Fargate limits và có thể tốn hơn EC2 ở sustained high utilization.

## Implementation constraints

- ECS tasks private, không public IP.
- Task role per service; image pin digest.
- Autoscaling có max bound theo DB/provider/budget.
- Graceful shutdown cho SSE và SQS visibility.
- Agent **MUST NOT** thêm Helm chart/Kubernetes manifests.

## Revisit triggers

Chỉ xem lại khi có ít nhất một: yêu cầu platform doanh nghiệp bắt buộc Kubernetes; workload cần capability ECS không đáp ứng; ≥10 services độc lập với team ownership; cost benchmark xác nhận; multi-cloud requirement được chấp nhận.

Acceptance: staging service replacement, scale test, AZ test, cost estimate và runbook pass. Nếu chưa có budget owner (`OQ-008`), production provisioning bị block.

Traceability: `DEC-009`, `ARCH-005`, `ARCH-007`.

