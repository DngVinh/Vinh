---
document_id: "DOC-OPS-010"
version: "1.0.0"
status: "draft"
owner: "FinOps and Capacity Owner"
approvers: ["Platform Lead", "SRE Lead", "Finance Owner", "Product Owner"]
last_updated: "2026-09-22"
---

# Capacity and cost model

## 1. Planning inputs

| Variable | Baseline hypothesis | Source |
|---|---:|---|
| `U_students` | 5,000 | `ASM-001` |
| `U_staff` | 100 | `ASM-001` |
| `C_peak` | 200 concurrent users | `ASM-001` |
| `Q_chat_day` | 10,000 chat requests/day | `ASM-002` |
| `Q_ticket_day` | 1,000 ticket actions/day | `ASM-002` |
| `D_documents` | 150–300 | `ASM-003` |
| `D_chunks_stress` | up to 100,000 pages/chunks equivalent | `ASM-003` |
| `A_target` | 99.9% AI/read monthly | `ASM-006` |

Đây là hypothesis, không hard limit. Mỗi limit thực tế phải có config, metric, error behavior và owner.

## 2. Capacity profiles

| Profile | Compute/data shape | Use |
|---|---|---|
| `local` | one container/runtime, local Postgres/Redis/fakes | development/test |
| `staging-min` | web/api/worker minimum one task each when not running HA drill; smallest compatible RDS/cache selected after benchmark | synthetic integration; not HA claim |
| `staging-parity` | web/api ≥2, worker ≥2, RDS/cache Multi-AZ when testing | load/failover/release evidence |
| `production-baseline` | web=2, api=2, worker=2 across ≥2 AZ; Multi-AZ RDS/cache | starting design, not final sizing |

CPU/memory/instance classes remain unresolved until benchmark. Agent MUST not select “latest cheapest” or claim capacity from vCPU count alone.

## 3. Throughput model

```text
requests_peak_per_second =
  (daily_requests * peak_hour_fraction * peak_minute_factor) / 3600

required_api_concurrency =
  requests_peak_per_second * p95_request_duration_seconds * headroom_factor

required_api_tasks =
  ceil(required_api_concurrency / tested_concurrency_per_task)

worker_arrival_rate = jobs_in_peak_window / peak_window_seconds
worker_service_rate = workers * concurrency_per_worker / p95_job_duration_seconds
stable_queue requires worker_service_rate > worker_arrival_rate * headroom_factor
```

`peak_hour_fraction`, factors, durations and per-task concurrency come from test/telemetry. Until measured, capacity is `unverified`.

## 4. Database budget

```text
total_connections =
  api_max_tasks * api_pool_size
  + worker_max_tasks * worker_pool_size
  + migration_connections
  + operations_reserve

total_connections <= tested_db_connection_limit * safe_utilization_ratio
```

`web_db_connections=0`. Separate budget for OLTP, retrieval and ingestion query time/I/O. Load test includes lexical + pgvector + transaction + outbox concurrency. RDS Proxy is considered only after pool/churn evidence and cost comparison.

Storage forecast:

```text
db_monthly_growth_gb =
  business_rows + messages + audit_metadata + outbox/inbox
  + knowledge_metadata + vectors + index_overhead

s3_monthly_growth_gb = source_objects + artifacts + logs + backups
```

Each term uses measured average bytes × volume × retention; compression/index/replica overhead must be measured.

## 5. LLM/token budget

```text
llm_input_tokens_month = sum(request_count[purpose] * avg_input_tokens[purpose])
llm_output_tokens_month = sum(request_count[purpose] * avg_output_tokens[purpose])

llm_cost_month =
  llm_input_tokens_month / billing_unit * current_input_price
  + llm_output_tokens_month / billing_unit * current_output_price
  + any_current_provider_fixed_or_cache_charges
```

Prices MUST be fetched from approved provider pricing at review time and timestamped/currency-normalized; this document intentionally records no price. Add retry/repair/rerank calls and eval traffic separately. Hard controls: per-turn call/token cap, concurrency cap, rate limit, circuit, daily/monthly budget signal and degraded mode.

## 6. AWS cost formula

