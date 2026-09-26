---
document_id: "DOC-AI-002"
version: "1.0.0"
status: "reviewed"
owner: "AI Architecture Lead"
approvers: ["Solution Architect", "Backend Lead", "Security Architect", "AI Quality Lead"]
last_updated: "2026-09-21"
---

# Controlled LangGraph state machine

## 1. Nguyên tắc

Graph là workflow hữu hạn, typed và allowlisted. Model MAY đề xuất intent hoặc tool candidate nhưng MUST NOT chọn node tùy ý, tạo node động, sửa state schema hoặc bỏ qua policy gate. Mỗi transition được code bằng deterministic router dựa trên validated fields.

`thread_id` là UUID do server cấp. Production MUST dùng persistent checkpointer. In-memory saver chỉ được dùng trong unit/local tests. LangGraph lưu checkpoint để resume interrupt; tài liệu chính thức lưu ý node chứa `interrupt()` sẽ chạy lại từ đầu khi resume, vì vậy mọi code trước interrupt MUST không có side effect hoặc MUST idempotent. Xem [LangGraph interrupts](https://docs.langchain.com/oss/python/langgraph/interrupts) (`SRC-LANGGRAPH-002`).

## 2. Typed state contract

Implementation MUST định nghĩa `AgentState` tương đương chính xác các nhóm field dưới đây. Field optional MUST có default rõ ràng; không dùng untyped `dict[str, Any]` làm state công khai.

| Field | Type | Owner | Quy tắc |
|---|---|---|---|
| `schema_version` | literal `"1.0"` | graph | Reject version khác. |
| `request` | `NormalizedTurn` | input normalizer | Immutable sau `normalize_input`. |
| `trusted_context_ref` | opaque string | application | Chỉ là reference; không serialize claims nhạy cảm vào prompt. |
| `route` | enum/null | intent router | Chỉ một trong route allowlist. |
| `safety` | `SafetyDecision` | safety gate | Append-only decision history. |
| `retrieval` | `RetrievalState`/null | RAG service | Chứa IDs/scores, không chứa toàn bộ document vượt budget. |
| `draft` | `DraftResponse`/null | composer | Untrusted cho đến output/evidence gate. |
| `tool_candidate` | `ToolCandidate`/null | model/deterministic router | Arguments chưa trusted. |
| `tool_flow` | `ToolFlowState`/null | tool broker | Preview/confirmation/execution state. |
| `handover` | `HandoverState`/null | handover node | Dữ liệu tối thiểu cần thiết. |
| `attempts` | typed counters | graph | Mỗi node có hard max. |
| `errors` | list `SafeError` | graph | Không chứa secret/stack/raw provider body. |
| `terminal` | enum/null | graph | Một khi set thì state immutable trừ telemetry finalization. |
| `versions` | `ExecutionVersions` | application | Prompt/model/policy/tool/retrieval versions. |

### 2.1 Enum bắt buộc

```text
Route = grounded_faq | personal_schedule | ticket_create |
        document_request | room_booking | human_handover |
        sensitive_case | unsupported

Terminal = answered | abstained | completed | cancelled |
           handed_over | safe_failure

ToolPhase = none | candidate | validated | authorized | previewed |
            awaiting_confirmation | confirmed | executing |
            succeeded | failed | uncertain
```

## 3. Node registry

| Node ID | Input precondition | Trách nhiệm duy nhất | Output | Max attempts |
|---|---|---|---|---:|
| AI-NODE-001 `normalize_input` | request exists | Unicode normalization, limits, locale, correlation | normalized request | 1 |
| AI-NODE-002 `pre_safety_rules` | normalized | deterministic PII/injection/sensitive signals | preliminary safety | 1 |
| AI-NODE-003 `sensitive_classifier` | bounded context | typed classifier decision | safety candidate | 2 incl. repair |
| AI-NODE-004 `merge_safety` | rules + classifier | chọn mức severity cao hơn | final safety | 1 |
| AI-NODE-005 `route_intent` | safety allows | route typed intent | route | 2 incl. repair |
| AI-NODE-006 `retrieve_evidence` | route FAQ | hybrid retrieval | evidence candidates | 1 |
| AI-NODE-007 `rerank_evidence` | candidates | rerank bounded set | evidence bundle | 1 provider + fallback |
| AI-NODE-008 `compose_grounded` | evidence bundle | draft answer with claim-citation mapping | draft | 2 incl. repair |
| AI-NODE-009 `evidence_gate` | draft | deterministic validation | supported draft/abstain | 1 |
| AI-NODE-010 `prepare_tool_candidate` | tool route | typed argument candidate | candidate | 2 incl. repair |
| AI-NODE-011 `authorize_tool` | schema-valid candidate | deterministic authorization | authorized/denied | 1 |
| AI-NODE-012 `execute_read_tool` | read + authorized | execute bounded read | result/error | theo registry |
| AI-NODE-013 `build_action_preview` | write + authorized | normalize payload, hash, preview | preview | 1 |
| AI-NODE-014 `await_confirmation` | preview exists | `interrupt()` với serializable payload | confirm/reject/expire | 1 interrupt cycle |
| AI-NODE-015 `revalidate_confirmation` | resume | bind actor/payload/policy/expiry | confirmed/rejected | 1 |
| AI-NODE-016 `execute_write_tool` | confirmed | idempotent execute | result/uncertain/error | theo registry |
| AI-NODE-017 `compose_tool_response` | safe tool outcome | user-facing response | draft | 2 incl. repair |
| AI-NODE-018 `prepare_handover` | handover route | minimal safe summary + reason | handover candidate | 1 |
| AI-NODE-019 `execute_handover` | authorized candidate | idempotent queue write | handover result | theo registry |
| AI-NODE-020 `output_guard` | any response draft | leakage, unsupported claim, unsafe phrasing check | final response | 1 |
| AI-NODE-021 `finalize` | terminal candidate | metrics + audit completion | terminal | 1 |

Không node nào MAY gọi trực tiếp node khác. Node trả typed state delta hoặc typed `Command`; graph definition sở hữu transitions.

## 4. Transition table

| From | Condition | To | Nếu condition không hợp lệ |
|---|---|---|---|
| `START` | request present | `normalize_input` | `safe_failure` |
| `normalize_input` | valid | `pre_safety_rules` | `safe_failure` |
| `pre_safety_rules` | always | `sensitive_classifier` | n/a |
| `sensitive_classifier` | valid/fallback | `merge_safety` | deterministic conservative decision |
| `merge_safety` | `critical|high` | `prepare_handover` | n/a |
| `merge_safety` | `normal` | `route_intent` | n/a |
| `route_intent` | `grounded_faq` | `retrieve_evidence` | n/a |
| `route_intent` | read/write tool route | `prepare_tool_candidate` | n/a |
| `route_intent` | handover | `prepare_handover` | n/a |
| `route_intent` | unsupported | `output_guard` with abstention | n/a |
| `retrieve_evidence` | candidates sufficient | `rerank_evidence` | `output_guard` with abstention |
| `rerank_evidence` | bundle sufficient | `compose_grounded` | `output_guard` with abstention |
| `compose_grounded` | schema valid | `evidence_gate` | repair once then abstain |
| `evidence_gate` | all material claims supported | `output_guard` | abstain or remove unsupported claims then recheck once |
| `prepare_tool_candidate` | valid | `authorize_tool` | bounded clarification/abstain |
| `authorize_tool` | deny | `output_guard` | n/a |
| `authorize_tool` | read allow | `execute_read_tool` | n/a |
| `authorize_tool` | write allow | `build_action_preview` | n/a |
| `build_action_preview` | preview valid | `await_confirmation` | `safe_failure` |
| `await_confirmation` | resume | `revalidate_confirmation` | remains interrupted |
| `revalidate_confirmation` | approve + valid | `execute_write_tool` | `cancelled` or new preview required |
| tool execution | known result | `compose_tool_response` | n/a |
| write execution | uncertain | `prepare_handover` | MUST NOT retry blindly |
| `prepare_handover` | valid | `execute_handover` | safe response with official configured channels only |
| any response draft | exists | `output_guard` | safe template |
| `output_guard` | pass | `finalize` | safe template/handover |
| `finalize` | terminal set | `END` | fail closed |

## 5. Confirmation interrupt

Interrupt payload MUST chỉ chứa dữ liệu JSON-serializable và không chứa secret:

```yaml
interrupt_type: "action_confirmation"
preview_id: "uuid"
tool_id: "ticket_create"
summary_lines: ["..."]
payload_hash: "sha256:..."
expires_at: "RFC3339"
allowed_decisions: ["approve", "reject"]
```

Resume payload MUST gồm `preview_id`, `decision` và opaque `confirmation_token`. Khi resume, node bắt đầu lại; do đó `await_confirmation` MUST không ghi business data trước `interrupt()`. `revalidate_confirmation` MUST kiểm tra:

1. token signature và expiry;
2. actor/session binding;
3. exact normalized payload hash;
4. tool contract version;
5. policy version hoặc thực hiện re-authorization nếu policy đổi;
6. preview chưa bị consume/cancel.

Nếu bất kỳ kiểm tra nào fail, graph MUST NOT execute. Payload thay đổi dù chỉ một field MUST tạo preview/token/idempotency key mới.

## 6. Retry, resume và side effects

- LLM call read-only MAY retry theo routing policy khi timeout/transient error; retry dùng cùng `request_id` và tăng `attempt`.
- Read tool MAY retry nếu registry đánh dấu `retry_safe: true`.
- Write tool MUST dùng idempotency key trước lần gọi đầu tiên. Chỉ retry khi adapter contract đảm bảo cùng key trả cùng logical result.
- Nếu upstream timeout sau khi có thể đã ghi và không có endpoint reconciliation, trạng thái MUST là `uncertain`; graph MUST handover, không gọi lại với key khác.
- Sau process restart, resume MUST dùng cùng `thread_id`, load checkpoint và revalidate token/policy trước side effect.
- Terminal state MUST ngăn mọi node nghiệp vụ chạy lại. Duplicate delivery chỉ được finalize telemetry idempotently.

## 7. Bounded execution

| Giới hạn | Giá trị V1 |
|---|---:|
| Tổng graph steps/turn | 24 |
| LLM calls/turn thông thường | 4 |
| LLM calls/turn có tool | 5 |
| Tool candidates/turn | 1 write hoặc tối đa 3 read độc lập |
| Clarification turns cho một action | 2 |
| Structured-output repair | 1/call |
| Retrieval rewrite | 1 |
| Evidence draft revision | 1 |

Vượt giới hạn MUST chuyển `abstained` hoặc `handed_over`, không tự tăng budget.

## 8. Concurrency

- Một `conversation_id` chỉ có tối đa một write-action flow đang `executing`.
- Hai turn cạnh tranh trên cùng conversation MUST dùng optimistic version/checkpoint conflict detection.
- Read-only turns MAY song song nếu không thay đổi memory, nhưng response ordering MUST gắn `turn_id`.
- Pending confirmation MUST không chặn câu hỏi read-only mới, nhưng confirmation resume MUST tham chiếu đúng `preview_id`.
- Handover creation và write action khác MUST không chạy song song cho cùng sensitive event.

## 9. Acceptance evidence

Implementation chỉ đạt khi có:

- state-schema typecheck;
- transition-table tests cho từng dòng và forbidden transition tests;
- property test chứng minh terminal state không phát sinh side effect;
- restart/resume test ở trước/sau interrupt;
- duplicate confirmation test;
- expired, wrong actor, altered payload và stale policy token tests;
- write-timeout uncertain outcome test;
- max-step/max-call budget tests;
- checkpoint retention và redaction inspection;
- trace cho mỗi node gồm `node_id`, start/end, outcome, version, không chứa chain-of-thought.

## 10. Nguồn chính thức

- [LangGraph Persistence](https://docs.langchain.com/oss/python/langgraph/persistence) mô tả checkpointer cho thread-scoped state, store cho cross-thread memory và yêu cầu persistent saver ở production (`SRC-LANGGRAPH-001`).
- [LangGraph Interrupts](https://docs.langchain.com/oss/python/langgraph/interrupts) mô tả pause/resume bằng cùng `thread_id`, JSON-serializable payload và việc node chạy lại từ đầu khi resume (`SRC-LANGGRAPH-002`).

