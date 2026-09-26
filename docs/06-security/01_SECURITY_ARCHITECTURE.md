---
document_id: "DOC-SEC-001"
version: "0.1.0"
status: "draft"
owner: "Security Architect"
approvers: ["Architecture Owner", "Privacy/Legal Owner", "Operations Owner"]
last_updated: "2026-09-21"
---

# Security architecture

## 1. Mục tiêu và phạm vi

Tài liệu này quy định kiến trúc bảo mật mục tiêu cho web/PWA, BFF, FastAPI, LangGraph orchestrator, RAG, tool gateway, PostgreSQL/pgvector, Redis, object storage, audit pipeline, DeepSeek gateway và các mock integration. Phạm vi là một trường duy nhất theo `DEC-001`; trường `tenant_id` không được dùng để tạo cảm giác đã có isolation đa tenant.

Mục tiêu bắt buộc là bảo vệ confidentiality, integrity, availability; ngăn LLM trở thành security principal; và bảo đảm lỗi policy/identity luôn dẫn đến từ chối an toàn.

## 2. Nguyên tắc kiến trúc

| ID | Quy tắc chuẩn | Acceptance evidence | Failure behavior |
|---|---|---|---|
| `SEC-ARCH-001` | Mọi request MUST được xác thực ở boundary và ủy quyền lại tại service sở hữu resource; network location MUST NOT được coi là tin cậy. | Integration tests chứng minh request thiếu/giả token nhận `401`, token đúng nhưng thiếu quyền nhận `403`. | Deny request; emit sanitized audit event. |
| `SEC-ARCH-002` | Browser MUST chỉ gọi public edge/BFF. Database, Redis, object storage, worker admin port và internal tools MUST không public-routable. | IaC/network test; port scan từ public test runner. | Deployment gate fails. |
| `SEC-ARCH-003` | LLM MUST được coi là untrusted reasoning component. LLM output MUST qua schema validation, policy decision và output encoding trước khi ảnh hưởng hệ thống hoặc UI. | Unit tests với malformed JSON, injected arguments và HTML/Markdown payload. | Reject output; no tool call; safe user message. |
| `SEC-ARCH-004` | LLM MUST NOT sở hữu database credentials, AWS credentials hoặc raw integration secrets. | Secret/IAM inventory không có principal LLM; architecture test kiểm tra env allowlist. | Startup fails for forbidden secret exposure. |
| `SEC-ARCH-005` | Tool Gateway MUST nhận `actor`, `action`, `resource`, normalized input, policy decision và correlation ID từ trusted application context; MUST NOT tin actor/role do model cung cấp. | Contract tests thay actor trong tool arguments nhưng policy vẫn dùng server context. | Deny and raise `SECURITY_POLICY_VIOLATION`. |
| `SEC-ARCH-006` | Mọi write action MUST dùng preview → explicit confirmation → idempotent execution theo `DEC-015`. | Replay, expiry, payload-binding và cross-user confirmation tests. | Expired/mismatched token returns `409`/`403`; no side effect. |
| `SEC-ARCH-007` | Public knowledge và personal/operational data MUST ở logical stores/indexes tách biệt. Personal data MUST NOT được embedding vào general knowledge index. | Index inventory; test query không truy hồi synthetic profile từ public collection. | Ingestion rejected and quarantined. |
| `SEC-ARCH-008` | External content, uploaded files và retrieved chunks MUST mang taint metadata `untrusted_content=true`. Content MUST NOT được ghép vào system/developer instruction channel. | Prompt assembly snapshot test. | Exclude content or route to quarantine. |
| `SEC-ARCH-009` | Egress từ API/worker MUST theo destination allowlist. User-provided URL MUST NOT được server fetch mặc định. | Egress policy test và SSRF corpus. | Reject URL; alert repeated attempts. |
| `SEC-ARCH-010` | Production MUST tách AWS account hoặc ít nhất account boundary được phê duyệt khỏi non-production; database, keys, secrets và identity clients MUST không dùng chung. | Resource inventory và configuration assertions. | Production gate fails. |
| `SEC-ARCH-011` | Security logs MUST đi tới append-only centralized sink ngoài quyền sửa của application role. | IAM test; attempted update/delete bị deny; restoration check. | Alert and block launch if immutability unavailable. |
| `SEC-ARCH-012` | Mọi external provider MUST có timeout, bounded retry, circuit breaker và deterministic fallback. Retry MUST không lặp side effect. | Chaos tests cho timeout/5xx/partial success. | Degrade to search/ticket-only mode. |
| `SEC-ARCH-013` | Health endpoint public MUST chỉ trả trạng thái tổng quát; diagnostics chi tiết MUST yêu cầu privileged service identity. | API tests không lộ version, stack, secret names hoặc dependency topology. | Return generic unavailable status. |
| `SEC-ARCH-014` | Admin plane MUST tách route, permission và telemetry khỏi student plane; admin operation nhạy cảm MUST yêu cầu MFA/step-up trong Entra phase. | Route inventory, role tests và MFA claim tests. | Deny privileged operation. |
| `SEC-ARCH-015` | Mọi control bắt buộc MUST được triển khai bằng code/IaC/policy có test; system prompt đơn lẻ MUST NOT được coi là security control. | Control-to-test matrix. | Control marked `not_implemented`; launch blocked. |

