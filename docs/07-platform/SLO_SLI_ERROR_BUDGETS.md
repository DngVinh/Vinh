---
document_id: "DOC-OPS-007"
version: "1.0.0"
status: "draft"
owner: "Service Reliability Owner"
approvers: ["Product Owner", "SRE Lead", "Application Lead", "AI Quality Lead"]
last_updated: "2026-09-22"
---

# SLO, SLI and error budgets

## 1. Status

Các mục tiêu dưới đây là **engineering design targets**, không phải SLA thương mại. `ASM-006` duyệt mục tiêu 99.9% tháng cho AI/read-only; các target chi tiết phải được load/pilot telemetry và Service Owner phê duyệt trước cam kết.

AI correctness/safety không được đổi thành availability SLO. Release AI vẫn dùng eval gates riêng.

## 2. Measurement rules

- Window: rolling 30 days cho operational view; calendar month cho business report.
- Source: edge/ALB + application metric reconciled; synthetic probe là outside-in corroboration, không sole source.
- Good/valid event được định nghĩa theo route/operation và outcome code, không parse text.
- Exclusion chỉ cho synthetic monitor invalid, approved maintenance và request bị client cancel trước server work. Authz deny, rate limit do capacity, dependency failure và degraded unsupported response không tự động bị loại.
- Missing telemetry là control failure; không tính mặc định là success.

## 3. SLO catalog

### `SLO-WEB-001` — Web availability

- Population: valid HTTPS navigation/request tới public web entry, excluding static client abort.
- Good: edge trả expected 2xx/3xx hoặc approved 4xx; không 5xx/origin error.
- Target: 99.9% / month, design target.
- Data: CloudFront/ALB/application reconcile.
- Owner: Web + SRE.

### `SLO-API-001` — Read API availability

- Population: authenticated valid read operations in OpenAPI (`GET`, plus non-mutating health excluded from product SLO).
- Good: expected 2xx hoặc business 4xx do caller; 5xx/503/timeout is bad. Unauthorized attempts outside valid population.
- Target: 99.9% / month (`ASM-006`).
- Slice: route family and capability state; overall success cannot hide schedule/ticket failure.

### `SLO-API-002` — Read latency

- Population: good eligible read requests excluding SSE and provider-generated response.
- SLI: p95 end-to-end server duration.
- Initial threshold: `T_read_p95_ms`, value MUST come from staging benchmark; until set, status `not_verified`.
- Target ratio: `P_read_latency`, owner-approved; no fabricated millisecond claim.

### `SLO-STREAM-001` — Chat stream startup

- Population: accepted `API-CONV-004` requests in supported capability state.
- Good: first canonical SSE event before `T_stream_first_event_ms` and exactly one terminal event.
- Target: unset until edge/DeepSeek/fake benchmark. Provider outage responses that enter declared degraded mode are measured separately, not silently good.

### `SLO-WRITE-001` — Confirmed internal action acceptance

- Population: valid, authorized, unexpired confirmations with new or replayed idempotency key.
- Good: accepted/replayed durable `ActionExecution` within `T_write_accept_ms`, without duplicate effect.
- Target: proposed `P_write_accept`; MUST be approved before production.
- Any duplicate side effect is a critical correctness incident regardless of ratio.

### `SLO-ASYNC-001` — Critical event enqueue

- Population: committed critical handover/outbox events.
- Good: published/visible in intended queue within 5 seconds (`ASM-009`).
- Target ratio: proposed 99.9%; human response time is explicitly outside this SLO until staffing approved.

### `SLO-ASYNC-002` — Normal async completion

- Population: valid jobs excluding quarantined poison messages.
- Good: terminal success/business-failure within class-specific threshold.
- Thresholds are in queue config and MUST derive from service catalog/load evidence; not set globally here.

### `SLO-RECOVERY-001` — Data recovery

- RPO target: ≤15 minutes.
- RTO target: ≤60 minutes from incident declaration/restore start definition recorded by drill.
- Status: `not_verified` until timestamped isolated restore drill passes end-to-end checksum/smoke.
- Regional disaster objective cannot be claimed while cross-location backup/region approval is unresolved.

## 4. Error budget math

For event SLO:

```text
eligible = total_events - explicitly_valid_exclusions
bad = eligible - good
allowed_bad = eligible * (1 - target_ratio)
budget_remaining = allowed_bad - bad
budget_remaining_ratio = max(0, budget_remaining / allowed_bad)
```

For time-based availability:

```text
allowed_bad_minutes = window_minutes * (1 - target_ratio)
```

At 99.9%, use formula against actual window; docs/pipeline MUST không hard-code a rounded allowance as universal truth.

Multi-window burn rate:

```text
burn_rate = observed_bad_ratio / (1 - target_ratio)
```

## 5. Budget policy

| Budget state | Condition | Action |
|---|---|---|
| Healthy | >50% remains and no critical correctness/security event | Normal delivery |
| Watch | 25–50% remains or sustained elevated burn | SRE review; reliability work prioritized |
| Freeze candidate | 0–25% remains or fast-burn alert | Stop nonessential risky release; owner decision |
| Exhausted | ≤0% | Feature release freeze except recovery/security; incident/problem review |

Security breach, cross-user disclosure, unconfirmed write, duplicate side effect, real-data leak or citation safety violation MAY freeze release independent of error budget. Error budget never authorizes unsafe behavior.

## 6. Burn-rate alerts

Exact executable thresholds live in `alarms.yaml`. Baseline method:

- fast burn: high multiple over short + medium windows, page;
- slow burn: lower multiple over hours/day, ticket;
- absolute availability symptom alarms protect before enough volume;
- low-traffic service uses synthetic probe and consecutive failure, avoiding unstable ratios.

Initial burn multipliers/periods are operational defaults subject to traffic validation; changes require SRE review, not silent tuning to reduce pages.

## 7. Dependency and degraded-mode accounting

- DeepSeek outage is bad for supported AI-generated capability, but deterministic search/ticket capability can remain good in its own SLO.
- Redis safe bypass remains good only if latency and security behavior pass.
- SQS outage is bad for async publication age, not necessarily immediate API durability when outbox commit succeeds.
- Planned maintenance exclusion requires prior approval, bounded window and transparent status; emergency maintenance remains visible in incident reporting.
- Client/business validation errors are not availability failures, but spikes are monitored for UX/security.

## 8. Reporting

Monthly report includes target/status, numerator/denominator, exclusions, budget burn, top error classes, release/config changes, dependency contribution, incidents and action owners. Report MUST label synthetic/staging data and MUST not claim production performance from test environment.

## 9. Acceptance

- Queries reproduce SLI from synthetic fixture and handle missing/duplicate telemetry.
- Route/error classification reviewed against OpenAPI/error model.
- Alert fixtures verify fast/slow burn and recovery.
- Dashboard links each SLO to runbook and release annotations.
- Restore objective only changes to `verified` with drill artifact, measured timestamps and approver.

