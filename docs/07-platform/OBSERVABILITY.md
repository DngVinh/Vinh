---
document_id: "DOC-OPS-006"
version: "1.0.0"
status: "draft"
owner: "SRE Lead"
approvers: ["Platform Lead", "Security Operations Owner", "Privacy Owner", "AI Quality Lead"]
last_updated: "2026-09-22"
---

# Observability specification

## 1. Mục tiêu

Observability phải trả lời được availability, latency, traffic, errors, saturation, dependency/degradation, AI quality proxy, queue/outbox health, release/config và cost mà không biến telemetry thành kho chứa transcript/PII/secret.

Bốn luồng được tách logical và quyền:

1. application logs;
2. metrics;
3. distributed traces;
4. immutable security/business audit.

Audit tuân `SEC-AUDIT-*`; generic log/trace không thay audit evidence.

## 2. Correlation contract

| Field | Format | Propagation | Data rule |
|---|---|---|---|
| `request_id` | UUID | edge → web/api → response | opaque, no identity |
| `trace_id`/`span_id` | W3C Trace Context | all sync calls; event link for async | no payload |
| `correlation_id` | UUID | business flow across retries/events | stable, no PII |
| `event_id` | UUID | outbox/SQS/consumer | unique, dedupe key |
| `conversation_ref` | keyed/pseudonymous ref | AI telemetry only when needed | not raw conversation UUID in broad metrics |
| `release_id` | immutable release | every signal | low cardinality |
| `config_version` | immutable version | every service signal | low cardinality |

SQS message carries `event_id`, safe correlation/trace link and schema version; MUST NOT carry raw transcript/token/secret.

## 3. Structured log schema

```json
{
  "timestamp": "RFC3339 UTC",
  "severity": "INFO",
  "service": "api",
  "environment": "staging",
  "release_id": "opaque",
  "event_name": "http.request.completed",
  "request_id": "uuid",
  "trace_id": "opaque",
  "route_template": "/v1/tickets/{ticket_id}",
  "method": "GET",
  "status_class": "2xx",
  "duration_ms": 0,
  "outcome": "success",
  "error_code": null,
  "data_classification": "INTERNAL",
  "redaction_applied": true
}
```

Required: UTC timestamp, service, environment, release, stable event name, correlation, outcome/error class, redaction marker. Route uses template, không raw path/query. Arbitrary `details`, raw request/response, prompt, tool argument and provider body are prohibited.

## 4. Redaction and cardinality

MUST redact/drop trước exporter:

- authorization/cookie/session/CSRF/API key/secret/token;
- student ID, email, phone, exact name, IP, schedule/ticket/transcript content;
- raw prompt/model response/retrieved chunk/tool payload;
- SQL values, stack trace with data, signed URL, confirmation token;
- user-provided metric label/log key/event type.

Metric dimensions allowlist: `service`, `environment`, `route_template`, `method`, `status_class`, `operation`, `dependency`, `outcome`, `queue`, `provider_alias`, `model_alias`, `prompt_version`, `release_id`, `capability_state`. No resource/user/request/event ID as metric dimension.

## 5. Metric catalog

### User-facing

| ID | Metric | Type | Dimensions |
|---|---|---|---|
| `OPS-MET-001` | `http_server_requests_total` | counter | service, route_template, method, status_class |
| `OPS-MET-002` | `http_server_duration_ms` | histogram | service, route_template, method, outcome |
| `OPS-MET-003` | `http_server_active_requests` | gauge | service |
| `OPS-MET-004` | `sse_connections_active` | gauge | service |
| `OPS-MET-005` | `sse_first_event_duration_ms` | histogram | route, outcome |
| `OPS-MET-006` | `capability_state` | gauge one-hot | state |

### Dependencies/data

| ID | Metric | Purpose |
|---|---|---|
| `OPS-MET-010` | `dependency_requests_total/duration_ms` | outcome/latency per dependency, no endpoint URL |
| `OPS-MET-011` | `db_pool_in_use/max/wait_ms` | connection saturation |
| `OPS-MET-012` | `db_query_duration_ms` | allowlisted operation class, not SQL text |
| `OPS-MET-013` | `redis_operations_total/duration_ms` | hit/miss/error/bypass |
| `OPS-MET-014` | `outbox_unpublished_total` | unpublished count |
| `OPS-MET-015` | `outbox_oldest_age_seconds` | relay health |
| `OPS-MET-016` | native SQS backlog/oldest/DLQ | worker health |
| `OPS-MET-017` | `worker_jobs_total/duration_ms` | queue/job type/outcome |

### AI/RAG/tool

