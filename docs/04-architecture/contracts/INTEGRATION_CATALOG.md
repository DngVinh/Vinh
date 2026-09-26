---
document_id: "DOC-INT-001"
version: "1.0.0"
status: "reviewed"
owner: "Integration Architect"
approvers: ["Solution Architect", "Security Lead", "Operations Lead"]
last_updated: "2026-09-21"
---

# Integration catalog V1

## 1. Nguyên tắc biên tích hợp

| ID | Quy tắc |
|---|---|
| INT-BASE-001 | Domain code MUST depend on internal ports/interfaces, không import SDK/provider concrete. |
| INT-BASE-002 | Mọi outbound call MUST có timeout, bounded retry, correlation ID, redacted telemetry và circuit-breaker policy. |
| INT-BASE-003 | Retry chỉ cho operation safe hoặc có provider idempotency key; không retry write mù quáng. |
| INT-BASE-004 | External response là untrusted input và MUST validate trước khi map vào domain. |
| INT-BASE-005 | Secret chỉ lấy từ approved secret provider; không nằm trong repo, log, browser hoặc event. |
| INT-BASE-006 | Demo MUST chạy được hoàn toàn bằng deterministic fake adapters, không cần paid service hay real credentials. |
| INT-BASE-007 | Mỗi adapter MUST expose health/dependency status nhưng MUST không lộ endpoint, credential hoặc raw provider error cho client. |

## 2. Catalog

### INT-AUTH-001 — Synthetic Identity Provider

| Thuộc tính | Giá trị |
|---|---|
| V1 status | Required, simulated |
| Direction | inbound authentication |
| Contract | `contracts/json-schema/identity/synthetic-identity-claims.schema.json` |
| Data class | PERSONAL |
| Availability | local dependency; fail closed |
| Owner | Identity Platform |

MUST ký token bằng asymmetric key dành riêng môi trường; API verify issuer, audience, signature, expiry và claims schema. Production profile MUST disable adapter. Demo identity MUST hiển thị rõ synthetic/unofficial status.

Failure mapping:

- invalid/expired token → `401 AUTHENTICATION_REQUIRED`;
- valid token nhưng synthetic issuer tại production → `403 IDENTITY_PROVIDER_NOT_ALLOWED`;
- unknown role claim → `403 ROLE_MAPPING_FAILED`, không default role.

### INT-AUTH-002 — Microsoft Entra ID OIDC (future-ready boundary)

| Thuộc tính | Giá trị |
|---|---|
| V1 status | Contract boundary only; not enabled |
| Protocol | OIDC Authorization Code + PKCE |
| Direction | inbound authentication |
| Data class | PERSONAL/SENSITIVE tokens |
| Owner | Identity Platform + university identity admin |

