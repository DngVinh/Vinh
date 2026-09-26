---
document_id: "DOC-ADR-007"
version: "1.0.0"
status: "draft"
owner: "AI Platform Lead"
approvers: ["Architecture Lead", "AI Quality Lead", "Security Lead", "Privacy Owner"]
last_updated: "2026-09-21"
decision_status: "proposed"
---

# ADR-007 — Provider-neutral LLM gateway với DeepSeek là provider đầu tiên

## Context

DeepSeek được chọn làm provider đầu tiên (`DEC-008`), nhưng model/capability/pricing/API thay đổi theo thời gian và privacy approval chưa hoàn tất. Domain coupling với provider SDK làm eval/fallback/test và đổi provider khó kiểm soát.

## Decision

Mọi inference **MUST** đi qua internal `LLMGateway` canonical contract tại `ARCH-008`. DeepSeek adapter là infrastructure implementation. Domain/graph **MUST NOT** import provider SDK hoặc biết base URL/model names.

Tests dùng deterministic fake. Provider, endpoint, model và credential là server-side config/secret. Provider switch chỉ được phép nếu capability contract, privacy, security và eval gate pass.

## Alternatives

- Direct DeepSeek calls từ graph nodes: từ chối vì coupling và guardrail duplication.
- Multi-provider active routing ngay V1: từ chối vì tăng eval/cost/incident surface; gateway chỉ tạo đường mở rộng.
- Self-host model: future option nếu legal/cost/quality evidence hỗ trợ.

## Consequences

Thêm mapping/validation layer và có thể không dùng mọi provider-specific feature ngay. Đổi lại có deterministic tests, central redaction/budget/circuit/telemetry và provider portability thực tế.

## Constraints

- Canonical structured request/response có version.
- Outbound payload **MUST** pass privacy policy; direct identifier blocked mặc định.
- Tool output/arguments strict-validated; model không execute.
- Raw reasoning **MUST NOT** persist/display.
- Provider streaming normalized trước API stream.
- Prompt/model change **MUST** trigger eval.

DeepSeek Responses API supports JSON Schema/tools/SSE but documents that generated function arguments may be invalid/hallucinated; application validation remains mandatory ([official API](https://api-docs.deepseek.com/api/create-response/)).

## Acceptance and failure

Contract suite pass cho fake/DeepSeek; redaction snapshot; malformed output, rate-limit, timeout và mid-stream failure tests; no-provider mode works. Until `OQ-005` closes, DeepSeek **MUST** only receive synthetic/non-personal approved data.

Traceability: `DEC-008`, `OQ-005`, `ARCH-004`, `ARCH-008`.

