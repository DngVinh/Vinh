---
document_id: "DOC-QUAL-004"
version: "1.0.0"
status: "reviewed"
owner: "Contract Testing Lead"
approvers: ["Architecture Lead", "Backend Lead", "AI Architecture Lead", "Security Lead"]
last_updated: "2026-09-22"
---

# Contract test plan

## 1. Scope

Contract testing covers:

- `contracts/openapi/v1/openapi.yaml` (`API-OAS-V1-001`);
- `contracts/json-schema/**` for errors, citations, actions, tickets, identity and handover;
- `contracts/tools/**` (`TOOL-002`, `TOOL-003`, `TOOL-REGISTRY-V1`);
- event envelopes and payloads defined by `docs/04-architecture/contracts/EVENT_CONTRACTS.md`;
- internal identity and external schedule/ticket/room/notification/LLM adapter boundaries;
- database migration compatibility that changes a public/internal contract.

No test may “learn” a schema from current implementation output. Approved contract is the oracle.

## 2. Contract suites

| Test ID | Oracle | Required cases | Trace |
|---|---|---|---|
| TEST-CON-OAS-001 | OpenAPI parses and every local/external `$ref` resolves | full document, no duplicate operation ID, unique method/path | API-OAS-V1-001; ARCH-CHECK-004 |
| TEST-CON-OAS-002 | Every operation response matches declared status/content/schema | one positive and every declared error family | API-SYS-001,002; API-IDENTITY-001; API-SCHEDULE-001; API-CONV-001..004; API-ACTION-001..003; API-TICKET-001,002; API-DOC-001,002; API-ROOM-001,002; API-BOOKING-001,002; API-HANDOVER-001,002; API-KNOW-001..003; API-OPS-001 |
| TEST-CON-OAS-003 | Request validation rejects unknown/invalid fields | missing required, boundary length, enum, format, additional property | REQ-NF-SEC-008; SEC-CTRL-002 |
| TEST-CON-ERR-001 | Error body is stable, non-leaking and correlated | 400/401/403/404/409/422/429/5xx; no existence/secret leak | API-SCHEMA-ERROR-001; REQ-NF-OBS-001,002 |
| TEST-CON-PAGE-001 | Cursor is opaque, actor/scope/query bound and stable | first/next/end, invalid/expired/foreign cursor, limit 1/100/101 | API conventions; SEC-AUTHZ-006 |
| TEST-CON-IDEM-001 | Same actor/action/key/canonical payload returns same logical result | sequential and concurrent replay | ADR-016; REQ-F-TICKET-008; REQ-F-ROOM-005 |
| TEST-CON-IDEM-002 | Same key with changed payload/actor/action is rejected | mismatch and expired record | API-ACTION-002,003; SEC-CTRL-003 |
| TEST-CON-SCHEMA-001 | Every JSON Schema compiles as Draft 2020-12 with format assertion | valid sample + malformed schema fixture | API-SCHEMA-*; TOOL-SCHEMA-001..006 |
| TEST-CON-SCHEMA-002 | Strict object contracts reject unknown properties and invalid formats | positive + one negative per rule/branch | REQ-NF-SEC-008; TOOL-002 |
| TEST-CON-CITE-001 | Citation resolves immutable source/version/locator/provenance | valid, missing, invented, superseded | REQ-F-RAG-003,004; EVAL-RED-019,020 |
| TEST-CON-ACTION-001 | Preview/confirmation schemas bind actor, action, payload hash, policy and expiry | valid, altered payload, expired, foreign actor, replay | API-SCHEMA-ACTION-PREVIEW-001; API-SCHEMA-ACTION-CONFIRM-001; ADR-016 |
| TEST-CON-TOOL-001 | Registry ID/name/version/schema refs resolve byte-for-byte | every registered tool, no orphan schema | TOOL-003; REQ-NF-PORT-002 |
| TEST-CON-TOOL-002 | Invocation/result validates before/after broker execution | unknown tool/version, extra trusted field, malformed result | TOOL-SCHEMA-002,003; REQ-NF-SEC-008 |
| TEST-CON-TOOL-003 | Read/write metadata controls workflow | read needs auth; write cannot execute without preview/confirmation/idempotency/audit | TOOL-SCHEDULE-001; TOOL-TICKET-001,002; TOOL-DOCUMENT-001; TOOL-ROOM-001,002; TOOL-HITL-001 |
| TEST-CON-EVT-001 | Event envelope has immutable ID/type/version/time/aggregate/correlation and valid payload | positive/negative for every event type | EVT-*; REQ-NF-OBS-001,003 |
| TEST-CON-EVT-002 | Consumer handles duplicate/out-of-order/unknown compatible event safely | replay, gap, newer optional field, unsupported version | ADR-008; REQ-NF-DATA-004 |
| TEST-CON-IDENT-001 | Mock and Entra-candidate fixtures map to same internal actor contract | valid issuer/audience/subject/roles, missing/forged claim | ADR-015; REQ-NF-PORT-003; SEC-AUTHN-001..012 |
| TEST-CON-ADAPTER-001 | Fake and candidate adapters satisfy same typed port | success, not-found, denial, validation, timeout, rate-limit, unknown outcome | REQ-NF-PORT-002; ARCH-008 |
| TEST-CON-LLM-001 | Fake/DeepSeek candidate map to provider-neutral request/result/error/usage contract | text, structured output, malformed JSON, timeout, rate-limit | ADR-007; REQ-NF-MAINT-002; AI gateway spec |
| TEST-CON-MIG-001 | Old and new application versions coexist during rollout | expand schema, old-read/new-write and new-read/old-write matrix | REQ-NF-MAINT-004; ADR-012 |