## 3. Trust zones và boundary

```text
ZONE-0 Untrusted
  Browser/PWA, uploaded documents, public web content, user prompt
        |
        | HTTPS + rate limit + WAF rules
        v
ZONE-1 Public edge
  CDN/WAF -> Next.js BFF/session boundary
        |
        | authenticated service request + CSRF protection
        v
ZONE-2 Application private network
  FastAPI -> Policy Enforcement -> LangGraph -> Tool Gateway
        |                  |                |
        |                  |                +--> approved integration adapters
        |                  +--> LLM Gateway ----> DeepSeek (external/untrusted)
        v
ZONE-3 Data private network
  PostgreSQL/pgvector, Redis, object storage, queue
        |
        v
ZONE-4 Security/operations account or boundary
  audit archive, alerts, KMS, Secrets Manager, backup vault
```

Boundary rules:

- Crossing `ZONE-0 -> ZONE-1` MUST apply request size, content type, rate and authentication/session controls.
- Crossing `ZONE-1 -> ZONE-2` MUST carry a server-created `IdentityContext`; user-controlled identity headers MUST be stripped.
- Crossing `ZONE-2 -> ZONE-3` MUST use workload identity and least-privilege database roles; no shared admin user.
- Crossing `ZONE-2 -> external LLM` MUST invoke the privacy gateway in `PRIV-FLOW-006`; real PII transmission is disabled.
- Crossing into `ZONE-4` MUST be one-way for application logs where feasible; application roles MUST NOT delete evidence.

## 4. Security enforcement points

| Enforcement point | MUST validate | MUST emit |
|---|---|---|
| Edge/BFF | TLS, method, host, body size, session, CSRF for cookie-authenticated mutation | request ID, result class, rate-limit decision |
| API middleware | token/session validity, `IdentityContext`, account state | actor pseudonymous ID, auth outcome |
| Route/service | function permission, object ownership/scope, field allowlist | authorization decision ID |
| Agent orchestrator | intent allowlist, risk class, tool allowlist, loop/tool/token budget | model/prompt version, policy outcome, no raw secret |
| Tool Gateway | server actor, action schema, resource scope, confirmation binding, idempotency | tool execution ID and redacted result |
| Data layer | row predicate, transaction boundary, least-privilege role | database audit metadata where supported |
| Output boundary | citation/evidence, HTML/Markdown encoding, link allowlist, PII/DLP check | response policy outcome |

## 5. Degraded modes

| Trigger | Allowed capability | Prohibited capability |
|---|---|---|
| LLM unavailable/untrusted output | deterministic search, ticket form, status page | generated advice, tool selection by LLM |
| Policy engine unavailable | public static content only | personal read, all write, admin action |
| Identity provider unavailable | existing short-lived session only if session policy explicitly permits | new login, role elevation, admin action |
| Audit sink unavailable | read-only public FAQ for a bounded grace period configured by Operations | personal data, writes, knowledge publish, admin changes |
| Knowledge integrity incident | ticket/handover and approved static emergency message | RAG answer from affected corpus |

## 6. Implementation decomposition

Coding agent MUST split implementation into disjoint tasks:

1. network/IaC boundary;
2. identity context middleware;
3. authorization policy interface;
4. tool gateway validation;
5. egress allowlist;
6. audit append-only sink;
7. degraded-mode switches;
8. negative integration and chaos tests.

Một task MUST NOT đồng thời sửa auth, network, database và agent workflow. Nếu contract của `IdentityContext`, `PolicyDecision` hoặc `ActionConfirmation` chưa được approved, task MUST dừng thay vì tự tạo schema.

## 7. Traceability

- Decisions: `DEC-003`, `DEC-004`, `DEC-007`, `DEC-008`, `DEC-009`, `DEC-014`, `DEC-015`, `DEC-020`.
- Assumptions: `ASM-001`, `ASM-002`, `ASM-006`.
- Threats: `THR-S-001`, `THR-T-003`, `THR-I-001`, `THR-LLM-001` đến `THR-LLM-010`.
- Controls: `SEC-CTRL-001` đến `SEC-CTRL-020`.

## 8. Nguồn chính

- [AWS Security Reference Architecture for generative AI agents](https://docs.aws.amazon.com/prescriptive-guidance/latest/security-reference-architecture-generative-ai/gen-ai-agents.html).
- [OWASP API Security Top 10 2023](https://api-security.owasp.org/editions/2023/en/0x11-t10/).
- [OWASP LLM06:2025 Excessive Agency](https://genai.owasp.org/llmrisk/llm062025-excessive-agency/).
- [NIST CSF 2.0](https://www.nist.gov/cyberframework).

Nguồn được truy cập ngày `2026-09-21`.
