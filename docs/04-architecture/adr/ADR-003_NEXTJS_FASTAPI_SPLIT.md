---
document_id: "DOC-ADR-003"
version: "1.0.0"
status: "draft"
owner: "Application Architect"
approvers: ["Architecture Lead", "Web Lead", "Backend Lead"]
last_updated: "2026-09-21"
decision_status: "proposed"
---

# ADR-003 — Next.js presentation và FastAPI application API

## Context

Sản phẩm cần responsive web/PWA, SSR/static assets, REST/SSE, typed Python AI ecosystem và separation giữa browser presentation với domain/security logic.

## Decision

`web` dùng Next.js/TypeScript; `api` dùng FastAPI/Python. Next.js **MUST** chỉ giữ presentation/server rendering/API client concerns. FastAPI **MUST** là authority cho authentication context, authorization, business transaction, tools và LangGraph.

Không direct database từ Next.js. Shared contract sinh từ OpenAPI/JSON Schema, không copy handwritten DTO hai phía.

## Alternatives

- Full-stack Next.js: từ chối vì AI/LangGraph/backend Python stack đã được chốt và dễ làm authorization phân tán.
- Server-rendered FastAPI templates: từ chối vì product UX/PWA/design-system needs.
- GraphQL: chưa chọn vì REST/resource commands và SSE đủ cho V1; thêm schema/runtime complexity.

## Consequences

Hai language/toolchain và network hop bổ sung, nhưng domain boundary rõ, Python AI tooling tự nhiên và web deploy độc lập. CORS/session strategy phải được contract hóa; ưu tiên same-origin edge routing.

## Constraints

- Browser **MUST NOT** nhận backend/provider/AWS secrets.
- API **MUST** recompute authorization; web guard chỉ là UX.
- User-specific Next response **MUST** private/no-store.
- SSE proxy/path **MUST** được load-test qua edge.
- API client types **MUST** generated/pinned từ approved contract.

## Acceptance and failure

Contract drift check, unauthorized endpoint tests, SSE disconnect test và build-to-build type compatibility phải pass. Nếu web cần domain decision để render, agent thêm API/query contract; **MUST NOT** reimplement policy trong TypeScript.

Sources: [Next.js self-hosting](https://nextjs.org/docs/app/guides/self-hosting), [FastAPI containers](https://fastapi.tiangolo.com/deployment/docker/). Traceability: `DEC-011`, `ARCH-002`, `ARCH-003`.