Monthly estimate uses current AWS Pricing Calculator/price list for approved Region:

```text
C_total = C_fargate + C_rds + C_redis + C_alb + C_cloudfront_waf
        + C_nat + C_endpoints + C_s3 + C_sqs + C_logs_traces
        + C_kms_secrets_backup + C_dns_monitoring + C_data_transfer
        + C_llm + C_contingency
```

| Component | Units to collect |
|---|---|
| Fargate | vCPU-hours, GB-hours by service/task, ephemeral storage, tasks count |
| RDS | instance-hours, storage GB-month, IOPS/throughput, backup beyond allowance, data transfer |
| Redis | node-hours, replicas, backup/storage/transfer if applicable |
| ALB | hours + LCU dimensions: new/active connections, processed bytes, rules |
| CloudFront/WAF | requests, transfer, WAF requests/rules |
| NAT | gateway-hours + processed GB; compare interface endpoint hours/GB |
| VPC endpoints | endpoint-AZ-hours + processed GB |
| S3 | storage by class, requests, lifecycle/replication, retrieval/transfer |
| SQS | API requests, payload chunks, KMS calls where applicable |
| Observability | log ingest/archive/query, custom metrics, alarms, traces/canaries |
| KMS/Secrets/Backup | keys/API calls, secret count/API calls, protected GB/job/copy |
| DeepSeek | input/output/cache tokens and approved provider charges |

## 7. Cost decision comparisons

### NAT vs endpoints

```text
C_nat = nat_gateway_hours * nat_hour_price + nat_processed_gb * nat_gb_price
C_vpce = sum(endpoint_az_hours * endpoint_hour_price)
       + endpoint_processed_gb * endpoint_gb_price
```

Choose per measured traffic and security/reliability need; no blanket claim endpoints always cheaper.

### HA premium

Report incremental cost for second task/AZ, RDS Multi-AZ, Redis replica/Multi-AZ, duplicate NAT and backup copies. Production HA cannot be silently removed to meet budget; trade-off requires Service/Product/Security/Finance review and ADR if invariant changes.

### Logging

```text
C_observability = ingest_gb * price_ingest
                + archived_gb_month * price_storage
                + query_scan_gb * price_query
                + custom_metric_count * metric_price
                + trace_count * trace_price
```

Reduce cost by allowlist logging, sampling and retention—not by dropping security audit or redaction controls.

## 8. Budget and anomaly controls

- `OQ-008` blocks production until monthly budget/currency/owner approved.
- Budget thresholds 50/75/90/100% of approved amount; alarm creation remains disabled/blocking when amount is null.
- Daily forecast, service/environment/tag variance and unallocated-cost metric.
- Cost anomaly routes to `RB-COST-001`; suspected abuse also to security.
- Quotas: task max, queue concurrency, LLM token/request budget, log ingestion/cardinality, upload/corpus size.
- Automatic cost action may throttle/degrade noncritical AI/ingestion within policy; MUST not disable encryption, audit, backup or auth.

## 9. Benchmark plan

Workloads:

- browse/login/schedule/ticket reads;
- chat SSE with fake and separately approved DeepSeek;
- hybrid retrieval exact ID/paraphrase/no-diacritic;
- action preview/confirm/idempotent duplicate;
- ingestion/outbox/SQS duplicate/backlog;
- 200 concurrent mixed users, burst/soak and one-AZ reduced capacity;
- corpus up to 100,000 chunk equivalents.

Capture throughput, p50/p95/p99, errors, CPU/memory, pool wait/connections, DB query/I/O/storage, Redis, queue age, token/call, log volume and unit cost. Never use real student traffic/data.

## 10. Capacity decision record

```yaml
capacity_decision:
  id: "CAP-..."
  environment: "staging"
  release_id: "..."
  workload_model_version: "..."
  dataset_manifest: "..."
  measured_at: "RFC3339"
  selected_profile: "..."
  resource_units: {}
  max_safe_load: {}
  bottleneck: "..."
  monthly_cost_estimate:
    currency: "USD"
    pricing_as_of: "YYYY-MM-DD"
    calculator_ref: "..."
    amount: null
  approved_by: []
```

Any null required production value keeps status `not_verified`.

