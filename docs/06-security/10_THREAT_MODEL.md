---
document_id: "DOC-THR-001"
version: "0.1.0"
status: "draft"
owner: "Security Architect"
approvers: ["Architecture Owner", "AI Quality Owner", "Privacy/Legal Owner"]
last_updated: "2026-09-21"
---

# STRIDE and LLM-specific threat model

## 1. Scope, assumptions and assets

In scope: web/PWA, BFF, FastAPI, agent graph, RAG ingestion/retrieval, Tool Gateway, synthetic operational stores, external LLM adapter, mock/Entra identity boundary, AWS target architecture, CI/CD and audit.

Assets:

- identity/session/authorization state;
- student schedule, tickets, requests, bookings and conversations;
- official knowledge provenance/version/citations;
- tool permissions and confirmation/idempotency state;
- prompts, model/provider configuration and evaluation sets;
- secrets, keys, source/build artifacts;
- audit evidence, service availability and budget.

Threat actors: unauthenticated attacker, malicious/compromised student, malicious/compromised staff, supply-chain attacker, poisoned content publisher, external provider/subprocessor, compromised workload, careless operator và model behaving unexpectedly.

Risk score dùng phương pháp trong `DOC-PRIV-002`; residual score chỉ hạ sau control evidence.

## 2. STRIDE register

| ID | STRIDE | Threat scenario | Inherent | Required controls | Residual target |
|---|---|---|---:|---|---:|
| `THR-S-001` | Spoofing | Giả token/session/header để mạo danh student/staff | 20 | `SEC-AUTHN-002..009`, `SEC-CTRL-002` | ≤4 |
| `THR-S-002` | Spoofing | Dùng stolen workload/API credential | 20 | `SEC-CRYPTO-005..009`, workload identity, rotation | ≤6 |
| `THR-S-003` | Spoofing | LLM tự gán actor/role trong tool call | 20 | `SEC-ARCH-005`, `SEC-AUTHZ-002` | ≤3 |
| `THR-T-001` | Tampering | Sửa action payload sau preview trước confirm | 20 | payload hash binding, `SEC-CRYPTO-010` | ≤3 |
| `THR-T-002` | Tampering | Sửa config/model/prompt/secret ngoài change process | 16 | signed build, protected config, audit, `SEC-SDLC-*` | ≤6 |
| `THR-T-003` | Tampering | Knowledge/document poisoning hoặc hidden instruction | 20 | provenance, quarantine, dual review, taint, injection tests | ≤6 |
| `THR-T-004` | Tampering | Xóa/sửa audit để che hành vi | 20 | immutable sink, separated role, integrity monitoring | ≤4 |
| `THR-R-001` | Repudiation | Người dùng/cán bộ phủ nhận confirmation hoặc admin action | 12 | actor/payload/policy/time evidence, append-only audit | ≤4 |
| `THR-R-002` | Repudiation | Provider/tool trả partial success nhưng client retry | 16 | idempotency, execution ledger, reconciliation | ≤4 |
| `THR-I-001` | Information disclosure | BOLA/BFLA lộ lịch/ticket người khác | 25 | `SEC-AUTHZ-*`, object tests, query predicates | ≤5 |
| `THR-I-002` | Information disclosure | Prompt/RAG/memory chéo phiên hoặc embeddings chứa PII | 25 | index isolation, no personal embeddings, canaries, DLP | ≤5 |
| `THR-I-003` | Information disclosure | Token/secret/PII vào logs/traces/errors | 20 | allowlist logging, pre-export redaction, secret scan | ≤4 |
| `THR-I-004` | Information disclosure | Markdown/URL/image beacon exfiltration | 16 | renderer sanitization, proxy/allowlist, no auto-fetch | ≤4 |
| `THR-D-001` | Denial of service | Flood chat/upload/search/tool gây cạn CPU/token/cost | 16 | quotas, body limits, timeouts, budgets, circuit breakers | ≤6 |
| `THR-D-002` | Denial of service | Provider/identity/audit outage gây cascading failure | 16 | bulkheads, degraded modes, queues, chaos tests | ≤6 |
| `THR-D-003` | Denial of service | Vector/query payload gây pathological search | 12 | query limits, timeout, index safeguards | ≤4 |
| `THR-E-001` | Elevation | Student gọi admin/staff endpoint hoặc mass assignment role | 25 | deny-default, field allowlist, function authz tests | ≤4 |
| `THR-E-002` | Elevation | Support officer mở rộng queue/unit hoặc tự phê duyệt | 20 | ABAC, SoD, time-bound grants, review | ≤5 |
| `THR-E-003` | Elevation | SSRF/tool abuse truy cập metadata/internal service | 25 | egress allowlist, no arbitrary URL, IMDS protection | ≤4 |

## 3. LLM/GenAI-specific register

