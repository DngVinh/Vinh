---
document_id: "DOC-OPS-008"
version: "1.0.0"
status: "draft"
owner: "Operations Lead"
approvers: ["SRE Lead", "Security Lead", "Application Lead", "Incident Response Owner"]
last_updated: "2026-09-22"
---

# Operations runbooks

## 1. Runbook contract

Mỗi runbook có trigger, severity, authority, safe diagnostics, containment, recovery, validation, escalation và evidence. Machine index ở `infra/specs/runbooks.yaml`.

Universal first response:

1. Acknowledge alert; open incident with UTC timestamps and owner.
2. Verify environment/release; do not assume alarm is production.
3. Preserve logs/audit/diff; do not delete queue/data/log or rotate blindly.
4. Freeze concurrent deploy/config for affected area.
5. Assess security/privacy and synthetic-vs-real data classification.
6. Choose declared degraded state; communicate only approved facts.
7. Apply reversible, bounded action; verify metrics and user behavior.
8. Record commands/actions/results without secret/PII.

Never run broad delete/reset/cleanup, force deployment, DLQ purge, database truncate, key deletion or unaudited console change.

## 2. `RB-API-001` — Web/API unavailable or high 5xx

**Trigger:** `ALM-EDGE-001`, `ALM-API-001`, no healthy targets, fast SLO burn. **Owner:** SRE. **Initial severity:** SEV-1 if broad; otherwise SEV-2.

1. Confirm CloudFront/WAF/ALB/ECS and route scope; compare external synthetic and internal health.
2. Check release/config annotation, target health reason, task stop reason, CPU/memory, DB pool and dependency latency.
3. If correlated with release, stop rollout; verify previous accepted digest/config and migration compatibility.
4. Roll back stateless image/config only when schema compatible. Otherwise set `READ_ONLY`/maintenance and forward-fix.
5. If capacity, scale within approved max only after DB/provider/budget headroom check.
6. Validate health, authz negative smoke, SSE, audit delivery and error budget recovery.
7. Escalate Security if WAF spike/auth anomalies; Data owner if DB saturation.

## 3. `RB-DATA-001` — RDS outage/failover/pool saturation

**Trigger:** `ALM-DB-001..004`. **Owner:** Data/SRE. **Severity:** SEV-1 for unavailable authoritative writes.

1. Set personal/write capability read-only/unavailable; never use Redis as truth.
2. Inspect RDS event/failover, connections, storage, CPU/I/O and app pool waits; do not expose endpoint/credential in incident chat.
3. During managed failover, allow bounded app reconnect; stop retry storm and noncritical workers.
4. For pool saturation, cap worker/API concurrency and identify release/query class; do not raise DB max without formula/review.
5. Verify transaction integrity, idempotency records, outbox age and migration state after recovery.
6. Run synthetic read/write/duplicate tests; clear degraded mode only after data owner accepts.
7. If corruption/regional loss suspected, invoke `RB-DR-001`; do not restore over source production.

## 4. `RB-CACHE-001` — Redis unavailable or failover

1. Confirm cache endpoint/replication event and distinguish network/TLS/auth.
2. API uses approved safe bypass for public/read caches; security-sensitive rate/authorization cache fails according to fail-closed policy.
3. Reduce load if DB impact rises; disable nonessential expensive reads.
4. Recover replication group through IaC/managed failover, not by treating snapshot as business truth.
5. Validate cross-user cache isolation, rate limit behavior and no stale policy before normal state.

## 5. `RB-ASYNC-001` — Outbox/queue backlog or DLQ

**Trigger:** oldest age/backlog/DLQ/outbox alarms. **Owner:** Application + SRE.

1. Identify exact queue/job schema/release; compare outbox publish vs consume rate.
2. Stop noncritical ingestion if it starves critical class.
3. Inspect a bounded synthetic/safely redacted sample and consumer error codes; do not dump payload.
4. Fix consumer/dependency or scale within approved max and DB/provider limits.
5. DLQ redrive prerequisites: incident contained, schema compatible, consumer idempotency verified, destination correct, bounded batch/rate approved.
6. Redrive small canary batch, verify inbox receipt/side effect, then continue bounded batches.
7. Never purge DLQ or mark outbox published manually. Reconcile duplicates/unknown outcomes explicitly.

## 6. `RB-LLM-001` — DeepSeek/provider degraded

