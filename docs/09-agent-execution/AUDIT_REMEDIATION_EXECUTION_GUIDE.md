---
document_id: "DOC-AGENT-AUDIT-REMEDIATION-001"
version: "0.1.0"
status: "draft"
owner: "Agentic Delivery Architecture"
approvers: []
last_updated: "2026-09-27"
---

# Audit remediation execution guide

## 1. Scope

This guide defines the execution discipline shared by the audit-remediation micro tasks. It narrows implementation choices; it does not supersede approved requirements, contracts, decisions, AI specifications, security controls, or the assigned task. A task remains blocked while this guide or another normative input required by that task is not approved.

## 2. Mandatory executor sequence

1. Resolve repository root, HEAD, branch, and the full pre-existing Git state including staged, unstaged, untracked, ignored, and deleted paths.
2. Load the assigned task verbatim, every input, every traceability source, outputs of dependencies, and the human approval record when required.
3. Confirm `status: ready`, accepted dependencies, an unexpired approval naming the exact task and scope, and a write lease covering every resolved allowed path and conflict key.
4. Run only the task's offline preflight commands. A missing dependency, unapproved source, dirty overlap, unavailable deterministic test, or need for an unlisted file produces a schema-valid `blocked` result.
5. Implement one observable objective. Domain policy belongs in domain/application services; routes, graph nodes, UI, and infrastructure adapters only translate or orchestrate typed outcomes.
6. Add focused behavior tests that prove the invariant and its principal failure paths. Do not weaken an assertion, replace a production boundary with a test-only helper, or treat a mock interaction as proof of persistence.
7. Run verification in order, record command, duration, exit code, and evidence reference, then inspect `git diff --name-only`, exact diff, and final status.
8. Return one `task-output.schema.json` object. `not_verified`, `blocked`, and `failed` remain explicit; they are never narrated as completion.

## 3. Agent state-machine invariants

The canonical write state progression is:

```text
PROPOSED
  -> NORMALIZED
  -> AUTHORIZED
  -> PREVIEWED
  -> AWAITING_CONFIRMATION
  -> CONFIRMED
  -> EXECUTION_RESERVED
  -> EXECUTING
  -> SUCCEEDED | FAILED_NO_EFFECT | RESULT_UNKNOWN
  -> RECONCILED when RESULT_UNKNOWN
```

`CANCELLED`, `EXPIRED`, `AUTHORIZATION_DENIED`, `POLICY_BLOCKED`, and `SAFE_FAILURE` are terminal without a side effect. The graph may not infer confirmation from conversational text, node traversal, a valid payload hash, or elapsed time. Confirmation is a trusted event containing actor/session binding, preview ID, one-time token, decision, and idempotency context. Resume must load the exact checkpoint and preview version; missing or incompatible state fails closed.

The execute node never fabricates a business ID or success result. It invokes an application service through a typed port. The service owns re-authorization, atomic reservation, mutation, audit/outbox, and receipt. The graph only maps the returned typed outcome. `RESULT_UNKNOWN` disables blind retry and routes to reconciliation using the original idempotency key and upstream correlation.

## 4. Tool and write protocol

Tool candidates are data. Before invocation deterministic code must:

- resolve the tool from an allowlisted registry and exact contract version;
- reject unknown fields, duplicate JSON keys, coercion, non-finite numbers, oversized text, invalid identifiers, and disallowed enum values;
- bind trusted identity and resource attributes outside model-controlled arguments;
- authorize tool, action, target, field set, and data classification;
- normalize payload once and calculate an immutable preview hash;
- create a durable preview with expiry, policy/tool versions, actor/session binding, and one-time status;
- require explicit confirmation for write tools and consume it atomically;
- reserve idempotency before mutation and return the original receipt for valid replay;
- commit mutation, audit event, and outbox in one transaction or return no effect;
- redact user-facing and logged errors while preserving a correlation ID.

Read tools still require authorization, bounded queries, output classification, minimization, and audit appropriate to their risk. The model never receives database credentials, unrestricted query syntax, filesystem access, arbitrary URLs, or a generic command executor.

## 5. Evidence and RAG protocol

Retrieved content is untrusted even when stored in an approved index. Retrieval must enforce tenant/actor visibility, publication state, version, effective interval, revocation, provenance, and source authorization before content enters the prompt. An indirect-injection detector is an additional signal; it never replaces these controls.

The answer pipeline produces typed claims before user-facing prose. `EvidenceGate` evaluates every policy/procedure claim against exact citation IDs and locators from the candidate bundle. It rejects absent, revoked, stale, future-effective, conflicting, unauthorized, or insufficient evidence. Unsupported claims are removed or cause abstention; the composer cannot mark itself grounded. Citation confidence and validity are server-derived facts or explicit `unknown`, never UI defaults.

