---
document_id: "DOC-SEC-003"
version: "0.1.0"
status: "draft"
owner: "Security Architect"
approvers: ["Product Owner", "Data Owner", "Operations Owner"]
last_updated: "2026-09-21"
---

# Authorization matrix

## 1. Authorization model

V1 MUST dùng `RBAC + ABAC + object-level policy`:

- RBAC giới hạn tập hành động theo bốn role của `DEC-006`.
- ABAC giới hạn `unit_id`, queue assignment, resource status, ownership, data class, environment và purpose.
- Object-level check chạy với mỗi object ID; chỉ kiểm tra role là không đủ.
- Database RLS MAY là defense-in-depth nhưng MUST NOT thay service policy.
- Deny-by-default; thiếu attribute hoặc policy error = deny.

Role codes:

```text
student
support_officer
knowledge_admin
system_admin
```

`system_admin` quản trị kỹ thuật, không mặc định có quyền đọc transcript/ticket nội dung. `knowledge_admin` không có quyền xem lịch cá nhân. `support_officer` không publish policy. Không có super-admin chung cho application và evidence/audit vault.

## 2. Resource/action matrix

Legend: `A` allowed, `C` conditional, `D` denied.

| Resource/action | student | support_officer | knowledge_admin | system_admin | Điều kiện bắt buộc |
|---|---:|---:|---:|---:|---|
| Public FAQ/search | A | A | A | A | Published/effective corpus only |
| Read own profile/schedule | A | C | D | D | Subject from server identity; officer only approved case purpose |
| Read another student's profile/schedule | D | C | D | D | Assigned case + approved purpose + field minimization + audit |
| Create own ticket/request | C | C | D | D | Preview + confirmation + idempotency |
| Read own ticket | A | C | D | D | Owner or assigned queue |
| Read arbitrary ticket | D | C | D | D | Unit/queue scope; no global default |
| Update ticket status | D | C | D | D | Assigned officer; valid state transition |
| Close ticket | C | C | D | D | Student acknowledgment or officer policy; reason required |
| Create room-booking request | C | C | D | D | Eligibility, conflict check, confirmation |
| Approve room booking | D | C | D | D | Explicit approver entitlement; separation from requester |
| Upload knowledge source | D | D | C | D | Approved source type; quarantine first |
| Publish/retire knowledge version | D | D | C | D | Dual review; cannot approve own material change |
| View knowledge ingestion diagnostics | D | C | A | C | Officer only case-related; admin metadata only |
| Manage app configuration | D | D | D | C | Named entitlement + MFA + audit + change record |
| Change auth/security policy | D | D | D | D via normal UI | Human-approved change/deployment only (`DEC-020`) |
| View aggregate operations metrics | D | C | C | A | Minimum cohort threshold; no raw PII |
| View raw conversation | Own only | C | D | D | Assigned case + purpose; sensitive fields restricted |
| Export personal data | Own only | D | D | C processor only | Verified request + privacy case approval |
| Delete personal data | Request only | D | D | C processor only | `PRIV-RET-*`, legal hold and approval |
| Read audit events | D | D | D | C | Dedicated `security_auditor` entitlement is preferred; no modify/delete |
| Emergency break-glass | D | C | D | C | Named account, step-up MFA, reason, time-bound grant, alert/review |

## 3. Internal policy input/output

Implementation MUST use a server-created context:

```json
{
  "actor": {
    "subject_id": "opaque-internal-id",
    "issuer": "mock|entra-tenant-specific-issuer",
    "roles": ["student"],
    "unit_ids": ["FIT"],
    "account_state": "active",
    "auth_time": "RFC3339",
    "mfa": false
  },
  "request": {
    "action": "ticket.read",
    "resource_type": "ticket",
    "resource_id": "opaque-id",
    "purpose": "student_support",
    "correlation_id": "uuid"
  },
  "resource": {
    "owner_subject_id": "opaque-internal-id",
    "assigned_unit_id": "FIT-STUDENT-SUPPORT",
    "classification": "CONFIDENTIAL",
    "state": "OPEN"
  },
  "environment": "staging"
}
```

Policy output MUST be explicit:

```json
{
  "decision": "allow|deny",
  "policy_id": "SEC-AUTHZ-...",
  "reason_code": "stable_machine_code",
  "obligations": ["redact:field", "require_confirmation", "audit:high"],
  "decision_id": "uuid"
}
```

