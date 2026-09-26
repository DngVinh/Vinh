---
document_id: "DOC-ADR-006"
version: "1.0.0"
status: "draft"
owner: "AI Architecture Lead"
approvers: ["Architecture Lead", "AI Quality Lead", "Security Lead"]
last_updated: "2026-09-21"
decision_status: "proposed"
---

# ADR-006 — Controlled LangGraph workflow thay autonomous multi-agent

## Context

Hệ thống cần multi-step conversation, retrieval, tool proposal, confirmation và HITL resume. Autonomous multi-agent làm tăng nondeterminism, cost và khó chứng minh authorization/safety. LangGraph cung cấp checkpoint và interrupt semantics phù hợp nhưng side effects quanh resume phải được kiểm soát.

## Decision

Một explicit LangGraph state machine **MUST** điều phối request-time AI. Graph có named nodes/transitions được review; không dynamic agent spawning. Deterministic code quyết định authentication, emergency rules, authorization, evidence, confirmation và execution. LLM chỉ classify/propose/draft trong schema.

Durable production checkpoints dùng PostgreSQL-compatible persistence. `thread_id` là opaque bounded identifier, không chứa PII. HITL dùng interrupt/resume với idempotent side effects.

## Alternatives

- Free-form ReAct/multi-agent: từ chối vì model có quá nhiều control authority.
- Handwritten ad-hoc loop: từ chối vì persistence/resume/inspection khó chuẩn hóa.
- Fully deterministic bot: không đáp ứng language/reasoning use case nhưng là degradation fallback.

## Consequences

Workflow testable/auditable, đổi lại cần versioning graph state, checkpoint migration và explicit node contracts. Graph complexity phải giữ nhỏ; business logic nằm ngoài nodes.

## Constraints

- Node **MUST NOT** direct SQL/HTTP/provider SDK.
- Transition **MUST** dựa typed state/code, không parse prose.
- Graph version **MUST** được lưu với checkpoint.
- Resume incompatible version **MUST** migrate hoặc handover, không guess.
- LLM **MUST NOT** chọn unrestricted next node.
- Side effect trước interrupt/resume **MUST** idempotent.

## Acceptance and failure

State-transition tests phải cover every edge, interrupt, duplicate resume, invalid state, provider timeout và checkpoint recovery. In-memory saver chỉ dùng test/local. LangGraph documents checkpointer persistence and interrupt resume behavior at `SRC-LANGGRAPH-001` and `SRC-LANGGRAPH-002`.

Nếu graph state contract thiếu version hoặc task yêu cầu dynamic agent, agent **MUST** stop và request ADR/change review.

Traceability: `DEC-014`–`DEC-016`, `ARCH-003`, `ARCH-006`.