Provider streaming of policy assertions is buffered until evidence validation. A stream that terminates as incomplete, failed, malformed, schema-invalid, or missing its terminal event cannot become a completed answer. The UI receives a stable safe outcome and correlation ID.

## 6. Prompt-injection and output controls

System policy, tool registry, identity, authorization, output schema, and evidence rules are separate trusted channels. User text, documents, citations, tool results, provider errors, and memory are delimited and labelled as data. Instructions inside those channels are ignored.

High-confidence exfiltration or tool-manipulation signals block the tool call and emit a privacy-safe security event. Output validation rejects secret/token patterns, hidden prompt disclosure, chain-of-thought requests, unbound citation IDs, unauthorized identifiers, dangerous links, and tool arguments outside schema. At most one schema repair is allowed when the route, deadline, and budget permit; repair adds no privileges and sees only redacted invalid output plus sanitized schema errors.

## 7. Sensitive and emergency handling

Deterministic rules and the classifier run before ordinary routing; the higher risk result wins. Classifier failure uses deterministic rules and defaults ambiguous high-risk input to the safe path. The response is supportive, non-diagnostic, privacy-minimized, and drawn from an approved versioned template.

An official contact appears only when configuration has an approved-active value, owner, verification date, effective interval, and environment permission. Otherwise the response states that an official contact is unavailable in the simulation. `HANDED_OVER` is emitted only after a durable queue receipt. Queue timeout produces `RESULT_UNKNOWN` or `FAILED_NO_EFFECT` according to dispatch knowledge; it never becomes a promise of human intervention.

## 8. Provider egress, budgets, and traces

Demo, test, and CI select a deterministic fake and deny network at the boundary. A live route requires an allowlisted destination/model profile, valid secret reference, environment permission, data classification, transfer approval, purpose, minimization/redaction result, budget reservation, deadline, and correlation context. Missing any gate disables the route. Free-provider failure does not authorize a paid fallback.

Token cap, tool-call cap, retry count, deadline, and spend are upper bounds. The adapter uses the smallest remaining approved limit. It never expands a caller's cap. Retry is allowed only for classified transient failures, while budget and deadline remain, and never for an uncertain write outcome.

Traces record correlation IDs and version identifiers for provider, model capability, prompt, retrieval, tool contract, policy, evidence gate, and safe outcome. They exclude raw authorization, secrets, unrestricted prompt/context, personal data, provider reasoning, and chain-of-thought. Provider error bodies are normalized and redacted before logging.

## 9. Required negative-test matrix

Each affected task selects applicable rows and records them in acceptance evidence:

| Boundary | Required negative cases |
|---|---|
| Confirmation | missing, deny, cancel, expired, actor/session mismatch, payload mismatch, policy changed, token replay, new idempotency key, concurrent confirm |
| Tool schema | unknown tool/version, extra/missing field, duplicate key, type coercion, oversized input, invalid enum/ID, unauthorized target |
| Persistence | DB unavailable, audit failure, outbox failure, transaction rollback, restart, two workers, retry after timeout |
| Evidence | zero result, stale/revoked/future source, conflicting sources, unauthorized source, locator mismatch, invented citation, unsupported claim |
| Injection | direct override, retrieved instruction, tool-output instruction, encoded attack, data exfiltration, fake citation, multilingual/typo variants |
| Safety | classifier unavailable, false positive benign control, ambiguous high risk, missing contact, queue unavailable, queue timeout, payload minimization |
| Provider | no approval, no key, unapproved destination, budget exhausted, deadline exhausted, 429/5xx, malformed JSON/SSE, incomplete/failed stream |
| UI | 401/403, empty, offline, timeout before/after dispatch, stale, result unknown, duplicate click, refresh/reload, keyboard focus restoration |

## 10. Evidence quality and recovery

Tests use deterministic clocks, UUIDs, fakes, and synthetic records. Network, paid services, real identities, personal data, production, and destructive operations remain disabled unless the task and exact human approval explicitly authorize them. Screenshots supplement behavioral evidence; they do not prove authorization, persistence, accessibility, or backend effects.

Recovery is non-destructive. Keep an unpromoted patch, disable an existing feature flag, restore a previous immutable pointer/image, or apply a reviewed reverse patch limited to the task. Additive migrations use forward fixes and an approved restore plan. Never prescribe broad cleanup, database reset, history rewrite, or deletion of dirty/untracked data.