Agent MUST NOT invent optional fallback such as “allow when policy service times out”.

## 4. Normative requirements

| ID | Requirement | Acceptance evidence | Failure behavior |
|---|---|---|---|
| `SEC-AUTHZ-001` | Every route/tool MUST declare `action` and invoke policy before data access. | Route inventory has 100% policy mapping. | Build/test fails for unmapped route. |
| `SEC-AUTHZ-002` | Actor MUST come only from validated server identity context. User/model fields such as `user_id`, `role`, `student_id` MUST not override it. | Parameter-tampering tests. | `403 AUTHORIZATION_DENIED`. |
| `SEC-AUTHZ-003` | Every object lookup by ID MUST check owner/queue/unit/purpose before return or mutation. | BOLA test suite per endpoint. | Return `404` where resource existence must be concealed; otherwise `403`. |
| `SEC-AUTHZ-004` | List/search MUST apply authorization predicate before pagination/count; post-filtering is prohibited. | Test proves total/count does not reveal unauthorized rows. | Query denied if predicate unavailable. |
| `SEC-AUTHZ-005` | Field-level allowlist MUST remove data not needed by actor/action. | Snapshot/contract tests per role. | Omit field; never return then hide client-side. |
| `SEC-AUTHZ-006` | All writes MUST require valid state transition plus `SEC-ARCH-006` confirmation when user-initiated. | State-machine and replay tests. | Transaction rollback. |
| `SEC-AUTHZ-007` | Privileged grants MUST have owner, reason, start/end and approver; permanent ad-hoc grants are prohibited. | Access-review export. | Grant creation rejected. |
| `SEC-AUTHZ-008` | Break-glass access MUST be time-bound, step-up authenticated, alerted in real time and reviewed within one business day. | Drill evidence. | Access denied if any prerequisite unavailable. |
| `SEC-AUTHZ-009` | Service accounts MUST use workload identity and resource-scoped permissions; no shared interactive credentials. | IAM/database-role inventory. | Deployment gate fails. |
| `SEC-AUTHZ-010` | Authorization cache, if any, MUST bind actor, action, resource version and policy version with TTL ≤60 seconds; deny decisions MAY be cached. | Cache key/expiry tests. | Bypass cache and reevaluate; never reuse ambiguous allow. |
| `SEC-AUTHZ-011` | Role/attribute changes MUST invalidate sessions or take effect within documented maximum 5 minutes. | Revocation integration test. | Disable affected privileged operations. |
| `SEC-AUTHZ-012` | Authorization decision and obligations MUST be audited without logging raw token or full resource. | Audit schema test. | High-risk action denied when audit unavailable. |
| `SEC-AUTHZ-013` | Knowledge publish, privileged config, export và deletion MUST enforce separation of duties. | Two-actor negative/positive tests. | Action remains pending. |
| `SEC-AUTHZ-014` | System admin MUST NOT gain content access solely from technical administrator role. | Negative tests for transcripts/tickets/schedules. | Deny. |

## 5. Required test matrix

Mỗi protected API/tool MUST có tối thiểu:

1. unauthenticated;
2. wrong role;
3. correct role, wrong owner/unit/queue;
4. correct role and scope;
5. resource does not exist;
6. identifier tampering;
7. hidden field/mass assignment;
8. revoked/disabled actor;
9. stale policy/role cache;
10. policy dependency unavailable.

Evidence MUST ghi endpoint/tool, fixture actor, resource, expected status/reason code và actual result. Coverage percentage không thay thế case matrix.

## 6. Traceability

- Decisions: `DEC-006`, `DEC-007`, `DEC-014`, `DEC-015`, `DEC-020`.
- Threats: `THR-E-001`, `THR-I-001`, `THR-S-001`, `THR-LLM-006`.
- Controls: `SEC-CTRL-002`, `SEC-CTRL-003`, `SEC-CTRL-007`, `SEC-CTRL-008`.
- Baseline: [OWASP API1:2023 BOLA](https://api-security.owasp.org/editions/2023/en/0xa1-broken-object-level-authorization/), [OWASP API5:2023 BFLA](https://api-security.owasp.org/editions/2023/en/0xa5-broken-function-level-authorization/).

Nguồn được truy cập ngày `2026-09-21`.
