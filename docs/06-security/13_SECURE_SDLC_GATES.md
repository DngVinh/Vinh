---
document_id: "DOC-SEC-008"
version: "0.1.0"
status: "draft"
owner: "Engineering Security Lead"
approvers: ["Security Architect", "Engineering Lead", "Release Owner"]
last_updated: "2026-09-21"
---

# Secure SDLC gates

## 1. Nguyên tắc

Security là điều kiện release, không phải backlog hậu kỳ. Gate evidence MUST được tạo tự động khi khả thi, giữ theo release artifact và không chứa secret/PII. Coding agent không được tắt rule, giảm threshold, skip test hoặc sửa requirement để làm gate xanh.

## 2. Gate sequence

### `SEC-SDLC-001` — Design ready

Pass khi:

- requirement có actor, precondition, MUST/MUST NOT, failure behavior và acceptance evidence;
- data class, data flow, authn/authz và retention đã xác định;
- threat-model diff và control mapping hoàn tất;
- API/tool schemas dùng allowlist và `additionalProperties: false` khi phù hợp;
- thay đổi security/privacy đã có reviewer.

Fail: task không được chuyển `ready`.

### `SEC-SDLC-002` — Dependency ready

Pass khi dependency mới:

- thực sự cần, có owner và use case;
- version được pin qua lockfile;
- license, maintenance, vulnerability và transitive risk được review;
- không kéo provider SDK vào domain layer;
- có SBOM update.

Unapproved dependency theo `DEC-020` MUST dừng chờ người phê duyệt.

### `SEC-SDLC-003` — Local/pre-commit verification

Required checks theo changed scope:

```text
format-check
lint
typecheck
unit-test
secret-scan
schema/contract validation
```

Generated/fixture files MUST cũng được secret/PII scan. Agent MUST báo exact command + exit code.

### `SEC-SDLC-004` — Pull-request security

Required:

- code review bởi owner khác người viết cho auth, crypto, policy, data flow;
- SAST, SCA, secret scan, IaC scan, container scan, SBOM;
- negative authorization/security tests;
- changed API/tool/DB/data-flow contract review;
- no Critical/High unresolved vulnerability unless valid exception.

### `SEC-SDLC-005` — AI/RAG security

Required khi thay model, prompt, tool, agent graph, chunking, embedding, reranker, source hoặc safety logic:

- `THR-ABUSE-004..014`, `025`, `026`, `030`, `033`, `035` liên quan;
- no unauthorized tool/side effect;
- citation/source integrity regression;
- PII/secret egress test;
- token/tool/step budget test;
- model/provider version pinned and allowlisted.

### `SEC-SDLC-006` — Staging security

Required:

- synthetic-only dataset assertion;
- DAST/API authorization scan trong authorized scope;
- browser security headers/cookie/CSRF/CORS test;
- TLS/port/egress scan;
- backup/restore smoke test;
- alerts routed and acknowledged;
- no debug/admin endpoint public;
- mock auth only if environment is explicitly synthetic demo.

### `SEC-SDLC-007` — Production go/no-go

Required:

- mọi blocker trong `16_LAUNCH_BLOCKERS.md` closed hoặc valid approved exception;
- independent penetration/security review;
- DPIA/vendor/cross-border/retention/legal approval;
- Entra production auth, MFA and revocation drill;
- incident/restore/degraded-mode drill;
- owner/on-call/runbook and rollback;
- immutable evidence bundle linked to release.

Agent MUST NOT deploy production.

### `SEC-SDLC-008` — Post-release verification

Within approved window:

- verify health, authz denial, audit/alert delivery, model/provider version, egress destination and cost limits;
- compare runtime config/image digest with approved release;
- rollback if critical control is absent or drifted.

## 3. Finding severity and blocking policy

| Severity | Example | Policy |
|---|---|---|
| Critical | auth bypass, cross-user disclosure, unconfirmed write, secret/PII external leak, remote code execution | MUST block; incident response if exposed |
| High | privilege escalation, persistent injection, audit deletion, unbounded paid flow | MUST block production; exception only under `SEC-CTRL-027` |
| Medium | exploitable defense-in-depth gap with bounded impact | Fix before release or approved time-bound exception |
| Low | limited hardening gap | Track with owner/due date |

Scanner severity MUST be triaged, not blindly trusted; downgrade requires evidence and independent reviewer.

## 4. Supply-chain requirements

| ID | Requirement | Evidence | Failure behavior |
|---|---|---|---|
| `SEC-SDLC-009` | Lockfiles and base-image digest MUST be pinned; floating `latest` is prohibited for release. | Build manifest. | Build fails. |
| `SEC-SDLC-010` | CI MUST generate SBOM for application/container and retain with release. | SBOM artifact hash. | Release fails. |
| `SEC-SDLC-011` | Build MUST use least-privilege ephemeral credentials; long-lived cloud secret in CI prohibited. | CI/IAM inventory. | Deployment denied. |
| `SEC-SDLC-012` | Artifact provenance/digest MUST bind reviewed source to deployed image/config. | Signed provenance or equivalent evidence. | Deployment denied. |
| `SEC-SDLC-013` | Critical dependency advisory MUST trigger impact assessment and rebuild even without source change. | Vulnerability response record. | Vulnerable release blocked/rolled back. |

## 5. Agent-specific constraints

| ID | Requirement | Failure behavior |
|---|---|---|
| `SEC-SDLC-014` | Agent MUST only edit assigned files and MUST not alter security test/control/config outside task. | Task `blocked`; emit change request. |
| `SEC-SDLC-015` | Agent MUST not suppress error, add blanket `try/except`, bypass TLS or weaken auth to pass tests. | Review rejects task. |
| `SEC-SDLC-016` | Agent MUST stop for auth/security/crypto architecture changes, new dependency or destructive migration under `DEC-020`. | Structured blocker. |
| `SEC-SDLC-017` | Agent completion MUST include changed files, diff summary, commands/exit codes, acceptance results, deviations and residual risks. | Task not accepted. |
| `SEC-SDLC-018` | Failed security test retry limit is 2 unless task specifies otherwise; agent MUST not expand scope to fix unrelated failures. | Stop and report evidence. |

## 6. Security evidence manifest

```yaml
security_release_evidence:
  release_id: "immutable-release-id"
  source_revision: "git-sha"
  artifact_digests: ["sha256:..."]
  control_ids: ["SEC-CTRL-..."]
  threat_ids: ["THR-..."]
  checks:
    - name: "secret-scan"
      tool_version: "pinned-version"
      result: "passed|failed|exception"
      artifact_ref: "path-or-uri"
  exceptions: []
  approved_by: ["role"]
  generated_at: "RFC3339"
```

## 7. Traceability

- Governance: `DEC-017` đến `DEC-021`.
- Threats: `THR-GOV-*`, `THR-ABUSE-*`.
- Controls: `SEC-CTRL-019`, `SEC-CTRL-023`, `SEC-CTRL-024`.
- Baseline: [OWASP ASVS](https://owasp.org/projects/asvs), [NIST CSF 2.0](https://www.nist.gov/cyberframework).

Nguồn được truy cập ngày `2026-09-21`.
