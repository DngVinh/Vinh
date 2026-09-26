---
document_id: "DOC-QUAL-002"
version: "1.0.0"
status: "reviewed"
owner: "Quality Engineering Lead"
approvers: ["Engineering Lead", "AI Quality Lead", "Security Lead", "SRE Lead"]
last_updated: "2026-09-22"
---

# Test pyramid and ownership

## 1. Pyramid model

| Layer | ID prefix | Scope and oracle | Execution | Primary owner |
|---|---|---|---|---|
| Static/fitness | `TEST-STATIC` | syntax, types, imports, policy, schemas | every task/PR | Component engineer |
| Unit/property | `TEST-UNIT` | pure rule/state/time/normalization | every task/PR | Component engineer |
| Component | `TEST-COMP` | one bounded context with in-process ports | PR/merge | Backend/frontend owner |
| Integration | `TEST-INT` | real Postgres/Redis/SQS-compatible dependency, fake external provider | merge/nightly | Backend/platform + QE |
| Contract | `TEST-CON` | producer/consumer/schema compatibility | PR/merge/release | Contract owner + QE |
| Acceptance/E2E | `TEST-ACC` | user journey plus persistent/audit oracle | merge/nightly/RC | QE + Product |
| AI evaluation | `TEST-AI` | RAG/tool/safety quality against versioned corpus | changed scope/nightly/RC | AI Quality |
| Security/privacy | `TEST-SEC` | abuse, access, egress, supply chain, config | PR/staging/RC | Security + QE |
| Performance/resilience | `TEST-PERF`, `TEST-RES` | threshold, saturation, degradation, recovery | nightly subset/RC | SRE + Performance QE |
| Accessibility | `TEST-A11Y` | WCAG 2.2 AA automated/manual | PR affected UI/nightly/RC | Accessibility owner |
| Operational drill | `TEST-OPS` | alert, incident, restore, rollback, on-call | pre-pilot/RC | SRE/Incident Commander |

Approximate portfolio intent is many fast deterministic tests, fewer integration tests, and a compact set of high-value E2E/drills. No numeric ratio is a gate; risk coverage and execution time evidence decide the mix.

## 2. Ownership matrix

| Artifact/activity | Responsible | Accountable | Consulted | Required reviewer independence |
|---|---|---|---|---|
| Unit/component tests | Implementing engineer/agent | Engineering Lead | QE | same task may author test; requirement may not be rewritten |
| Acceptance catalog/oracle | QE | Product Owner | Service/UX/Architecture | Product or domain reviewer distinct from implementer |
| API/tool/event contracts | Contract owner | Architecture Lead | QE/Security/AI | breaking/security change requires independent reviewer |
| AI dataset/rubric/gate | AI Quality | AI Quality Lead | Product/Knowledge/Security | two reviewers for critical/safety/security cases |
| Security test and severity | Security QE | Security Lead | Architecture/QE | author of vulnerable change cannot self-accept finding |
| Load/resilience/recovery | Performance QE/SRE | SRE Lead | Architecture/Service owner | restore evidence witnessed by Release Owner |
| Accessibility manual audit | Accessibility specialist | Product Owner | QE/UX | manual evidence cannot be replaced by automated score |
| Release evidence bundle | Release Engineering | Release Owner | all gate owners | bundle signer differs from candidate builder |
| Go/no-go | Release Owner coordinates | Product Owner; Security/Privacy approval mandatory | AI Quality, SRE, Support, Knowledge | no single role may override a failed hard gate |

For a one-human-plus-agents project, “independence” means a separate review pass with explicit reviewer role and immutable input revision; the same AI response cannot be both implementation and approval evidence.

## 3. Test placement rules

- Put a rule at the lowest layer that can observe it reliably, then add one higher-level proof for P0 journey integrity.
- Authorization must be tested below UI and again through API/E2E negative paths.
- Preview/confirm/idempotency requires domain unit tests, API/DB integration, and E2E persistent-state/audit assertion.
- Citation existence uses deterministic schema/provenance checks; citation meaning additionally uses eval/human rubric.
- DeepSeek behavior is never required for unit/contract tests; use deterministic fake provider. Live-provider tests are isolated promotion evidence.
- AWS controls are tested as IaC assertions before deployment and runtime probes in staging.

## 4. Minimum suite by component

| Component | Required tests |
|---|---|
| Next.js web | type/lint, component states, API mock contract, browser P0 flows, keyboard/reflow, security headers |
| FastAPI API | unit/application, authz negative matrix, OpenAPI response validation, idempotency/concurrency, structured error |
| Worker/outbox | state/property, duplicate/out-of-order, lease/visibility timeout, DLQ, crash-before/after ACK |
| PostgreSQL/pgvector | migration, constraints, ownership filters, lexical/vector retrieval, backup/restore |
| Redis | key-scope isolation, TTL/freshness, outage fail mode, no source-of-truth dependency |
| LLM gateway | provider contract, timeout/repair budget, de-identification, usage/cost telemetry, fake/live separation |
| LangGraph | state transition, checkpoint/resume, interrupt-before-write, max steps, invalid-state recovery |
| Knowledge pipeline | file allowlist/scan, provenance, chunk determinism, idempotent ingest, publish/supersede/rollback |
| AWS CDK/ECS | synth/test, IAM/network/encryption/logging policy, immutable image, health/rollback smoke |

## 5. Flaky and nondeterministic tests

- Deterministic tests MUST have zero tolerated flakiness. A rerun does not erase first failure.
- Quarantine requires defect ID, owner, scope, expiry and proof test is not a P0/hard-zero gate. Required P0 cases cannot be quarantined to promote.
- Live-provider semantic suites run at least three repeats where variance is expected; report `pass@all`, `pass@majority` and worst observed safety/security result.
- Time/randomness/UUID/external status MUST be injected or recorded. Fixed sleeps are prohibited when an observable condition can be awaited.
- Test order dependence is a defect; each test owns a namespace and cleanup must be safe/reversible.

## 6. Micro-task decomposition for Gemini Flash

A test implementation task SHOULD change one test file plus at most two fixture/helper files and SHOULD add about 150 lines. Split in this order:

1. fixture/schema validator;
2. happy-path unit/contract case;
3. authorization or validation negative case;
4. failure/dependency case;
5. audit/telemetry evidence assertion;
6. higher-level acceptance wiring.

Task exit must include exact command, exit code, test IDs executed, duration, artifact path/hash and changed files. `0 tests collected`, filtered required tests or empty report is failure.

## 7. Coverage policy

Line/branch coverage is diagnostic, not the release oracle. New/changed pure domain code SHOULD achieve at least 90% branch coverage, adapters/UI at least 80%, but a numeric exception does not excuse missing requirement/negative-path coverage. P0 requirement coverage is 100% by trace ID across positive, negative, authorization and failure paths where applicable.

## 8. Escalation

Unknown expected behavior, missing contract, contradictory documents, destructive test setup, real data/secret discovery or a requested threshold reduction creates `blocked`; agent stops before mutation outside task scope and reports impacted IDs and safe options.
