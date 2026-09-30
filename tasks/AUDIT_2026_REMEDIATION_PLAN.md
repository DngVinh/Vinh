# Antigravity findings: scoped remediation plan

Status: planning artifact, 2026-09-28. This file grants no implementation authority. Each row becomes a separate `tasks/items/*.yaml` task with an accepted dependency chain, approved inputs, an exact write scope, and any required task-specific human approval before it is marked `ready`.

`TASK-AGENT-PARSERFIX-001` was registered and accepted separately. Preserve all working-tree changes present before this plan.

| Proposed task ID | Findings | Objective and exact primary write paths | Approval gate |
|---|---|---|---|
| `TASK-AGENT-STATEFIX-001` | AI-001, AI-006 | Complete typed state in `services/api/src/campus247/agent/state.py`; focused state tests. | Approved AI state contract. |
| `TASK-AGENT-GRAPHFIX-001` | AI-002, AI-003 | Correct graph transitions in `services/api/src/campus247/agent/graph.py`; transition tests. | Architecture and security review of transitions. |
| `TASK-AGENT-EVIDENCEWIRE-001` | 001 | Connect the existing deterministic gate in `services/api/src/campus247/agent/nodes/definitions.py`; graph evidence tests. | Approved AI evidence contract. |
| `TASK-AGENT-WRITEWIRE-001` | 002 | Require explicit confirmation and authoritative execution receipt in `services/api/src/campus247/agent/nodes/definitions.py`; write-flow tests. | Authorization and security approval. |
| `TASK-AGENT-CONTACTFIX-001` | 003, RT-003 | Remove invented contact and false handover claim; fail safely and alert when approved contact/config is absent; `definitions.py`, narrowly scoped config/alert port, tests. | Safety/security approval; OQ-003 remains open for any real contact. |
| `TASK-AGENT-ROOMFIX-001` | 004 | Select the booking tool and recheck availability before write in `definitions.py`; booking tests. | Authorization and write-policy approval. |
| `TASK-AGENT-TOOLPOLICY-001` | 005 | Enforce timeout, attempts and breaker policy in `services/api/src/campus247/agent/tools/registry.py` and focused tests. | Security policy approval. |
| `TASK-AGENT-GUARDFIX-001` | AI-004 | Implement deterministic output rejection conditions in `services/api/src/campus247/agent/nodes/compose.py` and focused tests. | Safety/security approval. |
| `TASK-AGENT-CLASSFIX-001` | AI-005 | Parse and validate full sensitive-classifier schema in `definitions.py` and focused tests. | Safety/security approval. |
| `TASK-AGENT-CONFLICTFIX-001` | AI-007 | Replace query-string conflict shortcut with source metadata checks in `definitions.py` and focused tests. | Approved RAG contract. |
| `TASK-API-IDENTITYFIX-001` | SEC-001, API-004 | Correct demo cookie/session exposure and synthetic code in `services/api/src/campus247/presentation/identity.py`; focused API tests. Decide explicitly whether the JSON body still returns the token before this task is ready. | Authentication/security approval; file is dirty. |
| `TASK-API-TICKETAUTHZ-001` | SEC-002 | Re-evaluate authorization at preview and confirm in the two ticket application services and their `bootstrap/app.py` wiring; focused tests. | Authorization approval; bootstrap is dirty. |
| `TASK-API-CONFIRMBIND-001` | SEC-003 | Bind full context in `services/api/src/campus247/domain/actions/confirmation.py` and its confirm consumer; focused tests. Resolve whether session binding changes the approved contract before marking ready. | Cryptography/contract approval; source is untracked. |
| `TASK-API-BREAKGLASS-001` | SEC-004 | Implement named, step-up, reasoned, expiring staff break-glass policy with an explicit grant and alert port plus focused tests. | Exact privileged-access security approval; enumerate concrete files in the task. |
| `TASK-API-KEYGUARD-001` | SEC-005 | Reject default signing keys in production in `services/api/src/campus247/bootstrap/settings.py`; focused tests. Extending the guard to staging needs a separate explicit decision. | Security policy approval. |
| `TASK-API-STREAMFIX-001` | API-001 | Validate the complete answer before emitting semantic SSE deltas; use contracted terminal events in `services/api/src/campus247/presentation/chat.py`; API tests. | Approved stream contract; file is dirty. |
| `TASK-API-PREVIEWFIX-001` | API-003 | Use `sha256:` and canonical decision in `services/api/src/campus247/domain/action/preview.py` and required confirmation consumer; focused tests. | Cryptography/confirmation compatibility approval. |
| `TASK-API-ACTIONSROUTE-001` | API-002 | Mount canonical `/v1/actions/*` routes and schemas in presentation/bootstrapping; contract tests. | Authorization and contract approval; bootstrap is dirty. |
| `TASK-CONTRACT-CAPABILITIES-001` | API-005 | Declare two capability routes in `contracts/openapi/v1/openapi.yaml`; contract tests. | Contract owner approval. |
| `TASK-EVAL-QUOTA-002` | RT-001 | Create a deterministic generator, manifest and quota/provenance tests; keep large generated corpora outside Git as required by the approved dataset policy. | Approved evaluation baseline and human review of S1 cases; enumerate exact paths in the task. |
| `TASK-EVAL-REDTEAM-002` | RT-002 | Execute all catalog scenarios and benign controls against offline application boundaries in `evals/runners/red_team_catalog.py`; security tests. | Approved red-team catalog. |

## Execution order

1. Approve the relevant AI/evaluation/security normative sources and attach exact security/contract approvals. Do not invent an official emergency contact.
2. Register each proposed row as a schema-valid atomic task. Keep write scopes disjoint for concurrently ready tasks. The tasks touching `definitions.py` run serially.
3. Complete parser, state, registry, output guard, and independent API/eval work where sources and approvals permit. Then wire graph evidence, write confirmation, room booking, contact, and canonical API routes in dependency order.
4. Run each task's focused offline tests, catalog validation, exact diff/status check, and schema-valid output. Full release remains `not_verified` until production quotas and immutable release evidence pass.
