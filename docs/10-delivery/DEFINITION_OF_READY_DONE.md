---
document_id: "DOC-DEL-003"
version: "1.0.0"
status: "reviewed"
owner: "Delivery Quality Lead"
approvers: ["Product Owner", "Engineering Lead", "Quality Lead", "Security Lead"]
last_updated: "2026-09-22"
---

# Definition of Ready and Done

## 1. Rule

Ready authorizes work only inside declared scope; Done means reproducibly verified, not “agent says complete”. Any unchecked mandatory item keeps state `blocked` or `in_progress`. Approval and evidence cannot be inferred.

## 2. Micro-task Definition of Ready

A task may become `ready` only when:

- [ ] stable `TASK-<LAYER>-<DOMAIN>-<NNN>` ID, one objective and target phase exist;
- [ ] upstream requirement/acceptance IDs and priority/status resolve;
- [ ] architecture/ADR and API/DATA/EVT/TOOL contracts needed by the task exist at approved/review-eligible state required by governance;
- [ ] all dependencies are `accepted`, not merely code-complete;
- [ ] allowed write files/directories are explicit, inside workspace and disjoint from concurrent tasks;
- [ ] forbidden files/actions and security/data class are explicit;
- [ ] fixture/test IDs and deterministic oracle exist before implementation;
- [ ] positive, validation/auth and failure behavior are stated;
- [ ] expected commands/toolchain and evidence output are defined;
- [ ] no unresolved sensitive approval: auth/security policy, real data/secret, destructive migration, paid service, production deploy, breaking contract/dependency;
- [ ] rollback or safe abort is stated for any mutation/config/migration;
- [ ] pre-existing workspace changes were inspected and preservation is possible.

If task changes a contract/requirement/ADR, that governance change must be a separate accepted task before implementation.

## 3. Micro-task Definition of Done

A task is `verified` only when:

- [ ] objective behavior matches upstream contract without scope expansion;
- [ ] only allowed files changed and unrelated user/agent changes are preserved;
- [ ] implementation has no placeholder/TODO on success, authorization, audit, error or rollback path;
- [ ] relevant format/lint/type/static/unit/contract/integration tests pass;
- [ ] required negative and dependency-failure cases pass;
- [ ] logs/errors/evidence contain no secret, prohibited PII or full sensitive transcript;
- [ ] correlation/audit/metric events are asserted where applicable;
- [ ] exact commands, exit codes, test IDs, durations and artifact hashes are reported;
- [ ] no test/threshold/requirement was weakened to pass;
- [ ] deviations and residual risks are explicit; empty means genuinely none found;
- [ ] diff and repository status were reviewed after mutation;
- [ ] independent review accepts task when required.

`not_verified`, flaky rerun-only, skipped required suite or zero tests collected is not Done.

## 4. Specialized task requirements

### API/contract

Ready needs schema, auth, errors, idempotency/pagination and compatibility classification. Done needs schema compile, positive/negative fixtures, runtime response validation, consumer/provider check and compatibility report.

### Database/migration

Ready needs ownership, classification, expand/contract sequence, backup/restore and rollback/forward-recovery plan. Done needs empty/existing/max-shape dry-run, old/new version compatibility, constraint/index verification and no destructive operation. Destructive migration remains human-blocked.

### Frontend

Ready needs approved states/copy/API contract/accessibility acceptance. Done needs loading/empty/error/denied/degraded/success, keyboard/focus/reflow tests, no secret/PII client leak and E2E backend oracle.

### AI/RAG/tool

Ready needs versioned prompt/model/tool/corpus/eval scope and forbidden outcomes. Done needs deterministic fake suite, affected eval metrics/subgroups/red team, provider payload minimization, cost/latency and rollback pointer. Hard-zero failures block.

### Security/auth/privacy

Ready needs threat/data-flow/control diff and Security/Privacy reviewer. Done needs positive + negative role/resource/action tests, audit/egress/redaction evidence and independent approval. Agent cannot self-accept security exception.

### Infrastructure/release

Ready needs target non-production environment, IaC scope, budget approval, immutable artifact and rollback. Done needs synth/plan/policy scans, deployed smoke/health/config/digest proof and teardown/retention plan without broad deletion.

## 5. Increment Definition of Done

A capability increment is Done when all linked tasks are accepted; P0/P1 trace has no orphan; acceptance/contract/security/AI/nonfunctional suites applicable to it pass; user/service/operations docs and metrics exist; feature flag/safe mode/rollback is exercised; defects/risks have owner and disposition; Product, QE and mandatory domain reviewers accept.

## 6. Release candidate Definition of Ready

Candidate creation requires:

- immutable source revision and cleanly enumerated included changes;
- all target increment tasks accepted;
- versioned release manifest and artifact digests;
- environment/config/contract/data/AI asset hashes;
- applicable-gate matrix and test plan;
- deployment/rollback/runbook/communications draft;
- no unresolved Critical/S1 or unknown sensitive finding;
- gate owners and decision meeting/window identified.

## 7. Release Definition of Done

Non-production release is Done when required gates pass, deployment manifest matches runtime, smoke/post-deploy checks pass, rollback target remains usable and decision is recorded. Production additionally requires `GATE-REL-012`, explicit deployment authorization, observation window, sponsor acceptance and post-launch handoff. Merge, image push or infrastructure health alone is not release Done.

## 8. Phase Definition of Done

A phase is Done only by its `MS-*` exit criteria and promotion record in `PHASE_AND_MILESTONE_GATES.md`. Partially disabled capability may be accepted only if phase scope is formally reduced through change control and fallback is verified; documentation cannot silently redefine scope.
