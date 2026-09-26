---
document_id: "DOC-AI-001"
version: "1.0.0"
status: "reviewed"
owner: "AI Architecture Lead"
approvers: ["Solution Architect", "AI Quality Lead", "Security Architect", "Product Owner"]
last_updated: "2026-09-21"
---

# Đặc tả hệ thống AI

## 1. Mục tiêu

Campus 24/7 cung cấp trợ lý dịch vụ sinh viên có căn cứ, có thể tra cứu dữ liệu cá nhân và đề xuất hành động trong phạm vi quyền. AI là một thành phần lập kế hoạch/ngôn ngữ bị kiểm soát, không phải nguồn sự thật, policy engine hoặc actor có quyền.

Thiết kế này thực thi `DEC-008`, `DEC-012` đến `DEC-016` và chỉ dùng dữ liệu tổng hợp theo `DEC-004`.

## 2. Invariant bắt buộc

| ID | Quy tắc chuẩn tắc | Failure behavior | Evidence tối thiểu |
|---|---|---|---|
| AI-SYS-001 | Mọi assertion về quy định, thủ tục, thời hạn, phí, điều kiện hoặc đơn vị xử lý MUST có ít nhất một citation đã qua `EvidenceGate`. | Abstain hoặc hỏi một câu làm rõ có giới hạn; MAY đề nghị ticket/handover. | Eval citation + trace của evidence gate. |
| AI-SYS-002 | LLM MUST NOT truy cập database, HTTP integration, filesystem, secret hoặc message queue trực tiếp. | Tool broker từ chối capability không đăng ký. | Dependency test chứng minh domain graph chỉ gọi gateway/tool interfaces. |
| AI-SYS-003 | Authorization MUST được tính deterministic từ trusted identity context và resource attributes; model output MUST NOT cấp quyền. | Trả `authorization_denied`; không reveal resource existence ngoài policy. | Negative authorization tests. |
| AI-SYS-004 | Mọi write action MUST có preview, explicit confirmation còn hạn và idempotency key trước execute. | Route `awaiting_confirmation`, `cancelled` hoặc `safe_failure`; không side effect. | Audit chain preview→confirm→execute. |
| AI-SYS-005 | Tình huống sensitive/emergency MUST qua rule engine và classifier song song trước route thông thường. | Chọn mức rủi ro cao hơn; ưu tiên handover. | Safety eval theo `EVAL-SAFE-*`. |
| AI-SYS-006 | Mọi LLM output dùng cho routing, tool arguments, safety hoặc citation MUST validate bằng JSON Schema; additional fields MUST bị từ chối. | Một repair attempt không side effect; sau đó deterministic fallback. | Schema-fuzz tests. |
| AI-SYS-007 | Tests MUST dùng `DeterministicFakeProvider` theo mặc định và MUST không phụ thuộc network, clock thật hoặc output ngẫu nhiên. | CI fail nếu phát hiện provider network call. | Hermetic test report. |
| AI-SYS-008 | Provider, model, prompt version, retrieval version, tool contract version và policy version MUST xuất hiện trong trace. | Request MAY hoàn thành an toàn nhưng bị đánh dấu telemetry defect; release gate fail. | Trace completeness metric. |
| AI-SYS-009 | Hệ thống MUST có chế độ `search_only` và `ticket_only` không cần LLM khi provider hoặc guardrail không khả dụng. | Degrade theo `ROUTING_COST_LATENCY.md`; không giả vờ AI vẫn hoạt động. | Chaos/failover test. |
| AI-SYS-010 | Nội dung retrieved, tool result và user input đều là untrusted data; chúng MUST NOT thay đổi system policy hoặc tool registry. | Bỏ qua instruction trong data, ghi injection signal và tiếp tục/abstain. | Red-team cases. |
| AI-SYS-011 | Chain-of-thought/reasoning nội bộ từ provider MUST NOT được lưu, hiển thị hoặc dùng làm audit evidence. | Chỉ lưu normalized outcome, reason code, usage và safe rationale ngắn. | Log inspection. |
| AI-SYS-012 | Không được tuyên bố Campus 24/7 là dịch vụ chính thức của HUCE trong bản mô phỏng. | UI/response chèn simulation notice theo product contract. | Snapshot/content test. |

