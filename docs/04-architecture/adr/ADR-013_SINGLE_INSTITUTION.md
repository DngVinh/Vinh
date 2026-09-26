---
document_id: "DOC-ADR-013"
version: "1.0.0"
status: "draft"
owner: "Product Architect"
approvers: ["Product Owner", "Architecture Lead", "Security Lead"]
last_updated: "2026-09-21"
decision_status: "proposed"
---

# ADR-013 — Single institution; không multi-tenancy V1

## Context

Sản phẩm có định hướng thương mại nhưng V1 chỉ phục vụ một trường. Xây SaaS multi-tenant sớm kéo theo tenant identity, data isolation, billing, quotas, onboarding, support và compliance chưa có requirement.

## Decision

V1 **MUST** là single-institution deployment. Branding/config là deployment-level config. Không tenant table, `tenant_id` everywhere, tenant middleware, tenant billing, shared-tenant runtime hoặc cross-tenant admin.

Bounded contexts và ports vẫn sạch để tương lai đánh giá multi-tenancy, nhưng “extensible” không cho phép code speculative.

## Alternatives

- Shared-schema multi-tenant từ đầu: từ chối vì isolation/security complexity và không có khách hàng thứ hai.
- Database-per-tenant abstraction từ đầu: từ chối vì provisioning/migration overhead.
- Dedicated deployment per institution về sau: option cần đánh giá khi có khách hàng thật.

## Consequences

Implementation nhỏ, threat model rõ, ship nhanh; migration sang SaaS có thể tốn kém. Đây là trade-off có chủ đích. Không được marketing “multi-tenant ready”.

## Constraints

- Demo label là `HUCE Demo`, unofficial simulation.
- Institution-specific text/config không hard-code sâu trong domain; đặt configuration/content layer hợp lý.
- Không generalize khi chưa có second-institution requirements.
- Future change **MUST** có business case, tenancy ADR, isolation threat model, migration và tests.

## Acceptance and failure

Schema/source scan không có accidental tenancy/billing feature; UI có simulation disclosure. Nếu task yêu cầu tenant onboarding/quota/billing, agent **MUST** block vì ngoài `DEC-001`/`DEC-005`.

Traceability: `DEC-001`, `DEC-002`, `DEC-005`, `ARCH-001`, `ARCH-004`.