## 3. Fixture rules

Each schema/operation MUST have:

1. minimal valid fixture;
2. full valid fixture;
3. one invalid fixture per required field, enum, boundary, format and `additionalProperties` rule;
4. privacy canaries in prohibited fields to prove rejection/redaction;
5. immutable expected hash in the fixture manifest.

Fixtures MUST be synthetic and MUST NOT contain plausible real personal email, phone, student number or secret. UUID/time values are deterministic per seed or normalized before hashing.

## 4. Producer/consumer matrix

| Producer | Consumers | Required proof |
|---|---|---|
| FastAPI OpenAPI | Next.js, test client, operations probes | generated/typed client compatibility + runtime response validation |
| Tool registry/schema | LangGraph/tool broker, adapter implementations | registry ref resolution + invocation/result fixtures |
| Outbox events | workers, metrics, notifications | consumer contract + duplicate/out-of-order semantics |
| Identity adapter | application/authz policy | claim mapping and deny-safe negative fixtures |
| LLM gateway | agent graph, cost/telemetry | fake/live candidate conformance without domain SDK import |
| PostgreSQL schema | current/previous API and worker image | migration compatibility + restore/rollback plan |

Provider and consumer tests MUST run against the same contract hash. Generated clients/bindings, if used, must be reproducible and never hand-edited.

## 5. Compatibility classification

| Change | Classification | Gate |
|---|---|---|
| Add optional response field with tolerant consumer | compatible | contract regression + version note |
| Add required request field, remove/rename field or enum value | breaking | new version + migration + consumer readiness; block current release |
| Change meaning/auth/confirmation/idempotency | behavioral/security breaking | approved requirement/ADR/control + full affected gates |
| Tighten validation | potentially breaking | negative corpus + deployed-client impact review |
| Event optional field | compatible only if old consumer ignores safely | replay with old consumer |
| Tool schema or registry semantic change | promotion boundary | full tool/AI/security regression and registry version bump |

Compatibility tools are evidence helpers; human classification remains required for semantic changes.

## 6. API failure oracles

- 401/403/404 behavior MUST not reveal resource existence beyond approved error policy.
- 409 represents deterministic conflict/current state and MUST not be silently retried as success.
- 422 reports validation issues without echoing secret/forbidden input.
- 429 includes stable retry metadata; excess work is not processed.
- 5xx/timeout MUST not include false receipt, fabricated data or duplicate side effect.
- SSE policy/procedure content MUST not expose rejected unsupported deltas before evidence gate (`EVAL-RED-035`).

## 7. Evidence and gate

Evidence bundle includes validator/tool versions, contract hash, fixture manifest/hash, compatibility baseline, case counts, failures and machine-readable report. `GATE-REL-003` fails on unresolved ref, invalid example, untested operation/tool/event, unknown breaking change, missing negative fixture or implementation drift.

## 8. Micro-task order

Create separate tasks for: schema compiler; common error fixtures; each API domain; action/idempotency; tool registry; each tool schema; event envelope; each event family; identity adapter; LLM adapter; compatibility report. A task MUST NOT edit approved contract merely because implementation fails it.