| ID | Metric | Rule |
|---|---|---|
| `OPS-MET-020` | `llm_requests_total/duration_ms` | provider/model alias, purpose, outcome; no prompt |
| `OPS-MET-021` | `llm_tokens_total` | input/output, provider/model/prompt version |
| `OPS-MET-022` | `llm_circuit_state` | provider alias only |
| `OPS-MET-023` | `rag_requests_total/duration_ms` | corpus/retrieval version, outcome |
| `OPS-MET-024` | `evidence_gate_total` | pass/abstain/fail reason code |
| `OPS-MET-025` | `tool_executions_total` | tool ID/version/outcome, no payload |
| `OPS-MET-026` | `confirmation_total` | created/approved/rejected/expired/replay-blocked |
| `OPS-MET-027` | `guardrail_decisions_total` | safe reason class, severity, no content |
| `OPS-MET-028` | `external_pii_block_total` | MUST page/security alert if >0 in attempted egress |

Quality metrics (grounded correctness, citation precision/recall, sensitive-case recall) come from eval pipeline and MUST NOT be inferred solely from runtime counters.

### Security/operations

| ID | Metric | Purpose |
|---|---|---|
| `OPS-MET-030` | `authorization_decisions_total` | allow/deny/error by policy/action class |
| `OPS-MET-031` | `audit_delivery_total` | accepted/rejected/error |
| `OPS-MET-032` | `redaction_dropped_fields_total` | redaction health; no field value |
| `OPS-MET-033` | `synthetic_guard_violations_total` | non-synthetic input/config detection |
| `OPS-MET-034` | `release_info` | one-hot build/config/image identity |
| `OPS-MET-035` | `retention_job_lag_seconds` | lifecycle control |
| `OPS-MET-036` | `backup_restore_last_success_timestamp` | recovery evidence freshness |

## 6. Tracing

- Use OpenTelemetry APIs/semantic conventions with pinned SDK/collector versions.
- Trace inbound HTTP, application use case, DB operation class, cache, outbox publish, SQS consume, RAG stages, LLM gateway, tool broker and external adapter.
- Do not attach request body, prompt, retrieved text, tool args/result, SQL values, token or full URL query.
- Sampling: errors/security-relevant decisions sampled according to approved policy; normal traffic head/tail rate is config and cost-tested. C2/C3 payload still never recorded at 100% sampling.
- Async consumer creates span linked to producer trace/event rather than forging parent after long delay.
- Provider span uses alias, operation, latency, token counts and provider request ref only if safe/pseudonymous.

## 7. Health and readiness

`GET /health/live` (`API-SYS-001`) reports process only. `GET /health/ready` (`API-SYS-002`) reports generic ready/not-ready and capability state; public response MUST không lộ endpoint, version, credential or topology.

| Dependency | Readiness effect |
|---|---|
| PostgreSQL unavailable | API/worker not ready for authoritative operations |
| Redis unavailable | API may remain ready only if safe bypass and security rate policy allow |
| SQS unavailable | API may accept transactional write if outbox durable; capability marks async degraded |
| DeepSeek unavailable | API ready in `DEGRADED_NO_LLM`; generated path disabled |
| Audit unavailable | personal/write/admin fail closed; public FAQ grace only per policy |
| S3 knowledge unavailable | RAG/ingestion degraded; ticket/read capabilities may remain |

## 8. Dashboards and alarms

Machine definitions:

- `infra/specs/dashboards.yaml`: Service Overview, API/SSE, Async/Worker, Data, AI/RAG, Security/Synthetic Guard, Release/Cost.
- `infra/specs/alarms.yaml`: severity, expression, periods, missing-data behavior, owner and runbook.

Every paging alarm MUST have actionable runbook, stable owner, dedup key and recovery signal. Dashboard-only warning MUST không page. Composite alarms SHOULD suppress dependency-caused symptom storms while preserving evidence.

## 9. Retention/access

- Application logs: proposed 30 days synthetic unless narrower/approved; production value maps to retention policy.
- Traces/model/tool metadata: 90 days simulation per `PRIV-RET-007`.
- Audit: 400 days simulation per `PRIV-RET-008`, immutable policy; production unresolved.
- Access logs and security evidence have separate classification/roles.
- Dashboard viewer cannot mutate source log/audit. Application task role cannot delete log groups/streams/audit objects.

## 10. Acceptance evidence

- End-to-end correlation through web/API/outbox/SQS/worker.
- Seeded DLP test confirms prohibited values absent in exporter capture.
- Metric cardinality budget test and no user-controlled dimensions.
- Dashboard queries resolve and alarm fixtures move OK→ALARM→OK.
- Alarm notification reaches tested synthetic destination with timestamps.
- Audit sink outage triggers documented fail-closed behavior.
- Release/config/image digest visible and matches release manifest.