Các category tham chiếu [OWASP Top 10 for LLM Applications 2025](https://genai.owasp.org/resource/owasp-top-10-for-llm-applications-2025/); mapping là baseline engineering, không phải chứng nhận.

| ID | OWASP area | Threat scenario | Inherent | Required controls | Residual target |
|---|---|---|---:|---|---:|
| `THR-LLM-001` | LLM01 Prompt Injection | User hoặc document bắt model bỏ instruction, leak data/gọi tool | 25 | untrusted-content separation, typed tools, policy outside model, red team | ≤6 |
| `THR-LLM-002` | LLM02 Sensitive Information Disclosure | Model/provider/context làm lộ PII, secrets, cross-session text | 25 | no secrets, PII gate, minimized context, output DLP, provider gate | ≤5 |
| `THR-LLM-003` | LLM03 Supply Chain | SDK/model/provider compromise hoặc silent model change | 20 | pinning, SBOM, provider/model allowlist, eval/release gate | ≤6 |
| `THR-LLM-004` | LLM04 Data and Model Poisoning | Corpus/eval/source bị cấy nội dung sai hoặc malicious | 20 | provenance, checksum, dual approval, corpus diff/eval | ≤6 |
| `THR-LLM-005` | LLM05 Improper Output Handling | Render/execute model HTML, URL, code hoặc SQL unsafely | 25 | schema validation, encoding/sanitization, no eval/SQL | ≤4 |
| `THR-LLM-006` | LLM06 Excessive Agency | Model có quá nhiều tool/quyền/tự chủ, thực thi side effect | 25 | least-function tool set, server authz, preview/confirm, budget | ≤4 |
| `THR-LLM-007` | LLM07 System Prompt Leakage | Prompt/policy bị lộ và bị hiểu nhầm là secret boundary | 12 | no secrets in prompt, response guard, controls outside prompt | ≤4 |
| `THR-LLM-008` | LLM08 Vector/Embedding Weaknesses | Retrieval unauthorized, poisoned chunk, nearest-neighbor leak | 25 | metadata auth filter before rank, isolated index, ingest review | ≤5 |
| `THR-LLM-009` | LLM09 Misinformation | Hallucinated policy/citation ảnh hưởng quyền lợi | 20 | citation validation, effective-date filters, abstention, HITL | ≤6 |
| `THR-LLM-010` | LLM10 Unbounded Consumption | Recursive agent/tool loop hoặc oversized context làm cạn budget | 16 | step/tool/token/time/cost ceilings, circuit breaker | ≤4 |

## 4. Privacy and linking threats

| ID | Scenario | Controls |
|---|---|---|
| `THR-LINK-001` | Kết hợp pseudonymous logs, IP và schedule để tái nhận dạng | Coarsen/segregate, purpose access, retention, aggregate threshold |
| `THR-LINK-002` | Synthetic identity vô tình trùng người thật | Reserved domains/patterns, deterministic generator, sample/provenance review |
| `THR-LINK-003` | Citation URL hoặc external media phát tín hiệu người dùng/query | Link allowlist, no auto-fetch, warning/proxy policy |
| `THR-LINK-004` | Staff search rộng để theo dõi sinh viên ngoài nhiệm vụ | Query scope, purpose code, anomaly alert, access review |

## 5. Attack paths ưu tiên

### Path A — Indirect prompt injection to side effect

```text
Malicious document -> RAG retrieval -> model follows hidden instruction
-> forged tool arguments -> unauthorized booking/ticket/export
```

Path MUST bị cắt tại tối thiểu ba điểm: ingestion/quarantine, prompt taint boundary, Tool Gateway authorization/confirmation. Prompt warning đơn lẻ không đủ.

### Path B — Cross-user data disclosure

```text
Student changes object ID -> API lookup -> missing scope predicate
-> response/model context -> disclosure
```

Path MUST bị cắt trước data fetch bằng policy/query predicate; client-side hiding hoặc post-filter không hợp lệ.

### Path C — Secret to provider

```text
Secret in log/document/user prompt -> context assembly -> DeepSeek request
```

Path MUST bị cắt ở source scanning và runtime egress DLP. Provider policy không thay local prevention.

### Path D — Compromised privileged operator

```text
Stolen admin session -> change prompt/policy -> disable guard -> bulk export
```

Path MUST bị cắt bằng MFA/step-up, separation of duties, immutable audit, change approval và egress/export control.

## 6. Threat-model maintenance requirements

| ID | Requirement | Evidence | Failure behavior |
|---|---|---|---|
| `THR-GOV-001` | Mỗi external boundary, data store, privileged operation và LLM tool MUST map ít nhất một threat hoặc explicit “not applicable” rationale. | Coverage matrix. | Architecture review fails. |
| `THR-GOV-002` | New provider/tool/data class/integration MUST trigger threat-model diff before implementation task becomes `ready`. | Change record with added/updated threats. | Task blocked. |
| `THR-GOV-003` | Critical/High inherent threats MUST map preventive, detective and response control where feasible. | Threat-control matrix. | No launch/risk acceptance required. |
| `THR-GOV-004` | Residual score MUST cite passing evidence; planned controls count as absent. | Linked test/drill reports. | Keep inherent/residual high. |
| `THR-GOV-005` | Red-team corpus MUST include direct/indirect/multilingual/obfuscated injection, BOLA, data exfiltration and budget abuse. | Versioned synthetic corpus/results. | AI/security gate fails. |
| `THR-GOV-006` | Threat model MUST review at least each major release and after incident/material architecture change. | Review history. | Release blocked after stale threshold. |

## 7. Traceability

- Architecture: `SEC-ARCH-*`.
- Data/privacy: `SEC-DATA-*`, `PRIV-FLOW-*`, `PRIV-DPIA-*`.
- Controls: `SEC-CTRL-*`.
- Abuse tests: `THR-ABUSE-*`.
- Baseline: [OWASP LLM08:2025](https://genai.owasp.org/llmrisk/llm082025-vector-and-embedding-weaknesses/), [OWASP LLM06:2025](https://genai.owasp.org/llmrisk/llm062025-excessive-agency/), [OWASP API Security Top 10](https://api-security.owasp.org/editions/2023/en/0x11-t10/).

Nguồn được truy cập ngày `2026-09-21`.
