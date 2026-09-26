---
document_id: "DOC-SEC-004"
version: "0.1.0"
status: "draft"
owner: "Identity Architect"
approvers: ["Security Architect", "Architecture Owner", "University Identity Administrator"]
last_updated: "2026-09-21"
---

# Authentication and Microsoft Entra ID migration

## 1. Target boundary

Domain code MUST chỉ tiêu thụ `IdentityContext`; mock auth và Microsoft Entra ID là hai adapter cùng contract. Identity provider chứng minh authentication; application policy quyết định authorization.

```typescript
type IdentityContext = {
  subjectId: string;          // opaque internal immutable identifier
  externalSubject: string;    // provider sub/oid, never user-editable
  issuer: string;
  tenantId?: string;
  roles: Array<"student" | "support_officer" | "knowledge_admin" | "system_admin">;
  unitIds: string[];
  accountState: "active" | "disabled" | "suspended";
  authTime: string;
  expiresAt: string;
  mfa: boolean;
  sessionId: string;
};
```

Contract thật phải được đặt trong architecture/contracts domain và approved trước implementation. Đoạn trên là behavioral schema, không cấp quyền tự chọn path hay library.

## 2. Phase 0 — deterministic mock auth

Mock auth MUST:

- chỉ hoạt động khi `AUTH_PROVIDER=mock` **và** environment nằm trong explicit allowlist `local|development|test|demo-synthetic`;
- fail startup nếu `ENVIRONMENT=production` hoặc real-data flag được bật;
- chỉ dùng fixture identities version-controlled, `synthetic=true`;
- tạo signed server-side session hoặc test token bằng key riêng của environment; không dùng header `X-User-Id` từ browser làm auth;
- không lưu password, không có password reset và không mô phỏng MFA là thật;
- hiển thị banner “HUCE Demo — dữ liệu mô phỏng, không phải dịch vụ chính thức”.

Publicly reachable demo MUST có access restriction/rate limit và MUST không cho người dùng tự chọn privileged role. Development convenience endpoint MUST compile/route-disabled ngoài local/test.

## 3. Phase 1 — Entra readiness without cutover

Trước cutover:

1. University Identity Administrator cung cấp `tenant_id`, approved issuer, app registrations, redirect URIs và claims/group/app-role mapping (`OQ-004`).
2. Chọn single-tenant registration theo `DEC-001`; `common`, `organizations` và personal Microsoft accounts MUST không được chấp nhận.
3. Đăng ký riêng web/BFF client và protected API nếu kiến trúc yêu cầu.
4. Cấu hình exact redirect URI; wildcard redirect bị cấm.
5. App roles map sang bốn internal roles; raw group names MUST không đi thẳng vào domain policy.
6. Staging dùng test Entra tenant/users không phải hồ sơ sinh viên thật.

## 4. Phase 2 — OIDC Authorization Code + PKCE

