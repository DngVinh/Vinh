---
document_id: "DOC-ADR-012"
version: "1.0.0"
status: "draft"
owner: "Reliability Architect"
approvers: ["Architecture Lead", "Operations Lead", "Security Lead", "Finance Owner"]
last_updated: "2026-09-21"
decision_status: "proposed"
---

# ADR-012 — Single-region Multi-AZ và backup/restore DR

## Context

Target availability là 99.9%, RPO 15 phút, RTO 60 phút theo assumption. Multi-region active-active tăng cost, data-transfer/privacy và consistency complexity, chưa có production data residency/budget approval.

## Decision

V1 production architecture là một approved AWS Region, Multi-AZ cho edge/app/RDS/Redis. Disaster recovery cho region-level failure dựa trên versioned IaC, immutable images/artifacts, cross-location backup strategy đã được legal approve và tested restore. Không automatic cross-region write failover trong V1.

`ap-southeast-1` chỉ là simulated reference; region production chưa được hợp thức hóa cho real data.

## Alternatives

- Active-active multi-region: từ chối hiện tại do cost/consistency/operations.
- Single-AZ: chỉ nonprod cost optimization; không production.
- Warm standby: future nếu business impact/RTO yêu cầu và privacy cho phép.

## Consequences

AZ failures có managed recovery path; region outage cần runbook và có thể không đạt RTO nếu restore chưa đủ nhanh. Vì vậy RPO/RTO là hypothesis đến khi drill pass.

## Constraints

- Production app tasks trải ≥2 AZ.
- RDS Multi-AZ; ElastiCache Multi-AZ nếu critical.
- Backup encryption/retention/deletion protection.
- Restore không được ghi đè production; drill trong isolated environment.
- No cross-border replication trước privacy/legal approval.

AWS RDS Multi-AZ provides standby/failover behavior, nhưng application vẫn phải reconnect và test ([RDS Multi-AZ](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/Concepts.MultiAZSingleStandby.html)).

## Acceptance and failure

AZ failure test, RDS/cache failover, complete restore, DNS/config/secrets recovery và end-to-end checksum smoke phải có timestamp. Nếu measured RTO/RPO không đạt, status là `not_verified` và production gate fail; không được ghi “architecturally compliant” thay bằng test.

Traceability: `ASM-006`, `DEC-010`, `OQ-005`, `OQ-008`, `ARCH-005`, `ARCH-007`.

