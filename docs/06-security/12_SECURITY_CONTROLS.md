---
document_id: "DOC-SEC-007"
version: "1.0.0"
status: "approved"
owner: "Security Architect"
approvers: ["Privacy/Legal Owner", "Architecture Owner", "Security Test Lead"]
last_updated: "2026-09-22"
---

# Security and privacy control catalog

## 1. Cách sử dụng

Đây là catalog control chuẩn cho Campus 24/7, đã được phê duyệt chính thức (`status: approved`) cho phạm vi triển khai synthetic implementation ngày 2026-09-22 theo `TASK-DOC-SEC-001`. `Implemented` chỉ được ghi khi evidence tồn tại và test pass; code tồn tại nhưng chưa kiểm chứng = `Partially implemented`. Mỗi implementation task MUST chọn control IDs cụ thể và MUST không thay đổi mục tiêu control.

Status values:

```text
Not implemented -> Partially implemented -> Implemented -> Verified
                                      \-> Exception (approved, expiring)
```

## 2. Control catalog

| ID | Control objective and MUST behavior | Primary threats | Minimum verification evidence | Owner |
|---|---|---|---|---|
| `SEC-CTRL-001` | Asset/data inventory MUST cover service, store, integration, owner, classification, environment and region. | `THR-I-*`, `THR-LINK-*` | Automated inventory + owner review | Architecture/Data |
| `SEC-CTRL-002` | Strong authentication boundary MUST validate session/token and prohibit production mock auth. | `THR-S-001` | Auth negative corpus; production config test | Identity |
| `SEC-CTRL-003` | Authorization MUST be deny-default RBAC+ABAC+object/field policy. | `THR-I-001`, `THR-E-*` | Route/tool matrix and BOLA/BFLA tests | Security/API |
| `SEC-CTRL-004` | Privileged access MUST require MFA/step-up, time-bound grants, separation of duties and review. | `THR-E-002` | MFA/grant/break-glass drill | Identity/Ops |
| `SEC-CTRL-005` | Network MUST expose only edge endpoints; private stores/tools and egress MUST be restricted. | `THR-E-003`, `THR-I-*` | IaC tests, scan, egress deny tests | Platform |
| `SEC-CTRL-006` | All input/file/tool/model output MUST have strict type, size, schema and encoding validation. | `THR-T-003`, `THR-LLM-005`, `THR-D-*` | Fuzz and malicious-file corpus | API/AI |
| `SEC-CTRL-007` | Tool Gateway MUST use server identity/policy, typed allowlisted tools and no arbitrary code/SQL/URL. | `THR-S-003`, `THR-LLM-006` | Tool schema and policy spy tests | AI/API |
| `SEC-CTRL-008` | Write action MUST use preview, actor/payload-bound explicit confirmation and idempotency. | `THR-T-001`, `THR-R-001`, `THR-R-002` | Replay/tamper/partial-success tests | API |
| `SEC-CTRL-009` | TLS and encryption at rest MUST protect classified data according to `SEC-CRYPTO-*`. | `THR-I-*` | TLS/IaC/KMS assertions | Platform |
| `SEC-CTRL-010` | Secrets MUST be stored in approved manager, least-privilege accessed, scanned and rotated/revoked. | `THR-S-002`, `THR-I-003` | IAM, secret scan, rotation drill | Platform/Security |
| `SEC-CTRL-011` | Key lifecycle MUST separate admin/use, audit access and protect deletion. | `THR-T-002`, `THR-I-003` | KMS policy tests and deletion alert | Security/Platform |
| `SEC-CTRL-012` | Knowledge MUST have provenance, checksum, malware/PII/injection scan, quarantine and independent publish approval. | `THR-T-003`, `THR-LLM-004` | Ingestion tests and publication audit | Knowledge/Security |
| `SEC-CTRL-013` | RAG authorization MUST filter accessible corpus before ranking and isolate personal/public domains. | `THR-I-002`, `THR-LLM-008` | Cross-user/corpus canary tests | AI/Data |
| `SEC-CTRL-014` | AI response MUST validate evidence/citation, encode output, apply link policy and abstain when unsupported. | `THR-I-004`, `THR-LLM-005`, `THR-LLM-009` | Grounding/security eval | AI Quality |
| `SEC-CTRL-015` | Privacy lifecycle MUST enforce minimization, purpose, retention, rights and deletion reconciliation. | `THR-LINK-*`, `PRIV-DPIA-*` | Inventory, rights/deletion E2E | Privacy/Data |
| `SEC-CTRL-016` | External LLM/provider egress MUST block C2/C3, secrets and unapproved destinations. | `THR-LLM-002`, `THR-LINK-001` | DLP/provider spy and network test | Privacy/Security |
| `SEC-CTRL-017` | Resource/time/token/tool/cost budgets and rate limits MUST be enforced server-side. | `THR-D-001`, `THR-LLM-010` | Load/limit/circuit-breaker tests | Platform/AI |
| `SEC-CTRL-018` | Audit MUST be structured, minimized, append-only, independently accessible and monitored. | `THR-R-*`, `THR-T-004` | Audit/DLP/IAM/alert tests | SecOps |
| `SEC-CTRL-019` | Dependency/build pipeline MUST pin/scan/sign/provenance-track artifacts and block critical findings. | `THR-LLM-003`, `THR-T-002` | SBOM, SCA, image/IaC scans, provenance | Engineering/Platform |
| `SEC-CTRL-020` | Backup/restore and degraded modes MUST be tested against RPO/RTO and deletion replay. | `THR-D-002`, `PRIV-DPIA-005` | Restore/chaos drill | Operations |
| `SEC-CTRL-021` | Incident response MUST classify, contain, preserve evidence, assess notification and recover safely. | All realized threats | Tabletop + technical drill | Incident Commander |
| `SEC-CTRL-022` | Vendor/cross-border governance MUST maintain contracts, processing terms, locations, subprocessors and exit plan. | `THR-LLM-003`, `PRIV-DPIA-003/009` | Approved vendor record | Vendor/Privacy |
| `SEC-CTRL-023` | Security tests MUST include negative authorization, abuse, DLP, prompt injection and side-effect assertions. | All | `THR-ABUSE-*` results | Security Test |
| `SEC-CTRL-024` | Change/release MUST enforce secure SDLC gates and human approval for `DEC-020` actions. | `THR-T-002`, supply chain | Gate evidence | Engineering/Security |
| `SEC-CTRL-025` | Emergency/sensitive flow MUST minimize disclosure, use approved wording/contact and route HITL without autonomous diagnosis. | `PRIV-DPIA-007`, `THR-LLM-009` | Safety eval and service drill | Product/Ops |

