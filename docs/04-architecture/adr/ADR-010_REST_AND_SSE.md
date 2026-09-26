---
document_id: "DOC-ADR-010"
version: "1.0.0"
status: "draft"
owner: "API Architect"
approvers: ["Architecture Lead", "Web Lead", "Backend Lead", "Operations Lead"]
last_updated: "2026-09-21"
decision_status: "proposed"
---

# ADR-010 — REST/JSON và Server-Sent Events; không WebSocket baseline

## Context

Hầu hết capability là request/response resource/command. Chat cần server-to-client token/progress streaming nhưng client commands vẫn có thể là HTTP requests. WebSocket tạo connection/auth/reconnect/scaling protocol riêng chưa cần thiết.

## Decision

Public V1 API **MUST** dùng versioned REST/JSON. Chat/progress một chiều dùng SSE với canonical event types, sequence và terminal event. Async business events không public trực tiếp; UI lấy state qua API hoặc controlled SSE notifications.

## Alternatives

- WebSocket: từ chối baseline; reconsider nếu có realtime bidirectional collaboration/voice với measured requirement.
- Long polling: fallback có thể có nhưng không primary vì latency/request overhead.
- GraphQL subscriptions: không cần và tăng schema/runtime.

## Consequences

SSE đơn giản, qua HTTP infrastructure, dễ debug; không hỗ trợ client-to-server multiplex và cần heartbeat/reconnect semantics. Edge/load-balancer idle timeout phải cấu hình và test.

## Constraints

- SSE event có `id`, `event`, JSON `data`, monotonic sequence.
- Client reconnect dùng last event ID chỉ nếu endpoint contract hỗ trợ replay; không giả replay.
- Heartbeat không chứa business data.
- Exactly one terminal event; raw provider stream không public.
- Dynamic/SSE responses `no-store`.
- Write vẫn qua REST với idempotency key, không qua stream event.

## Acceptance and failure

Test normal stream, slow client, reconnect, duplicate event handling, client disconnect, provider mid-stream failure và ALB timeout. ALB default idle timeout behavior/config is documented by AWS ([ALB attributes](https://docs.aws.amazon.com/elasticloadbalancing/latest/application/edit-load-balancer-attributes.html)). Nếu streaming không đạt SLO qua selected edge, use non-streaming fallback và open architecture review; không bypass TLS/WAF.

Traceability: `ARCH-005`, `ARCH-006`, `ARCH-007`.

