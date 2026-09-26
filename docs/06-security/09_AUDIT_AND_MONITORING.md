---
document_id: "DOC-SEC-006"
version: "0.1.0"
status: "draft"
owner: "Security Operations Owner"
approvers: ["Security Architect", "Privacy/Legal Owner", "Platform Owner"]
last_updated: "2026-09-21"
---

# Audit, security logging and monitoring requirements

## 1. Mục tiêu

Audit phải trả lời được: ai/định danh nào, hành động gì, lên resource nào, policy/version nào, kết quả gì, tại thời điểm nào, từ workload/session nào—mà không tạo bản sao bí mật của token, prompt hoặc dữ liệu cá nhân.

Operational logs, application traces, conversation content và immutable security audit MUST là các luồng logical riêng với quyền và retention riêng.

## 2. Audit event schema

```json
{
  "event_id": "uuid",
  "event_version": "1.0",
  "occurred_at": "RFC3339 UTC",
  "received_at": "RFC3339 UTC",
  "environment": "staging",
  "service": "tool-gateway",
  "event_type": "authorization.decision",
  "severity": "info|warning|high|critical",
  "correlation_id": "uuid",
  "trace_id": "opaque",
  "actor": {
    "subject_ref": "pseudonymous-stable-ref",
    "actor_type": "user|service|system",
    "role_codes": ["student"],
    "session_ref": "pseudonymous-ref"
  },
  "action": "ticket.read",
  "resource": {
    "type": "ticket",
    "resource_ref": "opaque-or-hashed-ref",
    "classification": "CONFIDENTIAL"
  },
  "decision": {
    "outcome": "allow|deny|error",
    "policy_id": "SEC-AUTHZ-003",
    "decision_id": "uuid",
    "reason_code": "OBJECT_SCOPE_MISMATCH"
  },
  "change_ref": null,
  "source": {
    "ip_ref": "privacy-preserving-ref",
    "user_agent_family": "coarse-value"
  },
  "integrity": {
    "previous_hash": "optional-chain-value",
    "event_hash": "sha256:..."
  }
}
```

Fields MUST dùng allowlist. `details` arbitrary object bị cấm trong security audit schema.

## 3. Events bắt buộc

| ID | Event family | Minimum fields | Alert condition |
|---|---|---|---|
| `SEC-AUDIT-001` | Login/logout/callback/session create/revoke | issuer, subject ref, outcome, reason | brute force, issuer/audience mismatch, privileged login anomaly |
| `SEC-AUDIT-002` | Authorization allow/deny for C2/C3/admin | actor, action, resource ref, policy/decision | repeated cross-object denies, policy error |
| `SEC-AUDIT-003` | Role/grant/queue/unit assignment change | before/after codes, approver/change ref | privileged grant, self-approval |
| `SEC-AUDIT-004` | Action preview/confirm/tool execute | payload hash, confirmation ref, idempotency ref, result | replay, cross-user mismatch, execution without confirmation |
| `SEC-AUDIT-005` | Knowledge ingest/review/publish/retire | source checksum, version, reviewers | publish without dual review, PII/injection quarantine |
| `SEC-AUDIT-006` | Model invocation | provider/model/prompt version, token counts, policy outcome | blocked PII, tool-loop/token budget breach |
| `SEC-AUDIT-007` | Data export/deletion/correction/legal hold | privacy case, stores/results, approvers | bulk export, overdue deletion, hold misuse |
| `SEC-AUDIT-008` | Secret/key access/rotation/policy/deletion attempt | principal, key/secret ref, action, outcome | decrypt anomaly, key deletion, broad access |
| `SEC-AUDIT-009` | Admin/config/feature flag/deployment | change ref, actor, before/after hash | direct production change, security control disabled |
| `SEC-AUDIT-010` | Break-glass | actor, reason, scope, expiry, approver | every use immediate alert |
| `SEC-AUDIT-011` | Audit access/export | reader, query scope, case/change ref | broad/unscheduled access |
| `SEC-AUDIT-012` | Incident lifecycle | severity, owner, status, evidence refs | missed acknowledgement/escalation |

## 4. Prohibited log content

MUST NOT log:

