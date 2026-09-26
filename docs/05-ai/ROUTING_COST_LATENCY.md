---
document_id: "DOC-AI-007"
version: "1.0.0"
status: "reviewed"
owner: "AI Platform Lead"
approvers: ["AI Architecture Lead", "SRE Lead", "Product Owner", "Finance Owner"]
last_updated: "2026-09-21"
---

# Model routing, cost và latency policy

## 1. Nguyên tắc

Routing là deterministic policy dựa trên route, risk, capability, quality gate, deadline và budget. Model không tự chọn model/provider. Giá provider thay đổi theo thời gian nên MUST nằm trong versioned price registry có nguồn/effective date; tài liệu này không hard-code giá.

## 2. Logical model profiles

| Profile | Dùng cho | Yêu cầu |
|---|---|---|
| `classifier_fast` | intent/safety candidate | structured output, low latency, calibrated recall |
| `rewrite_fast` | bounded query rewrite | structured output, exact-token preservation |
| `reranker_balanced` | rerank ≤20 chunks | ordered-ID output, Vietnamese quality |
| `answer_balanced` | grounded answer/tool response | structured output, citation discipline |
| `reasoning_strong` | only approved complex policy synthesis | higher quality gate; no direct tools |
| `fake_deterministic` | all default tests | no network, fixture-driven |

DeepSeek model IDs được map vào profile qua config. Thêm provider/model mới cần capability + eval + cost/latency evidence, không sửa domain route.

## 3. Route budgets V1

| Route | LLM calls max | End-to-end target | Provider total deadline | Behavior khi quá budget |
|---|---:|---:|---:|---|
| `grounded_faq` | 4 | P95 ≤6s | 4.5s aggregate | lexical/RRF fallback hoặc abstain |
| `personal_schedule` | 2 | P95 ≤4s | 2.5s | deterministic tool result template |
| `ticket_create` | 3 trước confirm + 1 sau | P95 ≤10s excluding human wait | 6s | preserve draft/preview, no execute |
| `document_request` | như ticket | P95 ≤10s excluding wait | 6s | như trên |
| `room_booking` | 4 | P95 ≤10s excluding wait | 6s | show deterministic conflict/result |
| `sensitive_case` | 1 classifier | queue delivery P95 ≤5s | 1.5s | deterministic rule + handover |
| `unsupported` | 1 | P95 ≤3s | 1.5s | deterministic clarification/abstain |

Target SLO cuối phải đồng bộ platform SLO; mismatch phải tạo blocker, không tự chọn số khác.

## 4. Token/context budgets

Mỗi model profile registry MUST chỉ rõ context limit được provider xác minh. Route budget phân bổ baseline:

- system/task/output contract: ≤15% context;
- conversation/history: ≤20%;
- evidence/tool results: ≤50%;
- current request: ≤5%;
- reserved output/headroom: ≥10%.

Nếu vượt, deterministic context builder giảm theo thứ tự: duplicate evidence → old turns → nonessential metadata → lower-ranked evidence. MUST NOT truncate active policy, output schema, current user request, critical safety context hoặc action confirmation fields.

## 5. Cost accounting

Mỗi provider call MUST ghi:

```text
provider_id, model_id, price_registry_version,
input_tokens, cached_input_tokens, output_tokens, reasoning_tokens_if_billed,
estimated_cost_currency, route_id, request_id, success/failure
```

Formula được price registry định nghĩa theo billing unit/effective date. Cached/reasoning token chỉ áp dụng khi provider docs và invoice semantics xác nhận. Unknown usage MUST được đánh dấu `cost_unverified`, không tính bằng zero.

Aggregates bắt buộc:

- cost/request, cost/resolved session, cost/answered grounded FAQ;
- cost theo route/model/provider/prompt version;
- wasted cost từ invalid output/retry/abstention;
- token and cache-hit distributions;
- monthly projection và budget utilization.

## 6. Budget controls

- Cấu hình hard monthly budget và optional per-actor/per-route quota; `OQ-008` phải chốt trước production.
- Alerts mặc định tại 50%, 75%, 90%; hard-stop tại 100% trừ reserved safety/handover budget đã approved.
- Budget check trước provider call; race-safe reservation cho concurrent calls.
- Không tự động vượt budget.
- Khi 90%: ưu tiên fast/balanced profiles đã đạt quality gate, giảm nonessential rewrite/rerank; không giảm safety/evidence/authorization gates.
- Khi hard-stop: `search_only`/`ticket_only`; deterministic safety và handover vẫn hoạt động nếu không cần LLM.

## 7. Model selection rule

1. Route xác định required capabilities/risk tier.
2. Loại model không đạt offline quality/safety gate.
3. Loại model unhealthy, over budget, privacy-ineligible hoặc capability mismatch.
4. Chọn model có projected latency đáp ứng deadline và expected cost thấp nhất trong tập còn lại.
5. Nếu không còn model, dùng deterministic fallback; không bypass gate.

Quality-first: model rẻ hơn chỉ được activate sau khi đạt cùng hard gates; aggregate quality giảm ngoài non-inferiority margin đã phê duyệt thì rollback.

## 8. Degradation matrix

| Failure | Mode |
|---|---|
| DeepSeek unavailable | Approved secondary model nếu có; nếu không search/ticket-only. |
| Classifier model unavailable | deterministic safety rules, conservative high-risk route. |
| Reranker unavailable | RRF order. |
| Answer model unavailable | show extractive evidence snippets với citation hoặc ticket; không synthesize unsupported answer. |
| Embedding unavailable during query | lexical-only nếu metadata/evidence gates healthy. |
| Token budget exceeded | deterministic context reduction; sau đó abstain. |
| Monthly cost hard-stop | no optional LLM calls; preserve deterministic service. |
| Telemetry/cost accounting unavailable | fail closed for paid calls nếu reservation/accounting không đảm bảo. |

## 9. Acceptance evidence

- route-to-profile decision-table tests;
- capability mismatch tests;
- token truncation priority tests;
- budget reservation race tests;
- alert/hard-stop tests;
- cost formula tests với versioned fixtures/invoice samples;
- latency load test theo `ASM-001/002`;
- degradation chaos tests;
- quality non-inferiority report trước chuyển model/profile.

## 10. Nguồn

DeepSeek official Responses API cung cấp usage fields gồm input/output và chi tiết cached/reasoning tokens; compatibility có thể khác theo parameter, do đó adapter/price registry phải re-verify: [DeepSeek Responses API](https://api-docs.deepseek.com/guides/responses_api/) và [reference](https://api-docs.deepseek.com/api/create-response/).