## 3. Control implementation record

```yaml
control_implementation:
  control_id: "SEC-CTRL-..."
  status: "not_implemented|partially_implemented|implemented|verified|exception"
  implementation_refs: ["path#symbol", "IaC-resource"]
  requirement_refs: ["SEC-...", "PRIV-...", "THR-..."]
  test_refs: ["test-id-or-path"]
  evidence_refs: ["immutable-artifact-uri-or-hash"]
  environments: ["test", "staging"]
  owner: "role"
  verified_by: "independent-role"
  verified_at: "RFC3339"
  expires_at: "RFC3339|null"
  residual_risk: "statement"
```

## 4. Exception policy

| ID | Requirement | Failure behavior |
|---|---|---|
| `SEC-CTRL-026` | Exception MUST identify control, scope, reason, compensating controls, residual risk, owner and expiry ≤90 days by default. | Exception invalid; gate fails. |
| `SEC-CTRL-027` | Critical controls for unauthorized access/write, secret exposure, PII-to-provider or audit integrity MUST NOT be waived for production without explicit Security + Privacy + Sponsor acceptance and legal permissibility. | No launch. |
| `SEC-CTRL-028` | Expired exception MUST automatically become failed control. | Deployment/release blocked. |
| `SEC-CTRL-029` | Control owner MUST not be sole verifier for high-risk control. | Status cannot become `verified`. |
| `SEC-CTRL-030` | Evidence MUST be reproducible and synthetic-data safe; screenshot/assertion without underlying result is insufficient for deterministic control. | Evidence rejected. |

## 5. Baseline mapping

- NIST CSF 2.0 được dùng để bảo đảm đủ `Govern, Identify, Protect, Detect, Respond, Recover`; xem [NIST CSF](https://www.nist.gov/cyberframework).
- OWASP ASVS cung cấp cơ sở kiểm thử security controls cho web app; xem [OWASP ASVS](https://owasp.org/projects/asvs).
- OWASP API/LLM Top 10 cung cấp threat awareness, không thay risk assessment cụ thể.
- ISO/IEC 27001:2022 mô tả yêu cầu ISMS/risk management; xem [ISO](https://www.iso.org/standard/27001). Catalog này không tuyên bố dự án được chứng nhận hoặc conformant.

## 6. Traceability

- Requirements: toàn bộ `SEC-*`, `PRIV-*` trong package.
- Threats: `THR-*`.
- Tests: `THR-ABUSE-*`, future approved test IDs.
- Launch: `SEC-LAUNCH-*`, `PRIV-LAUNCH-*`.

Nguồn được truy cập ngày `2026-09-21`.