OIDC Core định nghĩa identity layer dựa trên OAuth 2.0; PKCE được chuẩn hóa trong [RFC 7636](https://datatracker.ietf.org/doc/html/rfc7636). V1 MUST NOT hard-code HUCE tenant, group IDs hoặc unapproved claims. Mapping target là internal identity context giống synthetic provider. OQ-004 blocks enablement.

### INT-SIS-001 — Synthetic SIS/Schedule Adapter

| Thuộc tính | Giá trị |
|---|---|
| V1 status | Required fake adapter |
| Capabilities | current student profile, schedule range |
| Direction | outbound read-only |
| Data class | PERSONAL |
| Source of truth | generated synthetic dataset |

Port operations:

```text
get_student_profile(internal_user_id) -> StudentProfileSnapshot
list_schedule(internal_user_id, starts_at, ends_at, page) -> SchedulePage
```

Adapter MUST NOT accept arbitrary student ID from student-facing request. Service resolves source subject from authenticated identity. Timeout budget 2 seconds; at most 2 retries with jitter for safe reads. Real SIS enablement blocked by OQ-007.

### INT-TICKET-001 — Internal Ticket Repository

V1 uses internal domain/storage, không external helpdesk. A future external adapter MAY mirror tickets after commit, nhưng internal Ticket remains API source until a separate ADR. Export/mirroring events MUST not include message body by default.

### INT-ROOM-001 — Synthetic Room Catalog and Booking Adapter

| V1 status | Required fake adapter/domain |
|---|---|
| Capabilities | room search, availability, confirmed booking, cancellation |
| Write policy | preview + confirmation + idempotency |
| Data class | PERSONAL for requester/purpose |

Port MUST support `reserve_booking(command, idempotency_key)` atomically. Preview availability is advisory. Real facility system integration blocked by OQ-007.

### INT-DOC-001 — Synthetic Document Service

Creates request records only; MUST NOT produce official HUCE certificates. Any generated sample MUST watermark `DỮ LIỆU MÔ PHỎNG — KHÔNG CÓ GIÁ TRỊ`. The adapter accepts allowlisted document/purpose codes and returns a synthetic tracking reference.

### INT-NOTIFY-001 — Notification Provider

V1 required capabilities: in-app notification; email adapter MAY be fake. SMS is disabled. Notification command MUST reference template ID + recipient ID + variables; MUST NOT carry arbitrary HTML or secret. Delivery is asynchronous and at-least-once; provider dedupe key is `notification_delivery.id`.

Failure behavior: retry transient provider errors with exponential backoff; permanent address rejection becomes terminal `FAILED_FINAL`; business transaction MUST not roll back because a non-critical notification failed.

### INT-LLM-001 — Provider-neutral LLM gateway / DeepSeek adapter

| Thuộc tính | Giá trị |
|---|---|
| V1 status | Interface required; fake provider mandatory for tests; DeepSeek first real adapter |
| Direction | outbound |
| Data class | redacted text only unless privacy approval expands |
| Owner | AI Platform |

Domain services call provider-neutral gateway. Endpoint, model and credentials are configuration. The official DeepSeek API documentation describes OpenAI-compatible client configuration; implementation MUST still isolate provider details behind the gateway ([DeepSeek API guide](https://api-docs.deepseek.com/)). This catalog does not define LLM tool contracts.

Requirements:

- Default outbound payload MUST exclude direct identifiers, raw auth tokens, hidden security context and unrestricted database records.
- Fake provider MUST return deterministic fixtures for unit/integration tests.
- Timeout or provider outage MUST degrade to search/ticket-only behavior where product flow permits.
- No provider response may directly commit a write action.

### INT-OBJ-001 — Private object storage

Stores source documents and derived safe artifacts. Object keys are private and MUST not appear in public API. Download uses short-lived authorized URL or API streaming. Upload MUST pass content-type allowlist, size limit, checksum and malware scan before `READY_FOR_REVIEW`.

### INT-EVENT-001 — Event transport

V1 logical contract is transport-neutral AsyncAPI. AWS mapping MAY use SNS/SQS/EventBridge only after platform ADR. Producer publishes via outbox; consumers deduplicate by `event_id`. Transport retention is not audit retention.

## 3. Timeout, retry và circuit policy

| Integration | Connect/request timeout | Retry | Circuit behavior |
|---|---:|---:|---|
| Synthetic IdP verification | local, 100 ms target | 0 | fail closed |
| SIS read | 2 s | max 2 | open after configured failure threshold; return 503 |
| Room write | 5 s | only with same idempotency key | ambiguous result triggers reconciliation |
| Notification | 5 s worker | max 5 transient | DLQ/manual review |
| LLM | model-class configuration, hard cap required | max 1 safe retry | fallback/abstain |
| Object storage | 10 s | max 2 safe request | preserve upload state |

Agent MUST NOT invent numeric retry thresholds beyond table/config defaults; if SDK forces behavior, expose it in config and test.

## 4. Synthetic dataset strategy

| ID | Rule |
|---|---|
| INT-DATA-001 | Dataset generator MUST be deterministic by explicit seed and version. |
| INT-DATA-002 | Generated names/emails/student codes MUST be fictional and use reserved/non-routable domains such as `example.invalid`. |
| INT-DATA-003 | Public HUCE pages MAY inform taxonomy/provenance but MUST NOT be redistributed as official corpus without rights review. |
| INT-DATA-004 | Large generated corpus MUST be reproducible from generator + manifest + checksums; repository SHOULD store representative fixtures, not bulk generated output. |
| INT-DATA-005 | Gold eval set MUST be separate from retrieval corpus generation to reduce leakage; every gold answer cites a deterministic synthetic source/version/section. |

## 5. Readiness matrix

| Integration | Demo ready criteria | Production enablement blocker |
|---|---|---|
| Synthetic IdP | signed tokens, negative validation tests | MUST remain disabled in production |
| Entra OIDC | port + config schema only | OQ-004, security review |
| Synthetic SIS | deterministic profiles/schedules | real API approval OQ-007 |
| Room | concurrency/idempotency tests | real API and process owner |
| Document service | watermarked simulated requests | official workflow/authority |
| Notification | in-app + fake email | sender domain/provider/DPA |
| DeepSeek | fake tests + gateway contract | privacy OQ-005, budget OQ-008, secrets |
| Object storage | private bucket contract | approved AWS account/region |

## 6. Acceptance evidence và failure behavior

Mỗi adapter implementation task MUST cung cấp contract tests, timeout/retry tests, redaction evidence, deterministic fake và mapping error. Nếu real API/spec/credential chưa có, agent MUST implement fake boundary only và emit `INTEGRATION_NOT_ENABLED`; MUST NOT scrape, reverse-engineer hoặc connect vào hệ thống HUCE.
