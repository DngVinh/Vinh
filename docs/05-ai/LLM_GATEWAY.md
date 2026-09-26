---
document_id: "DOC-AI-003"
version: "1.0.0"
status: "reviewed"
owner: "AI Platform Lead"
approvers: ["AI Architecture Lead", "Security Architect", "SRE Lead", "AI Quality Lead"]
last_updated: "2026-09-21"
---

# Provider-neutral LLM gateway

## 1. Mục tiêu và nguyên tắc

`LlmGateway` cô lập domain khỏi SDK, request shape, stream event, error và capability riêng của provider. DeepSeek là provider đầu tiên theo `DEC-008`; đây không phải quyền hard-code DeepSeek vào graph, RAG, prompt hoặc tool domain.

Gateway MUST:

- cung cấp interface typed ổn định;
- chuyển đổi request/response sang canonical contract;
- enforce timeout, token cap, budget, retry, redaction và telemetry;
- validate structured output/tool candidates ở application boundary;
- hỗ trợ deterministic fake provider cho mọi test mặc định;
- fail closed khi capability provider không đáp ứng route.

## 2. Canonical interface

Tên code symbol là chuẩn tắc; ngôn ngữ triển khai có thể dùng protocol/interface tương đương.

```text
LlmGateway.generate(request: LlmRequest) -> LlmResponse
LlmGateway.stream(request: LlmRequest) -> AsyncIterator[LlmEvent]
LlmGateway.capabilities(provider_id, model_id) -> ModelCapabilities
```

### 2.1 `LlmRequest`

| Field | Type | Required | Rule |
|---|---|---:|---|
| `request_id` | UUID | yes | Stable across retry. |
| `route_id` | enum | yes | Must exist in routing registry. |
| `model_profile` | string | yes | Logical profile, not raw provider model from caller. |
| `system_instructions` | string | yes | Rendered from approved prompt bundle. |
| `input_items` | typed list | yes | Bounded, redacted; retrieved/tool data labeled untrusted. |
| `output_schema` | JSON Schema/null | conditional | Required for all machine-consumed outputs. |
| `allowed_tools` | tool definitions | no | Derived from trusted graph state, never user text. |
| `tool_choice` | enum/specific | no | Deterministic route policy chooses. |
| `temperature` | decimal | yes | From model profile; caller cannot override. |
| `max_output_tokens` | positive int | yes | Hard cap from route. |
| `deadline_ms` | positive int | yes | Remaining end-to-end budget, not provider timeout alone. |
| `privacy_class` | enum | yes | `public|internal|personal_redacted`; raw sensitive prohibited. |
| `trace_context` | object | yes | IDs/versions only; no PII. |

Request MUST NOT contain API key, raw authorization token, password, complete student record, unrestricted transcript, chain-of-thought request hoặc provider-specific state ID.

### 2.2 `LlmResponse`

```text
status: completed | incomplete | failed
provider_id: string
model_id: string
provider_request_id: string|null
output_text: string|null
structured_output: object|null
tool_candidates: list[ToolCandidate]
finish_reason: stop | length | content_filter | tool_call | error
usage: {input_tokens, cached_input_tokens, output_tokens, reasoning_tokens?}
latency_ms: integer
attempt: integer
```

Gateway MUST NOT expose provider reasoning text. Nếu provider trả reasoning, adapter MUST discard khỏi application response và logs; chỉ token count MAY được giữ.

### 2.3 `LlmEvent`

Canonical stream event allowlist:

```text
response_started
text_delta
tool_arguments_delta
output_item_completed
usage_final
response_completed
response_incomplete
response_failed
```

Adapter MUST map provider event vào allowlist và reject unknown terminal semantics. Application MUST only display `text_delta` sau khi route cho phép streaming. Grounded policy answers SHOULD buffer đến evidence gate; không stream assertion chưa kiểm chứng.

## 3. Capability registry

Mỗi model version MUST có immutable capability snapshot:

```yaml
provider_id: deepseek
model_id: configured-model-name
effective_from: RFC3339
supports:
  structured_output: true|false
  function_tools: true|false
  streaming: true|false
  images: true|false
  stateless_requests: true|false
limits:
  context_tokens: integer
  max_output_tokens: integer
pricing_ref: "COST registry key"
verified_at: RFC3339
source_url: "official provider URL"
```

Không capability nào được suy đoán từ tên model. Startup MUST validate model profile so với route requirements. Mismatch MUST disable route hoặc chọn fallback đã duyệt; MUST NOT gửi parameter và hy vọng provider xử lý.

## 4. DeepSeek adapter

### 4.1 Baseline

- Base URL, credential và model ID MUST đến từ secret/configuration, không hard-code.
- Adapter SHOULD dùng Responses-compatible API nếu model đã được capability test; compatibility MUST được kiểm tra bằng contract tests.
- DeepSeek Responses API hiện được mô tả là stateless: `previous_response_id` và `conversation` không được hỗ trợ. Vì vậy conversation state MUST do Campus 24/7 quản lý và gửi bounded context mỗi request.
- `function` tools được hỗ trợ nhưng ứng dụng vẫn MUST parse và validate JSON arguments; documentation của provider cảnh báo arguments có thể không phải JSON hợp lệ hoặc có field hallucinated.
- Một số request parameter không hỗ trợ có thể bị bỏ qua im lặng. Adapter MUST không dựa vào provider để enforce `max_tool_calls`, parallel-call policy hoặc state.
- Streaming adapter MUST nhận biết `response.completed`, `response.incomplete`, `response.failed`; MUST NOT chờ sentinel `[DONE]` nếu API không dùng sentinel đó.

