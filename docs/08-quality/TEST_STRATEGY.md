---
document_id: "DOC-QUAL-001"
version: "1.0.0"
status: "reviewed"
owner: "Quality Engineering Lead"
approvers: ["Product Owner", "Architecture Lead", "AI Quality Lead", "Security Lead", "SRE Lead"]
last_updated: "2026-09-22"
---

# Test strategy

## 1. Quality mission

Chứng minh bằng evidence có thể tái tạo rằng Campus 24/7 thực hiện đúng capability đã duyệt cho một trường, không dùng dữ liệu thật, không tạo side effect ngoài authorization/confirmation, không trình bày nội dung không có căn cứ, và degrade/rollback an toàn trên AWS ECS reference architecture.

## 2. Risk model

| Risk tier | Ví dụ | Test obligation | Release policy |
|---|---|---|---|
| R0 catastrophic | auth bypass, cross-user leak, unconfirmed/duplicate write, secret/PII egress, missed critical safety case | Deterministic positive + negative + adversarial + audit assertion | Zero tolerance; no waiver to production |
| R1 critical | false success, fabricated contact/citation, audit failure on write, corrupt migration/restore | Unit + contract + integration + E2E/fault test | Must pass; exception only outside production with owner/expiry |
| R2 major | broken core journey, latency/SLO miss, inaccessible P0 flow | Automated regression + manual specialist evidence where required | Blocks affected phase unless capability disabled |
| R3 moderate | isolated P1 behavior or degraded UX with safe workaround | Relevant automated/manual test | Tracked with owner and phase-specific decision |
| R4 minor | cosmetic/nonmaterial content issue | Focused test or review | Does not block unless accumulation breaks accessibility/trust |

Severity is impact, not effort. Unknown impact is classified one level higher until triaged.

## 3. Test environments

| Environment | Permitted data/provider | Purpose | Forbidden |
|---|---|---|---|
| Local | deterministic synthetic fixtures; fake LLM/adapters | unit, component, contract | live HUCE/production credentials |
| CI ephemeral | immutable synthetic dataset; fake provider | PR/merge gates, parallel isolation | network to unapproved service |
| Shared integration | synthetic dataset namespace per run; fakes/local dependencies | API/DB/queue/outbox integration | evidence reused across release tuple |
| Staging | production-like AWS config; synthetic only; fake by default, approved DeepSeek candidate run isolated | E2E, DAST, load, resilience, AI candidate | real student records; production endpoints |
| Pilot | synthetic until legal/identity/operating approvals close; release candidate image | controlled operational rehearsal | implicit production claim |
| Production | outside current authorization | post-deploy verification after explicit approval | agent-initiated deployment or synthetic gate bypass |

Every run MUST record environment ID, region, timestamp, image/config/dataset hashes and dependency mode. Shared test state without run namespace is a test defect.

## 4. Verification layers

1. Static: format, lint, type, import boundaries, schema compile, secret/license/IaC policy scans.
2. Unit/property: pure domain rules, state machines, normalization, scoring, time boundaries.
3. Component/integration: FastAPI application services, PostgreSQL/pgvector, Redis, SQS/outbox, adapter fakes.
4. Contract: OpenAPI/JSON Schema/tool/event/identity adapter compatibility.
5. Acceptance/E2E: Next.js–API journeys with role, failure, accessibility and audit oracles.
6. AI evaluation: offline deterministic + human-reviewed semantic suites, sealed split and red team.
7. Nonfunctional: performance, capacity, resilience, recovery, accessibility, security and operations drills.
8. Post-release: immutable digest/config verification and minimal synthetic canaries; not a substitute for pre-release gates.

## 5. Change-impact selection

