---
document_id: "DOC-DEL-008"
version: "1.0.0"
status: "reviewed"
owner: "Release Owner"
approvers: ["Product Owner", "Security Lead", "Privacy Lead", "SRE Lead", "Quality Lead"]
last_updated: "2026-09-22"
---

# Launch and rollback plan

## 1. Scope and current authorization

This plan is executable for an explicitly approved **synthetic non-production pilot rehearsal**. Production launch is future and remains blocked until `MS-PROD-001`, `GATE-REL-012`, all `OQ-001..008` and explicit deployment authorization are complete. No step authorizes an agent to deploy, purchase resources or use real data/secrets.

## 2. Required launch roles

Release Owner coordinates; Product Owner decides business go/no-go; SRE executes/observes; Security/Privacy owns control stop; QE validates gates; AI Quality validates model/prompt/corpus; Service/Knowledge owners validate workflows/content; Communications owner issues approved messages. Any required owner `UNASSIGNED` makes decision `NO_GO` for production.

## 3. Pre-launch checklist

### Candidate and gates

- [ ] immutable candidate/release manifest and previous release target;
- [ ] required `GATE-REL-*` all `passed` for target phase;
- [ ] zero expired waiver or unresolved non-waivable finding;
- [ ] image/SBOM/signature/config/contract/data/AI asset/evidence hashes verified;
- [ ] scope, feature defaults and safe modes agreed.

### Platform/data

- [ ] backup/restore evidence current; RPO/RTO drill passed where required;
- [ ] migration dry-run and old/new compatibility pass; destructive step absent;
- [ ] capacity, quotas, DB pool, egress and cost caps configured;
- [ ] synthetic-only data/provenance scan passed;
- [ ] secrets supplied from approved manager; no value in manifest/log.

### Operations/service

- [ ] dashboards/alerts/correlation/audit and independent alert health verified;
- [ ] runbooks for provider/DB/queue/audit/safety/cost and rollback available;
- [ ] owner/on-call/escalation/contact/calendar/training conditions valid for target;
- [ ] user disclaimer, privacy notice, support-hours/limitations and status copy approved;
- [ ] incident channel/status communication mechanism approved without fake response promise.

## 4. Go/no-go meeting

Release Owner presents exact candidate, target, gate summary, changes, rollback target, open risks/waivers and observation plan. Each mandatory domain owner records `approve`, `reject` or `blocked` with reason. Any missing response is `blocked`; any hard gate rejection is `NO_GO`. Production cannot be `CONDITIONAL_GO` on a failed gate.

Decision record uses `RELDEC-*`, candidate/evidence hash, approvals, timestamp and authorized window.

## 5. Launch execution sequence

1. Confirm authorized environment/account/region and freeze candidate/config.
2. Capture pre-change health, task definitions, config versions, DB schema, queue/backlog and active AI/corpus pointers.
3. Verify backup/reference and rollback artifacts accessible; do not modify them.
4. Apply backward-compatible infrastructure/schema changes through approved pipeline.
5. Verify schema/health with synthetic smoke; abort before app rollout on failure.
6. Deploy API/worker/web immutable task definitions per approved ECS platform strategy.
7. Wait for readiness and run system/authz/audit/correlation smoke tests.
8. Activate feature/config/AI bundle in the approved order, default-safe, with exact version checks.
9. Run P0 synthetic canaries: grounded citation, schedule own-data, ticket preview/confirm idempotency, handover fallback, staff scope, safe-mode toggle.
10. Observe declared health/error/latency/queue/security/AI/cost signals; record decision to continue, hold or rollback.
11. Announce completion only after persistence/runtime/evidence confirms it; hand off to post-launch plan.

Every step records actor, start/end, command/pipeline ID, before/after version, result and evidence. Manual unrecorded configuration edits are prohibited.

## 6. Immediate abort/rollback criteria

Rollback or contain immediately on:

- auth bypass, cross-user exposure, secret/PII egress or unexpected public access;
- unauthorized/unconfirmed/duplicate write or false success;
- critical safety miss/invented contact/intervention or S1 injection bypass;
- mandatory audit/correlation unavailable for high-impact action;
- data corruption/loss, incompatible migration or unreconcilable write state;
- readiness instability or P0 smoke failure;
- latency/error/backlog/cost hard gate breach attributable to release;
- runtime image/config/AI version differs from manifest;
- monitoring/evidence is unavailable, making safety unknowable.

Security/Privacy/SRE may contain without waiting for a business vote. Recovery requires owner approvals in RACI.

## 7. Response decision tree

```text
hard-stop security/privacy/data-integrity?
  yes -> SUSPENDED/READ_ONLY as scoped -> preserve evidence -> rollback/incident
  no -> AI/model/corpus-only regression?
          yes -> SEARCH_ONLY/DEGRADED_NO_LLM -> revert AI bundle/corpus pointer
          no -> external integration failure?
                  yes -> disable affected capability -> reconcile unknown writes
                  no -> application/infrastructure regression?
                          yes -> rollback task definitions/config; verify schema compatibility
                          no -> hold and investigate with no further exposure
```

## 8. Rollback procedure

1. Declare `RBK-*`, incident/change ID, scope and decision authority.
2. Stop further promotion/config edits; preserve logs/traces/audit and failed artifact.
3. Activate safe mode appropriate to risk before rollback if continued traffic can harm.
4. Revert application to previous verified ECS task definitions/image digests and previous compatible config.
5. Revert prompt/model/tool-policy/corpus pointer independently when cause is AI asset.
6. Do not run destructive database down-migration automatically. Prefer backward-compatible previous code; if impossible, restore/forward-repair only under separate authorized recovery plan.
7. Reconcile outbox, idempotency and `unknown` writes before reopening mutation routes; never blind replay.
8. Run rollback smoke: identity/authz, P0 read, audit/correlation, safe fallback, object counts and version/digest checks.
9. Keep affected capability disabled until gate owners approve recovery; communicate truthful status.
10. Close execution only after evidence bundle, affected-user assessment and retrospective owner are recorded.

## 9. Rollback verification oracle

Rollback passes only when runtime matches prior manifest, readiness and required P0 probes pass, schema remains compatible, no new side effect occurred, audit/event chain is complete, queue/backlog is understood and hard-stop signal is absent. “Deployment completed” alone is not pass.

## 10. Communication

Messages state environment/simulation, affected capability, observed impact, safe alternative, known/unknown state and next approved update channel. Do not promise human response time, claim external contact, expose security detail/PII or say an action succeeded before authoritative confirmation.

## 11. Evidence

Launch/rollback evidence includes `RELDEC/RBK` IDs, manifest/evidence hashes, owner approvals, timeline, pipeline/task IDs, config/schema/AI pointer before-after, probe results, alerts/incidents, reconciliation counts, communications and residual risk. It feeds `GATE-REL-011` and post-launch review.