Các claim trên phải được re-verify khi cập nhật adapter theo [DeepSeek Responses API guide](https://api-docs.deepseek.com/guides/responses_api/) và [API reference](https://api-docs.deepseek.com/api/create-response/) (`SRC-DEEPSEEK-001`, `SRC-DEEPSEEK-002`).

### 4.2 Normalization rules

| Provider behavior | Canonical behavior |
|---|---|
| Unsupported field bị ignore | Capability layer MUST ngăn gửi field cần thiết nhưng unsupported. |
| Parallel tool call luôn bật/field ignored | Gateway accepts candidates nhưng graph/tool broker serializes write operations và enforces count. |
| Tool arguments là JSON string | Parse strict UTF-8 JSON, validate schema, reject duplicate keys nếu parser hỗ trợ, reject trailing content. |
| Response incomplete do token limit | Không dùng partial machine output; MAY retry một lần với smaller input hoặc route fallback. |
| Content filter/incomplete | Safe template hoặc handover theo route; không tự nối nội dung. |
| Provider returns reasoning text | Discard content; count tokens only. |

## 5. Deterministic fake provider

`DeterministicFakeProvider` là dependency bắt buộc trước DeepSeek adapter. Nó MUST:

- không gọi network;
- map `fixture_key = hash(route_id, prompt_version, normalized_input_fixture)` sang fixture immutable;
- có virtual clock và configured latency;
- phát canonical stream event theo thứ tự deterministic;
- mô phỏng completed, invalid JSON, schema mismatch, timeout, rate limit, partial stream, tool candidate, safety refusal và provider failure;
- ghi request đã redaction để test assertions;
- fail test khi thiếu fixture, không tự sinh câu trả lời;
- hỗ trợ seeded deterministic output khi property test yêu cầu, seed phải xuất trong evidence.

Unit/integration/CI MUST inject fake provider. DeepSeek live tests MUST có marker riêng, default skipped, explicit secret, cost budget và approval; live tests MUST không dùng dữ liệu cá nhân.

## 6. Validation và repair

1. Adapter parse provider response thành canonical response.
2. Gateway reject output vượt byte/token limit hoặc invalid encoding.
3. Nếu `output_schema` có mặt, gateway validate Draft 2020-12.
4. Với validation failure, gateway MAY thực hiện đúng một repair call nếu route cho phép và còn deadline/budget.
5. Repair prompt MUST chỉ chứa schema error đã sanitize và output invalid đã redaction; MUST không thêm tool quyền.
6. Repair failure route về deterministic fallback; MUST không parse “best effort”.
7. Tool candidate luôn qua tool broker; schema-valid không đồng nghĩa authorized.

## 7. Timeout, retry và circuit breaker

| Lớp | Quy tắc |
|---|---|
| Connection | Timeout cấu hình; retry transient tối đa 1 lần với jitter và cùng request ID. |
| First token | Route-specific; nếu quá hạn, cancel provider request nếu có thể. |
| Total generation | Hard deadline; partial structured output bị bỏ. |
| HTTP 429/5xx | Retry chỉ khi còn end-to-end deadline và budget; honor provider retry hint trong cap. |
| HTTP 4xx contract/auth | Không retry; mở operational alert thích hợp. |
| Circuit breaker | Theo provider+model; mở sau threshold đã cấu hình, half-open bằng probe không PII. |
| Fallback | Chỉ model/profile đã approved; không tự chọn model mới. |

Mỗi attempt MUST ghi latency, normalized error class và token usage nếu có. Error logs MUST không chứa secret, raw prompt hoặc raw student data.

## 8. Configuration

Tối thiểu:

```text
LLM_PROVIDER_ID
LLM_BASE_URL
LLM_MODEL_<PROFILE>
LLM_API_KEY_SECRET_REF
LLM_TIMEOUT_CONNECT_MS
LLM_TIMEOUT_TOTAL_MS
LLM_MAX_RETRIES
LLM_CIRCUIT_* 
LLM_PRICE_REGISTRY_VERSION
```

Repository MUST chỉ chứa `.env.example` placeholder ở domain platform, không chứa secret. Startup logs MUST redact URL query, authorization headers và secret refs.

## 9. Contract tests và evidence

| ID | Test bắt buộc |
|---|---|
| AI-GW-001 | Domain graph chỉ phụ thuộc `LlmGateway`, không import provider SDK. |
| AI-GW-002 | Fake provider chạy toàn bộ AI integration suite offline và output lặp lại byte-for-byte. |
| AI-GW-003 | DeepSeek adapter map đủ terminal events và không chờ `[DONE]`. |
| AI-GW-004 | Invalid/unknown tool argument không tới tool adapter. |
| AI-GW-005 | Unsupported required capability làm startup/route readiness fail. |
| AI-GW-006 | Raw provider reasoning không xuất hiện trong DB, log, trace hoặc response. |
| AI-GW-007 | Timeout, 429, 5xx, malformed JSON và incomplete response có failure behavior đúng. |
| AI-GW-008 | Budget hard-stop ngăn request trước network call. |
| AI-GW-009 | PII canary không xuất hiện trong telemetry export. |

Evidence gồm test command/exit code, fixture IDs, request/response canonical snapshots đã redaction, capability snapshot và live-test cost nếu có.

## 10. Nguồn

- [DeepSeek Responses API guide](https://api-docs.deepseek.com/guides/responses_api/).
- [DeepSeek Responses API reference](https://api-docs.deepseek.com/api/create-response/).
- [DeepSeek Tool Calls](https://api-docs.deepseek.com/guides/tool_calls/).
- JSON Schema dùng dialect [Draft 2020-12](https://json-schema.org/draft/2020-12).

