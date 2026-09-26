---
document_id: "DOC-AI-004"
version: "1.0.0"
status: "reviewed"
owner: "AI Quality Lead"
approvers: ["AI Architecture Lead", "Security Architect", "Knowledge Governance Lead"]
last_updated: "2026-09-21"
---

# Prompt governance và structured output

## 1. Mục tiêu

Prompt là versioned production artifact, không phải chuỗi tùy ý trong source code. Mọi output được code tiêu thụ là untrusted cho đến khi parse và validate. Tài liệu này định nghĩa lifecycle, layering, variable safety, schema rules và failure behavior.

## 2. Prompt registry

Mỗi prompt MUST có manifest:

```yaml
prompt_id: "AI-PROMPT-<DOMAIN>-<NNN>"
version: "semver"
status: "draft|reviewed|approved|retired"
purpose: "single bounded purpose"
owner: "role"
model_profiles: ["logical-profile"]
input_schema_ref: "path or null"
output_schema_ref: "path or null"
allowed_tool_ids: []
max_input_tokens: 0
max_output_tokens: 0
privacy_classes: ["public", "internal", "personal_redacted"]
eval_dataset_ids: ["EVAL-..."]
content_sha256: "sha256:..."
change_summary: "..."
```

Approved prompt content MUST được lưu ngoài application code trong version-controlled prompt directory do architecture task xác định. Application chỉ reference `prompt_id@version`; MUST NOT copy/paste prompt vào nhiều node.

## 3. Prompt layering

Thứ tự chuẩn tắc:

1. `platform_policy`: immutable safety, privacy, simulation notice và non-authority rules;
2. `task_instruction`: một nhiệm vụ cụ thể của node;
3. `output_contract`: schema, allowed enums, no-extra-fields;
4. `trusted_context`: server-generated facts tối thiểu;
5. `untrusted_context`: user text, retrieved text, tool result, luôn có delimiter/label;
6. `response_style`: chỉ format, không thay đổi policy.

Instruction trong `untrusted_context` MUST được coi là nội dung cần phân tích, không phải lệnh. Retrieved document MUST có wrapper chứa `source_id`, `document_version_id`, `chunk_id`, `trust=untrusted_content`. XML/Markdown delimiter không tự tạo security boundary; application authorization và output validation vẫn bắt buộc.

## 4. Variable contract

- Mỗi variable MUST có type, max length/count, source và privacy class.
- Raw template interpolation MUST escape/serialize theo format. Không nối user text vào system instruction bằng string concatenation.
- Missing required variable MUST fail trước provider call.
- Extra variable MUST fail để phát hiện caller/template drift.
- Secret, access token, password, connection string và full authorization claims MUST NOT là prompt variable.
- Conversation history MUST được chọn bởi deterministic context builder và giới hạn theo turn/token; model không tự truy cập toàn lịch sử.
- Citation IDs MUST do retrieval layer cấp, model chỉ được reference ID allowlisted.

## 5. Prompt families V1

| Prompt ID | Mục tiêu duy nhất | Output |
|---|---|---|
| AI-PROMPT-INTENT-001 | Phân loại route | `IntentDecision` schema |
| AI-PROMPT-SAFETY-001 | Classifier nhạy cảm thứ hai | `SafetyDecision` schema |
| AI-PROMPT-QUERY-001 | Rewrite truy vấn giữ nguyên constraints | `QueryPlan` schema |
| AI-PROMPT-RERANK-001 | Rerank candidate IDs | `RerankResult` schema |
| AI-PROMPT-ANSWER-001 | Soạn câu trả lời từ evidence allowlist | `GroundedDraft` schema |
| AI-PROMPT-TOOL-001 | Trích candidate arguments cho đúng một tool | tool input schema |
| AI-PROMPT-SUMMARY-001 | Tóm tắt hội thoại/handover tối thiểu | `SafeSummary` schema |
| AI-PROMPT-REPAIR-001 | Repair syntax/schema một lần | schema ban đầu |