## 3. Phân chia deterministic và model-based

### 3.1 Bắt buộc deterministic

- xác thực danh tính và lấy roles/attributes;
- authorization và resource ownership;
- validate JSON Schema;
- metadata filter theo hiệu lực, audience, faculty và publication status;
- confirmation token, expiry và payload hash;
- idempotency, transaction và side-effect execution;
- rate limit, budget hard-stop, timeout, retry và circuit breaker;
- citation existence, source/version/effective-date checks;
- audit event và metrics calculation;
- kill switch, degraded mode và emergency-contact configuration check.

### 3.2 Có thể dùng model, nhưng phải bị chặn bằng contract

- intent classification;
- query rewrite không làm thay đổi semantic constraints;
- reranking;
- grounded answer composition;
- extraction of candidate tool arguments;
- conversation summary;
- sensitive-case classifier thứ hai sau deterministic rules;
- LLM-as-judge trong exploratory evaluation, không phải sole release gate.

### 3.3 Không thuộc phạm vi AI

- quyết định học vụ, kỷ luật, tài chính hoặc y tế;
- phê duyệt giấy tờ, phòng học hoặc ngoại lệ;
- tự gọi cơ quan khẩn cấp;
- thay đổi điểm, hồ sơ, quyền, cấu hình policy hoặc knowledge publication;
- tự tạo số điện thoại, email, SLA hoặc quy định chưa có nguồn.

## 4. Component model

```text
Trusted Request Context
  -> Input Normalizer
  -> PII/Injection/Sensitive Rules
  -> Controlled Agent Graph
       -> RAG Service -> Evidence Gate
       -> LLM Gateway -> DeepSeekAdapter | DeterministicFakeProvider
       -> Tool Broker -> Policy Engine -> Domain Adapters
       -> HITL Queue
  -> Output Guard
  -> Response + Citations
  -> Audit/Telemetry (redacted)
```

### 4.1 Interface boundaries

| Component | Nhận | Trả | MUST NOT |
|---|---|---|---|
| `InputNormalizer` | raw UTF-8 text, locale | normalized text + signals | Không xóa nội dung làm thay đổi ý định; không cấp quyền. |
| `SensitiveCaseGate` | normalized text, bounded history | severity, labels, confidence, reason codes | Không chẩn đoán hoặc gọi tool write. |
| `RagService` | query + trusted audience filters | evidence bundle | Không nhận `actor_role` từ LLM; không trả unpublished content. |
| `LlmGateway` | typed normalized request | typed response/tool candidates | Không giữ conversation state ở provider; không execute tool. |
| `ToolBroker` | validated candidate + trusted context | preview/result/error | Không tin actor/scope do model gửi. |
| `EvidenceGate` | claims + evidence bundle | supported/unsupported claim map | Không cho citation chỉ “có vẻ liên quan” qua gate. |
| `OutputGuard` | draft response + decisions | safe response | Không thêm policy fact mới. |

## 5. Các luồng V1

| Intent class | Route chuẩn | Model role | Terminal outcome |
|---|---|---|---|
| `grounded_faq` | classify → retrieve → rerank → draft → evidence gate | rewrite, rerank, compose | `answered` hoặc `abstained` |
| `personal_schedule` | classify → authorize → read tool → compose | extract bounded date range, compose | `answered` hoặc `safe_failure` |
| `ticket_create` | classify → collect → preview → interrupt → execute | extract draft fields | `completed`, `cancelled`, `handover` |
| `document_request` | như write tool | extract request type/reason | `completed`, `cancelled`, `handover` |
| `room_booking` | search read tool → draft → preview → interrupt → execute | extract constraints, explain conflict | `completed`, `cancelled`, `safe_failure` |
| `human_handover` | classify/rule → summarize → create handover | safe summary only | `handed_over` |
| `sensitive_case` | rule + classifier → guardrail response → handover | classifier and approved response template selection | `handed_over` hoặc `safe_response` |
| `unsupported` | bounded clarification or abstain | classify | `abstained` |

## 6. Request lifecycle và correlation

Mỗi turn MUST có:

- `request_id`: UUID mới cho HTTP/message request;
- `conversation_id`: UUID ổn định trong hội thoại;
- `thread_id`: UUID tương ứng LangGraph checkpoint, tối đa 255 ký tự;
- `turn_id`: UUID mới cho user turn;
- `actor_id`: lấy từ trusted identity context, không đưa vào prompt nếu không cần;
- `policy_version`, `prompt_bundle_version`, `tool_registry_version`;
- `provider_id`, `model_id`, `retrieval_profile_id` khi có dùng;
- `trace_id` và `audit_correlation_id`.

Raw provider reasoning MUST bị loại trước khi persistence. Provider request/response body đầy đủ MUST NOT được log ở production; chỉ lưu redacted envelope và hash khi cần đối soát.

## 7. Error taxonomy

| Code | Retry | User behavior | Audit |
|---|---:|---|---|
| `AI_INPUT_INVALID` | Không | Yêu cầu sửa input cụ thể. | Metadata, không raw sensitive content. |
| `AI_POLICY_BLOCKED` | Không | Safe refusal/handover. | Policy ID + reason code. |
| `AI_PROVIDER_TIMEOUT` | Tối đa theo routing policy | Degraded mode hoặc thử model đã duyệt. | Latency, attempt, provider. |
| `AI_PROVIDER_INVALID_OUTPUT` | Một repair attempt | Fallback/abstain. | Schema errors, output hash. |
| `AI_RETRIEVAL_INSUFFICIENT` | Không tự lặp vô hạn | Clarify/abstain/ticket. | Candidate counts và gate reasons. |
| `AI_TOOL_AUTHZ_DENIED` | Không | Thông báo không có quyền, không reveal dữ liệu. | Actor, policy decision, tool ID. |
| `AI_CONFIRMATION_REQUIRED` | Không | Hiển thị preview và chờ. | Preview ID, expiry. |
| `AI_TOOL_UNCERTAIN_OUTCOME` | Không tự retry write | Thông báo đang xác minh và handover/reconcile. | Idempotency key + upstream correlation. |
| `AI_BUDGET_EXCEEDED` | Không | Search/ticket-only mode. | Budget dimension. |
| `AI_INTERNAL_ERROR` | Chỉ safe retry | Xin lỗi ngắn, không lộ stack/secret. | Error class + trace. |

## 8. Acceptance evidence hệ thống

Không được đánh dấu gói AI hoàn tất nếu thiếu:

1. component/dependency test chứng minh không có provider SDK trong domain graph hoặc tool broker;
2. state-transition coverage cho mọi edge hợp lệ và edge bị cấm;
3. schema validation tests gồm unknown fields, wrong type, overlength, Unicode và malicious strings;
4. deterministic fake-provider integration suite chạy offline;
5. RAG gold-set report và citation audit;
6. authorization/confirmation/idempotency negative tests;
7. safety + prompt-injection red-team report;
8. cost/latency report theo route;
9. trace sample đã redaction và đủ version fields;
10. failover test cho provider unavailable, retrieval unavailable và tool uncertain outcome.

## 9. Nguồn chính thức

- LangGraph phân biệt checkpointer thread-scoped và store cross-thread; production cần persistent checkpointer: [LangGraph Persistence](https://docs.langchain.com/oss/python/langgraph/persistence) (`SRC-LANGGRAPH-001`).
- DeepSeek yêu cầu ứng dụng validate tool arguments trước khi gọi function; model không tự thực thi function: [DeepSeek Responses API](https://api-docs.deepseek.com/api/create-response/) và [Tool Calls](https://api-docs.deepseek.com/guides/tool_calls/) (`SRC-DEEPSEEK-001`, `SRC-DEEPSEEK-002`).
- Prompt injection có thể dẫn tới truy cập trái phép hoặc rò rỉ dữ liệu và cần defense-in-depth: [OWASP LLM01:2025](https://genai.owasp.org/llmrisk/llm01-prompt-injection/) (`SRC-OWASP-001`).
- Baseline quản trị rủi ro AI tham chiếu [NIST AI RMF 1.0](https://www.nist.gov/publications/artificial-intelligence-risk-management-framework-ai-rmf-10); đây là framework tự nguyện, không phải tuyên bố chứng nhận.

