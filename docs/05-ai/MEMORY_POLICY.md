---
document_id: "DOC-AI-005"
version: "1.0.0"
status: "reviewed"
owner: "AI Architecture Lead"
approvers: ["Privacy Officer", "Security Architect", "AI Quality Lead"]
last_updated: "2026-09-21"
---

# Conversation memory policy

## 1. Mục tiêu

Memory phục vụ continuity tối thiểu, không biến hội thoại thành hồ sơ sinh viên không kiểm soát. Knowledge base, graph checkpoint, transcript, durable user preference và operational audit là các data domain riêng; implementation MUST không trộn chúng.

## 2. Memory classes

| Class | Nội dung | Scope | Retention V1 | Cho vào prompt |
|---|---|---|---|---|
| `turn_buffer` | Một số turn gần nhất đã redaction | conversation | đến khi summarize/90 ngày tối đa | Bounded |
| `graph_checkpoint` | State cần resume | thread | theo workflow + tối đa 90 ngày mô phỏng | Chỉ field cần node |
| `conversation_summary` | Tóm tắt factual tối thiểu | conversation | 90 ngày mặc định (`ASM-007`) | Bounded |
| `pending_action` | Preview/token refs, không raw secret | actor+conversation | đến expire/complete + audit refs | Chỉ action flow |
| `durable_preference` | locale/accessibility preference đã consent | actor | configurable; user can delete | Chỉ khi relevant |
| `knowledge` | Approved institutional content | global authorized scope | theo source governance | Qua RAG only |
| `audit` | Security/business event metadata | policy-defined | `OQ-006` chưa chốt | Không đưa vào prompt |

V1 MUST NOT tự động ghi “long-term memory” từ nội dung chat ngoài allowlisted preferences. Personal facts, sức khỏe, tâm lý, kỷ luật, tài chính, điểm, credential và inferred attributes MUST NOT vào durable memory.

## 3. Write policy

Memory write MUST có:

- `memory_type` allowlisted;
- trusted `actor_id` và scope;
- source turn/reference;
- purpose code;
- privacy class;
- created/expiry timestamp;
- provenance (`user_explicit`, `tool_verified`, `system_generated`);
- confidence chỉ cho summary/extraction, không biến inference thành fact;
- policy version.

Durable preference chỉ được ghi khi user explicit yêu cầu hoặc UI setting xác nhận. Model MAY đề xuất candidate; deterministic policy quyết định và application thực hiện. Memory write không được là hidden side effect của answer generation.

## 4. Context construction

Thứ tự:

1. Load trusted route/policy context.
2. Chọn tối đa N recent turns theo token budget và same actor/conversation.
3. Load summary đã qua schema validation.
4. Load allowlisted preferences relevant.
5. Remove superseded/expired facts.
6. Redact PII không cần thiết.
7. Label mọi user/history content là untrusted.
8. Ghi `context_manifest` gồm memory item IDs và token counts.

Không dùng vector similarity trên toàn bộ conversation archive để đưa ngẫu nhiên personal content vào prompt. Cross-conversation retrieval MUST bị tắt trong V1 trừ durable preference allowlist.

## 5. Summary contract

`ConversationSummary` MUST gồm:

```yaml
summary_version: "1.0"
conversation_id: "uuid"
covered_through_turn_id: "uuid"
user_goals: ["bounded string"]
confirmed_facts:
  - value: "bounded string"
    provenance: "user_explicit|tool_verified"
    source_turn_id: "uuid"
open_questions: ["bounded string"]
pending_action_refs: ["uuid"]
excluded_sensitive_categories: ["reason code"]
```

Summary MUST NOT chứa password/token, full student profile, unsupported inference, raw sensitive disclosure, chain-of-thought hoặc copied institutional policy. Policy facts được truy hồi lại từ RAG để nhận phiên bản hiện hành.

## 6. Isolation và deletion

- Mọi read MUST filter bằng trusted `actor_id` và authorization; model-supplied ID bị bỏ qua.
- Conversation sharing/impersonation nằm ngoài V1.
- Deletion request MUST delete/anonymize user-facing memory theo privacy policy nhưng preserve minimum legal/security audit only when approved policy requires.
- Deletion job MUST emit evidence counts và tombstone; prompt context builder MUST honor tombstone immediately.
- Backup deletion semantics là open decision thuộc privacy/platform; production launch blocked bởi `OQ-006`.

## 7. Failure behavior

| Failure | Behavior |
|---|---|
| Memory store unavailable | Tiếp tục stateless nếu route an toàn; pending write action MUST không execute nếu confirmation context không verify. |
| Summary invalid | Ignore summary, use bounded recent turns; log validation metric. |
| Ownership mismatch | Deny without revealing existence; security event. |
| Retention expired | Exclude immediately; async physical deletion per policy. |
| Context budget exceeded | Deterministic truncate oldest non-essential items; never truncate system policy or active confirmation data. |
| Sensitive content detected | Exclude from durable memory; safety route vẫn nhận bounded current disclosure. |

## 8. Acceptance evidence

- isolation negative tests giữa hai synthetic students;
- no-cross-conversation retrieval test;
- summary schema/factuality tests;
- sensitive-category non-persistence tests;
- retention/expiry/deletion/tombstone tests;
- context token-budget tests;
- restart/resume test cho pending action;
- telemetry inspection chứng minh raw memory không bị log.

## 9. Nguồn

[LangGraph Persistence](https://docs.langchain.com/oss/python/langgraph/persistence) phân biệt checkpointer cho short-term thread state và store cho cross-thread application data; thiết kế này áp dụng sự phân tách đó và thêm privacy constraints của Campus 24/7 (`SRC-LANGGRAPH-001`).

