---
document_id: "DOC-OPS-005"
version: "1.0.0"
status: "draft"
owner: "Platform Configuration Owner"
approvers: ["Security Lead", "Application Lead", "AI Platform Lead"]
last_updated: "2026-09-22"
---

# Configuration and secrets

## 1. Phân loại

| Class | Ví dụ | Store |
|---|---|---|
| Build-time public | asset build ID, UI feature compiled safely | source/release manifest |
| Runtime non-secret | environment, region, timeout, route flag, model alias | versioned config artifact/SSM parameter if chosen |
| Sensitive reference | secret ARN/name, KMS key ARN, DB endpoint | deployment config; do not expose browser |
| Secret value | DB credential, DeepSeek API key, signing/HMAC key, OIDC client secret | AWS Secrets Manager only; local ignored fake fixture |
| Business policy | queue routing, retention, feature kill switch | versioned approved policy store, audit changes |

Feature flag không được dùng để che secret hoặc bypass authorization. Security/synthetic guard flags fail closed và không client-editable.

## 2. Configuration precedence

```text
compiled safe defaults
  < versioned environment configuration
  < deployment-time non-secret overrides (allowlist only)
  < emergency operational override (time-bound, audited, approved)
```

Secret values không tham gia precedence này; application nhận secret qua named reference/resolver. Unknown key và ambiguous duplicate source MUST fail startup.

## 3. Required runtime keys

| Key | Service | Secret | Rule |
|---|---|---:|---|
| `APP_ENVIRONMENT` | all | no | enum, must match release/environment |
| `APP_RELEASE_ID` | all | no | immutable trace dimension |
| `DATA_MODE` | all | no | `synthetic_only` until approved |
| `INSTITUTION_LABEL` | web/api | no | `HUCE Demo`; deployment-level, not tenant |
| `SIMULATION_NOTICE_ENABLED` | web/api | no | MUST true in synthetic mode |
| `AUTH_PROVIDER` | web/api | no | mock nonprod; Entra target prod |
| `IDENTITY_CONFIG_VERSION` | api | no | mapping version, no raw token |
| `DATABASE_SECRET_REF` | api/worker/migration | reference | exact Secrets Manager ARN/name |
| `REDIS_ENDPOINT_REF` | api/worker | reference | TLS endpoint, no password in plain config |
| `OBJECT_BUCKET_*` | api/worker | no/reference | exact bucket/prefix allowlist |
| `QUEUE_URL_*` | api/worker | no/reference | exact named queue URL/ARN |
| `LLM_PROVIDER` | api/worker | no | `fake` default; `deepseek` gated |
| `LLM_MODEL_ALIAS` | api/worker | no | alias maps in provider adapter config; no domain hard-code |
| `LLM_API_KEY_SECRET_REF` | api/worker | reference | DeepSeek key secret; only gateway consumer |
| `LLM_DATA_POLICY` | api/worker | no | default `NO_DIRECT_IDENTIFIERS` |
| `OTEL_EXPORTER_ENDPOINT` | all | no | private collector endpoint |
| `LOG_LEVEL` | all | no | cannot disable redaction; production allowlist |
| `CAPABILITY_STATE` | api | no | normal/degraded/read-only/search-only/maintenance |
| `CONFIG_VERSION` | all | no | immutable config artifact checksum/version |

No configuration key MAY contain `TENANT_ID` for product tenancy. `ENTRA_TENANT_ID` is an identity-provider setting only and MUST not leak into domain tenancy.

## 4. Secret inventory

| Secret ID | Consumers | Rotation | Failure behavior |
|---|---|---|---|
| `SEC-SECRET-DB-RUNTIME` | api/worker | managed/manual approved | readiness false; no fallback credential |
| `SEC-SECRET-DB-MIGRATION` | migration task only | per release/risk | migration stops |
| `SEC-SECRET-DEEPSEEK` | LLM gateway in api/worker | provider-supported/manual | `DEGRADED_NO_LLM` |
| `SEC-SECRET-CONFIRM-HMAC` | api | overlap rotation | writes requiring confirmation stop |
| `SEC-SECRET-CURSOR-HMAC` | api | overlap rotation | cursor operations fail safely |
| `SEC-SECRET-SESSION` | web/BFF | overlap rotation | login/session unavailable; no insecure fallback |
| `SEC-SECRET-OIDC-CLIENT` | web/BFF future | Entra policy | production login unavailable |
| `SEC-SECRET-ALERT-DEST` | observability integration | owner policy | page delivery alarm; no logging value |