Một prompt MUST NOT vừa classify intent, truy hồi, quyết định quyền, execute tool và soạn câu trả lời.

## 6. Structured output rules

Mọi schema MUST dùng JSON Schema Draft 2020-12 và:

- root `type: object`;
- `additionalProperties: false` tại mọi object nghiệp vụ;
- explicit `required`;
- enum/const thay vì free-text status;
- `minLength`, `maxLength`, `minimum`, `maximum`, `maxItems` phù hợp;
- string date/time dùng RFC 3339 format nhưng application MUST thực hiện format assertion;
- ID có pattern cụ thể;
- nullable chỉ khi domain thực sự cho phép;
- không dùng số floating làm money hoặc confidence ngoài range `0..1`;
- không chấp nhận provider-only keyword không qua validator nội bộ.

Application MUST parse strict JSON và reject duplicate object keys, non-finite numbers, comments, trailing text, invalid Unicode hoặc nesting vượt limit. Schema validation thành công không thay thế semantic validation, authorization hoặc evidence check.

Dialect chính thức: [JSON Schema Draft 2020-12](https://json-schema.org/draft/2020-12).

## 7. Output handling

```text
provider bytes
 -> UTF-8/size guard
 -> strict JSON parse
 -> JSON Schema validation
 -> semantic validation
 -> policy/evidence/authorization gate
 -> use or fail-safe fallback
```

- Không dùng regex để “cứu” JSON hỏng.
- Repair tối đa một lần, chỉ cho output read-only chưa tạo side effect.
- Repair output MUST chạy lại toàn pipeline.
- Safety classifier parse failure MUST dùng conservative deterministic decision.
- Intent parse failure MUST route `unsupported` hoặc bounded clarification.
- Tool argument parse/validation failure MUST NOT execute tool.
- Grounded answer failure MUST abstain; không trả raw draft.

## 8. Prompt change lifecycle

1. Author tạo version mới; không sửa nội dung của version đã approved.
2. Chạy static checks: manifest, variables, forbidden tokens, schema refs, hash.
3. Chạy targeted eval và full regression dataset.
4. Security review nếu thay instruction hierarchy, tool availability, memory hoặc sensitive handling.
5. Knowledge review nếu thay citation/evidence language.
6. Approver đổi status.
7. Deploy bằng feature flag/canary; ghi prompt version trong mọi trace.
8. Rollback chỉ đổi active version pointer; không xóa version cũ.

Thay typo có thể là editorial; thay câu có khả năng đổi output hoặc safety MUST được phân loại behavioral/security theo `DOCUMENT_CONTROL.md`.

## 9. Static lint rules

Prompt build MUST fail nếu:

- thiếu manifest/header hoặc schema ref;
- chứa secret pattern hoặc real student identifier;
- có câu cho phép model bỏ qua policy/tool broker;
- yêu cầu model tự xác định quyền;
- dùng URL/contact/SLA hard-code chưa có approved source/config;
- output machine-consumed nhưng không có schema;
- cho phép citation ngoài candidate allowlist;
- context budget có thể vượt route limit;
- version/hash không khớp content;
- eval coverage bắt buộc chưa khai báo.

## 10. Acceptance evidence

- prompt manifest schema validation;
- variable fuzz tests và injection-boundary tests;
- structured-output parser tests;
- snapshot của rendered prompt với canary redaction;
- eval before/after report theo version;
- evidence không có secret/PII;
- rollback test;
- trace chứng minh exact prompt version/hash và output schema version.

## 11. Security basis

OWASP nêu prompt injection có thể trực tiếp hoặc gián tiếp từ nguồn bên ngoài và có thể gây truy cập chức năng trái phép hoặc rò rỉ dữ liệu. Delimiter/prompt wording không đủ; thiết kế MUST kết hợp least privilege, tool authorization, validation, monitoring và human approval. Tham chiếu [OWASP LLM01:2025](https://genai.owasp.org/llmrisk/llm01-prompt-injection/) (`SRC-OWASP-001`).

