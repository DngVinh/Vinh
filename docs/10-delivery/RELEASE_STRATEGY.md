---
document_id: "DOC-DEL-004"
version: "1.0.0"
status: "reviewed"
owner: "Release Engineering Lead"
approvers: ["Architecture Lead", "Quality Lead", "Security Lead", "SRE Lead"]
last_updated: "2026-09-22"
---

# Release strategy

## 1. Principles

Build once, verify once per immutable candidate, promote the same digests. Configuration is externalized and versioned; secrets remain in approved secret manager. Application release, data migration, infrastructure change and AI asset promotion are separately observable but coordinated by one release manifest.

No production deployment is authorized by this plan.

## 2. Versioning and release units

Use semantic product versioning:

- major: incompatible public behavior/contract or explicitly approved major product change;
- minor: backward-compatible capability increment;
- patch: backward-compatible defect/security fix without scope addition.

Contracts, database schema, prompts, models, corpus/index, tool registry and infrastructure each retain independent immutable version/hash in the product release manifest.

```yaml
release_manifest:
  candidate_id: RC-<semver>-<sequence>
  source_revision: <git-sha>
  web_image_digest: sha256:<64-hex>
  api_image_digest: sha256:<64-hex>
  worker_image_digest: sha256:<64-hex>
  infrastructure_revision: <hash>
  database_schema_version: <version>
  openapi_hash: sha256:<64-hex>
  tool_registry_version: <version>
  config_hashes: {}
  dataset_corpus_index_hashes: {}
  model_prompt_policy_versions: {}
  sbom_refs: []
  evidence_bundle_hash: sha256:<64-hex>
  previous_release_id: <id-or-null>
```

## 3. Source and integration strategy

Use short-lived task branches/worktrees with small, reviewable changes and disjoint agent write scopes. Main/trunk must remain buildable. Integrate only accepted tasks; never use force-push, destructive reset/clean or discard unrelated dirty/untracked work. Tags/releases are created only by authorized release action after gates.

## 4. Environment promotion

| Stage | Data/provider | Promotion requirement |
|---|---|---|
| Local/CI | synthetic + fake | task/PR checks |
| Integration | synthetic + fake | merge contract/integration gates |
| Staging | synthetic; fake default; approved DeepSeek candidate isolated | full candidate gates |
| Synthetic pilot | synthetic only, production-like non-production AWS | `MS-PILOT-*`, explicit non-production approval |
| Production | future approved real-data/integration policy | all gates + `MS-PROD-*` + explicit deploy approval |

Artifact is promoted, not rebuilt. Environment config differences must be allowlisted and hashed; unexpected drift blocks.

## 5. Feature and capability control

Flags are server-authoritative, typed, versioned, audited and default-safe. Required controls:

- generated answers/tools, each write capability, knowledge publish, sensitive handover and external provider can be disabled independently;
- declared modes `NORMAL`, `DEGRADED_NO_LLM`, `DEGRADED_NO_INTEGRATION`, `DEGRADED_ASYNC_BACKLOG`, `READ_ONLY`, `SEARCH_ONLY`, `MAINTENANCE` map to capability endpoint/UI;
- flag/config change requires preview/approval where high impact and creates audit event;
- client flag never grants authorization;
- expired/unknown config fails to conservative state.

Flags do not excuse incomplete security or permanently hide dead code; each temporary flag has owner/removal criterion.

## 6. Database and event compatibility

Use expand–migrate/backfill–switch–contract:

1. add backward-compatible schema/event support;
2. deploy code that reads old/new and writes approved format;
3. run bounded idempotent backfill with progress/evidence;
4. switch behavior after compatibility checks;
5. remove old field/schema only in a later explicitly approved change after rollback window.

Contracting/destructive steps are not part of the same automatic release. Old/new API and worker versions must safely overlap during ECS replacement; outbox consumers tolerate duplicate/out-of-order supported events.

## 7. ECS application rollout

Baseline rollout uses approved ECS/Fargate deployment behavior with immutable task definitions, health/readiness, capacity to replace tasks and deployment circuit breaker/automatic failure detection as defined by platform spec. Release Engineering MUST verify:

1. schema is backward compatible before application tasks;
2. API/worker/web image digests match manifest;
3. new tasks become ready and smoke probes pass;
4. error/latency/authz/audit/queue/AI hard indicators remain within gate policy;
5. previous task definitions/images/config remain available for rollback.

A blue/green or canary mechanism may be adopted only by accepted platform design/change; this document does not invent one.

## 8. AI asset promotion

Prompt/model/provider/retrieval/corpus/tool-policy changes are releaseable assets, never untracked dashboard edits. Promote an immutable bundle after `GATE-REL-005`; record versions per response. Rollback switches to the previous verified bundle/pointer without deleting failed evidence. Corpus publish is atomic pointer activation; dual-current ambiguity forces abstain/alert.

## 9. Release types

| Type | Scope | Minimum gates |
|---|---|---|
| Standard | planned capability/fix | all affected + phase mandatory gates |
| Configuration/AI asset | no image change but behavior may change | trace/contract/security/AI/ops/rollback as affected |
| Security patch | urgent containment/fix | expedited but never omits authz/data/integrity tests; retrospective required |
| Emergency disable | reversible flag/safe-mode containment | authorization, audit, post-action verification; then standard fix process |
| Documentation-only | no runtime behavior | governance/link/trace review; reclassify if behavior/contract changed |

## 10. Release evidence and custody

Release bundle contains manifest, SBOM/scans, gate results, test/eval reports, migration/rollback plan, deployment config diff, approvals, known risks/waivers and post-deploy checklist. It is content-addressed, access-controlled and redacted. Missing bundle/hash/owner yields `not_verified`.