Actual secret names/ARNs are environment outputs, not committed values. Every secret has owner, consumers, class `RESTRICTED`, rotation method, revocation runbook and last-rotation evidence.

## 5. Retrieval patterns

- Prefer ECS secret injection only when restart-on-rotation is accepted; deployment MUST force new tasks after rotation.
- For overlap/live rotation, use bounded Secrets Manager resolver with cache TTL, version-stage allowlist and telemetry, never list all secrets.
- Secret MUST not enter command argument, image layer, CloudFormation output, CDK context, client bundle, log, trace or exception.
- Task role only gets exact `secretsmanager:GetSecretValue` and relevant KMS decrypt with encryption context/ARN conditions where supported.
- Application validates secret presence/shape but MUST not print value or hash that enables guessing.

## 6. Rotation protocol

1. Open approved change/incident and identify exact secret/consumers.
2. Create new version; maintain bounded old/new overlap only if protocol supports.
3. Restart/refresh consumers and verify synthetic health.
4. Confirm old version no longer used via metadata, not secret logging.
5. Revoke old provider credential/version.
6. Run authentication/provider/write confirmation tests.
7. Record timestamps, actors, version refs and result in audit evidence.

Suspected compromise skips scheduled wait: revoke/rotate immediately under incident authority. Key/secret deletion remains separate destructive approval and is not part of ordinary rotation.

## 7. DeepSeek configuration gate

DeepSeek adapter may start only when:

- provider endpoint matches allowlist and TLS validation is enabled;
- named model alias resolves to reviewed provider model/capability;
- prompt/model/provider versions have passed affected eval suites;
- secret reference exists and is accessible only to gateway runtime;
- `LLM_DATA_POLICY=NO_DIRECT_IDENTIFIERS` for synthetic stage;
- outbound payload redaction test passes;
- timeout, retry, parallel request and cost/token limits are configured;
- `OQ-005`/vendor approval is closed before real data.

Failure enters `DEGRADED_NO_LLM`; MUST NOT silently switch provider or use a developer key.

## 8. Mock auth and Entra readiness

- Mock auth enabled only by both environment allowlist and `AUTH_PROVIDER=mock`; production hard fails.
- Mock fixtures are deterministic, synthetic and cannot self-select privileged role on public demo.
- Entra values (`issuer`, `tenant`, `audience`, redirect URI, app-role mapping) stay unresolved until `OQ-004`; unknown mapping denies.
- Raw ID/access/refresh tokens are not runtime config and MUST never persist/log.

## 9. Configuration change classes

| Change | Gate |
|---|---|
| Timeout/capacity within tested range | Platform owner + automated tests |
| Model/prompt/retrieval version | AI eval + release review |
| Provider/egress destination | Architecture + Security + Privacy/Vendor |
| Auth/issuer/role mapping | Identity + Security + human approval |
| Retention/logging/redaction | Privacy + Security |
| KMS/IAM/secret policy | Security-specific task and approval |
| Feature kill/degraded state | Runbook authority, time-bound audit |
| Real-data/data-mode switch | Legal/Data/Product/ Security approval; production gate |

## 10. Validation

- Schema validation before build/deploy and again at startup.
- Browser bundle scan for server keys/secret names/values.
- Configuration snapshot records keys + redacted value hashes/version, not secrets.
- Cross-environment test proves prod cannot reference nonprod secret/KMS/bucket/queue.
- Rotation drill and revoked-old-secret negative test.
- Synthetic-only and mock-auth fail-start tests for every environment combination.

