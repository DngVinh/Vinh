---
document_id: "DOC-SEC-005"
version: "0.1.0"
status: "draft"
owner: "Security Architect"
approvers: ["Platform Owner", "Privacy/Legal Owner"]
last_updated: "2026-09-21"
---

# Cryptography, key and secrets policy

## 1. Policy

Agent MUST use platform/library primitives; MUST NOT invent cryptographic algorithms, write custom JWT verification, hard-code keys hoặc “encrypt” bằng encoding/hash. Key administration và key usage MUST tách quyền.

## 2. Approved minimums

| Use | Required baseline |
|---|---|
| External/internal HTTP | TLS 1.2 minimum; TLS 1.3 preferred; certificate validation required |
| Persistent AWS data | Service encryption at rest with customer-managed KMS key where classification/access isolation requires it |
| Application field encryption | Authenticated encryption such as AES-256-GCM through reviewed library/envelope encryption; only when threat model requires |
| Integrity/hash | SHA-256 or stronger for non-password integrity; HMAC-SHA-256 with managed key for keyed integrity |
| Password hashing | No application passwords in target Entra design; if later approved, Argon2id/baseline must be specified by separate ADR |
| Random tokens | CSPRNG; minimum 128 bits entropy for opaque confirmation/reset/session identifiers |
| Token signing | Maintained OIDC/JWT library and approved asymmetric algorithm/provider metadata; no `none`/algorithm confusion |
| Backups/log archive | Encryption with dedicated environment/classification key and tested restore permissions |

[AWS Well-Architected](https://docs.aws.amazon.com/wellarchitected/latest/security-pillar/sec_protect_data_transit_encrypt.html) yêu cầu bảo vệ data in transit bằng secure TLS và nêu AWS API yêu cầu ít nhất TLS 1.2. [AWS KMS documentation](https://docs.aws.amazon.com/kms/latest/developerguide/kms-cryptography.html) mô tả envelope encryption; điều này là baseline kỹ thuật, không phải chứng nhận tuân thủ.

## 3. Key hierarchy và separation

```text
AWS KMS customer-managed keys (per environment)
  key/app-data-{env}       -> database/object data
  key/audit-{env}          -> immutable audit archive
  key/backup-{env}         -> backup vault
  key/secrets-{env}        -> Secrets Manager
```

- Production keys MUST không được dùng ở development/staging.
- KMS key administrator MUST không mặc định có decrypt permission; workload decrypt permission MUST không có key-admin action.
- Key policy MUST không dùng wildcard principal/action khi có thể scope cụ thể.
- KMS encryption context MUST không chứa PII/secret vì context có thể xuất hiện plaintext trong CloudTrail. AWS xác nhận encryption context không bí mật trong [KMS access guidance](https://docs.aws.amazon.com/prescriptive-guidance/latest/aws-kms-best-practices/access.html).
- Key deletion MUST require human approval, waiting period, backup/impact review và real-time alert.

## 4. Secret inventory và lifecycle

Secrets gồm DeepSeek API key, database credential, OIDC confidential-client credential/certificate, webhook secret, signing/HMAC key và any break-glass credential.

Mỗi secret MUST có record:

```yaml
secret_record:
  id: "SEC-SECRET-..."
  owner: "role"
  environments: ["staging"]
  consumers: ["workload identity"]
  storage: "AWS Secrets Manager"
  rotation_method: "automatic|manual-runbook"
  rotation_interval_days: 90
  last_rotated_at: "RFC3339"
  expires_at: "RFC3339|null"
  revocation_runbook: "path"
  classification: "RESTRICTED"
```

Rotation interval là risk-based maximum, không mặc định áp dụng nếu provider không hỗ trợ. Compromise suspicion MUST trigger immediate revoke/rotate, không chờ schedule. AWS khuyến nghị least privilege và rotation trong [Secrets Manager best practices](https://docs.aws.amazon.com/secretsmanager/latest/userguide/best-practices.html).

## 5. Normative requirements

| ID | Requirement | Acceptance evidence | Failure behavior |
|---|---|---|---|
| `SEC-CRYPTO-001` | HTTP plaintext và TLS <1.2 MUST bị chặn ở production boundary. | TLS scanner report. | Deployment fails. |
| `SEC-CRYPTO-002` | Certificate hostname/chain/expiry validation MUST không bị disabled, kể cả development integration code. | Negative TLS tests. | Connection fails closed. |
| `SEC-CRYPTO-003` | C1–C3 persistent stores/backups MUST bật encryption at rest; C2/C3 key access MUST được audit. | IaC assertion + CloudTrail sample. | Resource creation blocked. |
| `SEC-CRYPTO-004` | C3 application field encryption MUST use reviewed AEAD/envelope design; ciphertext MUST bind record/purpose context as AAD where approved. | Test vector + tamper test. | Decryption fails; incident alert if unexpected. |
| `SEC-CRYPTO-005` | Secret MUST only reside in approved secret store or local ignored test fixture; repository, image, logs và frontend bundle are prohibited. | Secret scan, image scan, bundle scan. | Build/release fails; exposed secret revoked. |
| `SEC-CRYPTO-006` | Workload MUST retrieve only named secrets through workload identity; broad list/read access is prohibited. | IAM policy simulator tests. | Startup/call fails. |
| `SEC-CRYPTO-007` | Logs/errors MUST redact secret/token/cookie/authorization headers before serialization/export. | Seeded DLP tests. | Drop sensitive field/event; alert repeated leak. |
| `SEC-CRYPTO-008` | Secret version rotation MUST support overlap/rollback without embedding two active values in code. | Staging rotation drill. | Keep previous secret only for bounded rollback; no deployment workaround. |
| `SEC-CRYPTO-009` | Crypto/key policy changes MUST be separate reviewed tasks under `DEC-020`. | Approved change record and targeted tests. | Agent blocks task. |
| `SEC-CRYPTO-010` | Confirmation token MUST be single-purpose, actor/action/payload/expiry-bound, tamper-evident and single-use. | Tamper, replay, cross-user, expiry tests. | No side effect; deny/audit. |
| `SEC-CRYPTO-011` | Raw access/refresh token MUST không được persisted in application database or analytics. | Schema/log scan. | Release gate fails. |
| `SEC-CRYPTO-012` | Key/secret backup, recovery and revocation MUST be exercised before production. | Drill output with RTO and evidence. | Production blocked. |

## 6. Local/test behavior

- Test keys MUST be clearly named, non-production and generated/replaced safely; examples MUST use obvious placeholders.
- Automated tests MUST use fake provider; paid DeepSeek credential MUST not be required for unit/integration test.
- `.env.example` MAY list variable names, MUST NOT contain usable values.
- Agent output MUST never print environment variables, secret file content or decoded tokens.

## 7. Traceability

- Decisions: `DEC-008`, `DEC-009`, `DEC-020`.
- Data classes: `SEC-DATA-*`.
- Threats: `THR-I-003`, `THR-R-002`, `THR-S-002`, `THR-T-002`.
- Controls: `SEC-CTRL-009`, `SEC-CTRL-010`, `SEC-CTRL-011`.

Nguồn được truy cập ngày `2026-09-21`.
