---
document_id: "DOC-ADR-015"
version: "1.0.0"
status: "draft"
owner: "Identity Architect"
approvers: ["Architecture Lead", "Security Lead", "Identity Owner", "Privacy Owner"]
last_updated: "2026-09-21"
decision_status: "proposed"
---

# ADR-015 — Internal identity contract; simulated auth tới Microsoft Entra OIDC

## Context

V1 cần synthetic login nhưng tương lai dùng Microsoft identity. Domain không được phụ thuộc mock headers/cookies hoặc Entra-specific claims. Identity/authorization là security-sensitive và production claims/group mapping chưa có (`OQ-004`).

## Decision

Domain nhận immutable internal `Principal` từ trusted authentication middleware. Demo dùng `MockIdentityAdapter` chỉ trong nonproduction. Production target dùng OIDC Authorization Code flow with PKCE qua approved Entra configuration. Claims map vào canonical roles/attributes bằng versioned mapping; API không tin role/student ID do browser gửi.

## Alternatives

- Hard-coded demo header promoted to production: từ chối.
- Application-managed passwords: từ chối target vì tăng credential risk và không tận dụng university IdP.
- ALB-only auth without app claim validation: chưa chọn; app vẫn cần canonical mapping/session/logout/object auth.

## Consequences

Mock và production share authorization behavior; cần token/session validation, key rotation, clock skew, logout/revocation và role mapping tests. MFA policy thuộc IdP/organization và vẫn phải verify.

## Constraints

- Mock adapter **MUST** hard-disable in production config.
- `Principal` có `subject_id`, roles, approved attributes, auth time, claims version; không raw token.
- Token/cookie **MUST NOT** log hoặc gửi LLM.
- Staff role mapping fail closed; unknown role gets minimum access.
- Object authorization remains domain responsibility.
- Auth/security change requires human approval under `DEC-020`.

## Acceptance and failure

Environment guard test, forged-header/token negative tests, role mapping fixture, expiry/key rotation/clock tests và object-level authorization. Production blocked until IdP metadata, claims and owner approved (`OQ-004`). Standards: [OpenID Connect Core](https://openid.net/specs/openid-connect-core-1_0.html), [OAuth 2.0 Security BCP](https://www.rfc-editor.org/rfc/rfc9700.html).

Traceability: `DEC-007`, `DEC-020`, `ARCH-001`, `ARCH-004`, `ARCH-008`.