| Changed artifact | Minimum suites |
|---|---|
| Domain/application logic | unit, property, affected integration, acceptance, architecture boundary |
| OpenAPI/JSON/tool/event schema | schema compile, positive/negative fixture, compatibility, consumer/provider, affected E2E |
| DB migration/model | migration dry-run, backward compatibility, rollback/restore, repository integration, data-quality |
| Next.js UI | component, browser E2E, keyboard, screen reader where P0, API contract |
| Prompt/model/provider | AI full affected suites, 3 repeats for high-variance suite, security/egress, latency/cost |
| Retrieval/chunker/embedding/reranker/corpus | ingestion, provenance, retrieval metrics, grounded answer, poisoning, performance |
| Auth/authz/session | full role/resource/action matrix, IDOR, CSRF/cookie, audit, production-config negative test |
| Write workflow | preview/hash/expiry, explicit confirmation, idempotency, concurrency, unknown-outcome reconciliation, audit |
| IaC/container/runtime config | IaC policy, image/SBOM/secret scan, deployment smoke, network/egress, rollback |
| Cache/retry/queue | isolation, freshness, duplicate/out-of-order, retry budget, DLQ/redrive, fault injection |

If impact cannot be bounded, run the full regression set; do not mark unaffected by assumption.

## 6. CI and scheduled lanes

| Lane | Trigger | Target duration | Mandatory content | Failure action |
|---|---|---:|---|---|
| L0 task | each micro-task | ≤10 min goal | focused unit/static/contract test | task remains incomplete |
| L1 PR | every change | ≤20 min goal | changed-scope suites, secret/SAST/SCA, synthetic scan | merge blocked |
| L2 merge | main candidate | ≤45 min goal | integration, full fake-provider, acceptance smoke, image/SBOM | candidate rejected |
| L3 nightly | scheduled | ≤3 h goal | broad E2E, accessibility automation, AI regression, resilience subset | release status red; owner paged by severity |
| L4 release candidate | immutable candidate | time-box declared by plan | all `GATE-REL-*`, full security/AI/performance/recovery evidence | no promotion |
| L5 monthly pilot | after authorized pilot | planned window | live-provider red team, incident/restore drill, metric review | capability rollback/disable as policy requires |

Durations are pipeline design goals, not permission to skip tests.

## 7. Oracle hierarchy

Preferred oracle order:

1. exact schema/state/business invariant;
2. persisted object/event/audit diff;
3. deterministic fake-provider output;
4. approved gold evidence and rubric;
5. two-person human review for critical semantic cases;
6. LLM judge only as supporting signal.

UI text snapshot alone cannot prove authorization, write integrity or audit completeness.

## 8. Entry and exit

Test execution entry requires approved upstream requirement/contract, accepted dependencies, executable fixture manifest and known expected result. A suite exits only when every required case has a terminal result, evidence is complete, reruns are linked rather than overwritten, and all failures have defect IDs.

A release is not eligible when any required suite is skipped, evidence points to another revision/config, flaky quarantine hides a required P0 case, or a test was changed in the same patch only to accept the current output without approved requirement change.

## 9. Defect policy

| Severity | Response | Closure evidence |
|---|---|---|
| Critical | stop promotion; contain affected path | reproducer, fix diff, regression test, security/quality approval |
| High | block affected release route | regression evidence and owner acceptance |
| Medium | phase decision with deadline | fix or time-bound waiver + compensating control |
| Low | backlog | linked rationale and target phase |

A defect closes only after the original failing case and a nearby negative/benign control pass on the same candidate.

## 10. Phase coverage

| Phase | Minimum exit |
|---|---|
| Foundation | contracts compile; architecture/security rules executable; synthetic generator reproducible; unit/static baseline |
| MVP | all P0 core read/write journeys on fake dependencies; hard-zero AI/security; CI evidence |
| Pilot readiness | production-like staging E2E; 200-user load; accessibility; recovery/rollback/incident drills; operating owners configured |
| Production readiness | all gates pass on immutable candidate; legal/privacy/identity/vendor/open questions closed; independent review; explicit go-live authority |

## 11. Traceability

Upstream: `DEC-003`, `DEC-004`, `DEC-008`–`DEC-020`, all P0/P1 `REQ-F-*`, all `REQ-NF-*`, `ARCH-001`–`ARCH-009`, `AI-*`, `EVAL-*`, `SEC-*`, `PRIV-*`, `HITL-*`. Downstream: `TEST-*`, `GATE-REL-*`, defect/waiver records and release evidence bundles.