Microsoft khuyến nghị Authorization Code Flow kết hợp PKCE/OIDC cho web/SPA và khuyến nghị thư viện được hỗ trợ thay vì tự dựng protocol. Nguồn: [Microsoft identity platform OAuth 2.0 authorization code flow](https://learn.microsoft.com/en-us/entra/identity-platform/v2-oauth2-auth-code-flow).

Target flow:

```text
Browser -> BFF /login -> Entra authorize (state, nonce, PKCE S256)
Entra -> exact BFF callback with code
BFF -> token endpoint with code_verifier and approved client authentication
BFF -> encrypted HttpOnly Secure SameSite session cookie
Browser -> BFF/API; raw refresh token remains server-side
API -> validate access token/session-derived service assertion -> IdentityContext
```

Browser MUST NOT lưu access/refresh token trong `localStorage` hoặc JavaScript-readable cookie. Cookie-authenticated mutations MUST có CSRF defense. Logout MUST terminate local session; revocation/disable behavior MUST được test.

## 5. Token validation rules

API MUST dùng maintained library và tenant-specific OIDC discovery/JWKS. Theo [Microsoft access token validation guidance](https://learn.microsoft.com/en-us/entra/identity-platform/access-tokens) và [claims validation guidance](https://learn.microsoft.com/en-us/entra/identity-platform/claims-validation), validator MUST:

- verify signature với allowed algorithms và current JWKS; handle key rotation;
- exact-match `iss` với approved single-tenant issuer;
- exact-match `tid` với configured Entra tenant;
- exact-match `aud` với Campus API, không nhận token dành cho Microsoft Graph/resource khác;
- validate `exp`, `nbf`, token version và authorized client/actor khi áp dụng;
- validate required scopes/app roles;
- map stable external subject (`oid`/subject contract approved) sang immutable internal `subjectId`;
- reject missing/ambiguous/overage claims thay vì tự cấp role.

ID token MUST NOT được dùng làm bearer authorization cho API. Decode token mà không verify không phải authentication.

## 6. Role provisioning

Microsoft Entra app roles được phát trong `roles` claim khi được cấu hình/assign phù hợp; xem [Microsoft app roles](https://learn.microsoft.com/en-us/entra/identity-platform/howto-add-app-roles-in-apps). Mapping target:

| Entra app role | Internal role | Extra application attribute |
|---|---|---|
| `Campus.Student` | `student` | active student record; own subject mapping |
| `Campus.SupportOfficer` | `support_officer` | approved `unitIds`/queues |
| `Campus.KnowledgeAdmin` | `knowledge_admin` | approved knowledge domains |
| `Campus.SystemAdmin` | `system_admin` | named privileged assignment; no content read |

Role assignment MUST be deny-by-default. Privileged role MUST có owner, approval, expiry/review cycle. Group-to-role mapping MAY được dùng nhưng mapping ID/version MUST được quản lý; display name không phải stable authorization key.

## 7. Normative requirements

| ID | Requirement | Acceptance evidence | Failure behavior |
|---|---|---|---|
| `SEC-AUTHN-001` | Domain MUST không import mock/Entra SDK hoặc parse provider token. | Architecture dependency test. | Build fails. |
| `SEC-AUTHN-002` | Mock auth MUST fail startup in production/real-data mode. | Configuration tests for every environment. | Process exits non-zero. |
| `SEC-AUTHN-003` | User-controlled identity headers MUST bị stripped at edge và ignored by API. | Spoofing integration test. | Request uses validated context only; unauthenticated = `401`. |
| `SEC-AUTHN-004` | Session cookies MUST be `Secure`, `HttpOnly`, appropriate `SameSite`, scoped path/domain, rotated after login/privilege change. | Browser/API header tests. | Login fails if secure cookie policy unavailable. |
| `SEC-AUTHN-005` | Login/callback MUST validate `state`, OIDC `nonce` where applicable, PKCE S256 and exact redirect URI. | Protocol negative tests. | Abort flow and audit. |
| `SEC-AUTHN-006` | Access token validation MUST enforce signature, issuer, tenant, audience, time and required permission claims. | Forged/wrong-aud/wrong-iss/expired test corpus. | `401 INVALID_TOKEN`. |
| `SEC-AUTHN-007` | Staff/admin production access MUST require university-approved MFA/Conditional Access; high-risk operations MUST support recent-auth/step-up evidence. | Entra policy evidence + claim/session tests. | Privileged action denied. |
| `SEC-AUTHN-008` | Disabled/suspended account or removed privileged role MUST lose access within 5 minutes maximum target. | Revocation drill. | Kill session/cache; deny. |
| `SEC-AUTHN-009` | Authentication error MUST không lộ token, claims dump, tenant configuration hoặc user existence. | Error snapshot/DLP test. | Generic error + correlation ID. |
| `SEC-AUTHN-010` | Service-to-service calls MUST use workload identity or short-lived signed assertion; user tokens MUST không được forwarded indiscriminately. | Service identity inventory. | Call denied. |
| `SEC-AUTHN-011` | Break-glass identities MUST separate from normal accounts, phishing-resistant MFA where platform permits, monitored use and quarterly drill. | Access review + drill evidence. | Break-glass marked unavailable; launch blocked if no alternative. |
| `SEC-AUTHN-012` | Cutover MUST have rollback to mock only in synthetic non-production; production rollback MUST be safe maintenance/read-only mode. | Cutover runbook test. | No production mock fallback. |

## 8. Migration acceptance checklist

- [ ] `OQ-004` closed by Identity Administrator.
- [ ] Single-tenant issuer/tenant/audience values approved and stored as non-secret config.
- [ ] Exact redirect/logout URIs inventoried per environment.
- [ ] App roles and unit/queue mapping approved.
- [ ] Staff/admin MFA policy tested.
- [ ] Token-validation negative corpus passes.
- [ ] Session fixation, CSRF, logout and revocation tests pass.
- [ ] Mock auth production hard gate passes.
- [ ] No real PII in Entra staging test fixtures.
- [ ] Security review approves dependency/library versions.

## 9. Agent stop conditions

Implementation agent MUST stop if it needs to choose auth library, claim mapping, Entra tenant, redirect URI, privileged role or session lifetime without an approved contract. Agent MUST NOT create a backdoor header, default admin, wildcard issuer/audience, or production mock toggle to make tests pass.

## 10. Traceability

- Decisions: `DEC-001`, `DEC-006`, `DEC-007`, `DEC-020`.
- Open question: `OQ-004`.
- Authorization: `SEC-AUTHZ-*`.
- Threats: `THR-S-001`, `THR-E-001`, `THR-R-001`.

Nguồn được truy cập ngày `2026-09-21`.