1. Confirm gateway error class, latency/rate limit/circuit and egress; do not log provider body/key/prompt.
2. Enter `DEGRADED_NO_LLM`; expose deterministic search, existing ticket/query and handover as approved.
3. Do not silently switch model/provider, increase retries/token cap or use personal key.
4. If config/release caused issue, roll back provider adapter/prompt/model alias only to accepted eval version.
5. Validate fake provider path, redaction, evidence gate and cost telemetry.
6. Recover circuit after bounded probe/cooldown; run affected safety/RAG eval before full restore if version changed.
7. Escalate Privacy/Security on unexpected data location, PII block or provider incident.

## 7. `RB-REL-001` — Bad release/configuration

1. Stop deployment and capture release/image/config/template/migration IDs.
2. Classify app-only, config, schema, IAM/network or data corruption.
3. App-only: roll back to prior accepted digest. Config: restore prior immutable config if safe. Schema: forward-fix/compatible rollback only.
4. Infra: use reviewed CDK diff; no console patch except break-glass, and record drift.
5. Verify OpenAPI smoke, authz denial, synthetic guard, audit, queue, AI safety sample and dashboards.
6. Mark failed release; do not overwrite artifacts/evidence.

## 8. `RB-AUDIT-001` — Audit delivery unavailable

1. Enter `READ_ONLY` for write, C2/C3 and admin paths; bounded public FAQ may continue per policy.
2. Verify exporter, permissions, destination health and clock; preserve local bounded buffer only if approved/encrypted.
3. Do not route audit into ordinary app logs or grant app delete/write-admin rights.
4. Restore append-only path; reconcile sequence/gaps/duplicates.
5. Security Operations accepts integrity evidence before reopening high-risk paths.

## 9. `RB-SEC-001` — Secret/PII/synthetic guard incident

1. Set at least SEV-1 for real PII/secret or cross-user exposure; invoke `SEC-IR-*`.
2. Stop affected egress/tool/index/log flow and preserve minimal evidence.
3. Revoke/rotate exact credential if exposure plausible; do not print it or rotate unrelated secrets.
4. Quarantine dataset/document/release; keep synthetic-only guard fail closed.
5. Privacy/Legal determines notification; operations MUST not notify external parties autonomously.
6. Run DLP/authorization/canary and downstream deletion/reconciliation before recovery.

## 10. `RB-DR-001` — Restore and regional disaster

Detailed procedure in `BACKUP_RESTORE_DR.md`:

1. Declare disaster and recovery point; identify approved target account/region and legal authorization.
2. Restore to isolated new resources, never overwrite source.
3. Reconstruct network/security/compute from accepted CDK/templates and exact image digests.
4. Restore RDS/S3/config/secrets through approved mechanisms; Redis is rebuilt empty.
5. Replay deletion tombstones and reconcile outbox/queues before opening traffic.
6. Run checksum, migration, authz, audit, AI/provider and synthetic smoke.
7. Update DNS/traffic only after Incident Commander, Data, Security and Product acceptance.

## 11. `RB-COST-001` — Cost anomaly or budget alarm

1. Confirm Cost Explorer/Budgets signal, account/environment/tag and service contribution.
2. Check traffic/security abuse, log cardinality/retention, NAT/endpoint transfer, runaway tasks, LLM token/request volume and orphan approved stacks.
3. Apply reversible quota/scale/feature degradation within approved minimum; never disable security/audit/encryption.
4. Suspected abuse invokes security incident. Paid resource deletion needs exact target authorization; report cleanup candidates instead.
5. Update forecast/formula and Finance owner; retain evidence.

## 12. `RB-BACKUP-001` — Backup/restore job failure

1. Confirm exact resource/vault/job/error and last successful recovery point.
2. Freeze stateful infrastructure changes if recovery coverage at risk.
3. Check role/KMS/vault policy/capacity without broadening permission.
4. Retry only safe backup operation; do not delete failed/recovery points.
5. Run isolated restore validation if gap could violate RPO.
6. Escalate if no recovery point within target or immutable vault control drifted.

## 13. Exit evidence

Every runbook execution records incident ID, environment, alarm, start/ack/contain/recover times, release/config, actions/approvers, metrics before/after, verification, residual risk and follow-ups. Evidence references are restricted/hashed; no raw C2/C3 content.