- access/refresh/ID token, session cookie, CSRF token, API key, password, client secret;
- full `Authorization`, `Cookie`, `Set-Cookie` headers;
- raw C2/C3 prompt, response, ticket, transcript, attachment;
- full schedule, student ID/email/phone/address or sensitive disclosure;
- KMS encryption context containing PII/secret;
- unvalidated control characters or user-provided event type/key.

Debug mode MUST không nới quy tắc này. Sensitive troubleshooting phải dùng case-specific evidence vault, explicit scope, short access và C3 retention.

## 5. Integrity, access and time

| ID | Requirement | Acceptance evidence | Failure behavior |
|---|---|---|---|
| `SEC-AUDIT-013` | Audit archive MUST append-only/immutable for configured retention; application roles MUST not update/delete. | IAM/policy tests; attempted mutation denied. | High-risk features fail closed. |
| `SEC-AUDIT-014` | Events MUST be UTC, clock-synchronized and preserve occurred/received time. | Clock skew alert test. | Mark unreliable time; alert. |
| `SEC-AUDIT-015` | Event IDs MUST be unique; ingestion MUST be idempotent and detect gaps/duplicates. | Replay/gap tests. | Quarantine duplicate/conflict; alert gap. |
| `SEC-AUDIT-016` | Security log access MUST be role/purpose constrained, MFA-protected and itself audited. | Access matrix tests. | Deny. |
| `SEC-AUDIT-017` | Redaction MUST occur before data leaves process/trust boundary, not only in dashboard. | Exporter capture tests. | Drop event/field; alert control failure. |
| `SEC-AUDIT-018` | Alert routing MUST have owner, severity, acknowledgement target and tested destination. | Alert drill with timestamps. | Launch blocked for critical alert gaps. |
| `SEC-AUDIT-019` | Correlation ID MUST propagate across BFF/API/agent/tool without carrying identity or secrets. | End-to-end trace test. | Generate new safe ID and record broken-chain metric. |
| `SEC-AUDIT-020` | Audit outage behavior MUST follow `SEC-ARCH-011`: privileged/write/C2-C3 paths deny; bounded public read MAY continue. | Chaos test. | Enter documented degraded mode. |
| `SEC-AUDIT-021` | Detection rules MUST be version-controlled and unit-tested on synthetic events. | Rule test fixtures and pass report. | Rule release blocked. |
| `SEC-AUDIT-022` | Audit retention MUST map to `PRIV-RET-008`; operational logs MUST not inherit longer retention silently. | Lifecycle configuration inventory. | Config drift alert/release failure. |

## 6. Minimum detection use cases

1. ≥5 denied object-scope attempts by one subject in 5 minutes.
2. Privileged role grant followed by export/config change within 30 minutes.
3. Confirmation replay or payload hash mismatch.
4. Knowledge publication without independent reviewer.
5. Prompt/attachment blocked for secrets/PII/injection above threshold.
6. Tool calls exceed per-request loop/action budget.
7. LLM egress attempts to unapproved provider/destination.
8. Mock auth startup outside synthetic environment.
9. Audit/KMS/Secrets Manager policy change or deletion attempt.
10. Break-glass use.
11. Retention/deletion backlog exceeds approved threshold.
12. Model/provider version changed without release record.

## 7. Acceptance evidence bundle

Security logging implementation is not accepted without:

- schema validation report;
- forbidden-field/DLP tests;
- append-only IAM negative test;
- event coverage inventory;
- alert rule fixture results;
- audit outage chaos test;
- sample event set containing only synthetic values;
- proof that dashboard viewer cannot modify source evidence.

## 8. Traceability

- Decisions: `DEC-003`, `DEC-014`, `DEC-015`, `DEC-020`.
- Retention: `PRIV-RET-008`, `PRIV-RET-012`.
- Threats: `THR-R-001`, `THR-T-004`, `THR-I-003`.
- Baseline: [NIST SP 800-61 Rev. 3](https://csrc.nist.gov/pubs/sp/800/61/r3/final), [NIST CSF 2.0](https://www.nist.gov/cyberframework).

Nguồn được truy cập ngày `2026-09-21`.
