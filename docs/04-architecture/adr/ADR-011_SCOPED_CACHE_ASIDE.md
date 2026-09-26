---
document_id: "DOC-ADR-011"
version: "1.0.0"
status: "draft"
owner: "Application Architect"
approvers: ["Architecture Lead", "Security Lead", "Privacy Owner", "Operations Lead"]
last_updated: "2026-09-21"
decision_status: "proposed"
---

# ADR-011 — Scoped cache-aside và cấm shared personal/AI-answer cache

## Context

Cache có thể giảm latency/cost nhưng dễ rò dữ liệu giữa users, trả policy hết hiệu lực hoặc bypass authorization. Next.js multi-instance cũng cần cache coordination; Redis không phải source of truth.

## Decision

V1 dùng cache-aside có scope/version/freshness. Chỉ static immutable assets và public approved knowledge được shared cache. User-specific HTML/API, final AI answer và restricted data **MUST NOT** shared cache.

Redis có thể cache config, bounded retrieval candidates không PII, short-lived personal reads với opaque subject scope và rate limits. Mọi cache hit vẫn authorize.

## Alternatives

- Cache mọi model response theo text: từ chối vì privacy, context/corpus/role mismatch.
- No cache: an toàn nhưng không tối ưu; vẫn dùng cho personal/generated path V1 khi chưa chứng minh key.
- Write-through domain cache: chưa cần; tăng consistency complexity.

## Consequences

Hit rate thấp hơn aggressive caching nhưng giảm leak/stale risk. Cache key/version/invalidation cần contract và tests. Redis outage có thể tăng latency nhưng không mất truth.

## Constraints

- Key **MUST** include corpus, algorithm, locale và authorization scope liên quan.
- Publish corpus/config/role change **MUST** invalidate bằng version bump/tag, không wildcard delete.
- Personal cache TTL/freshness explicit; no stale-while-revalidate mặc định.
- Negative cache không biến transient outage thành not-found.
- Cache/log key **MUST NOT** chứa raw student ID/query.

Next.js self-hosting docs nêu local cache không tự đồng bộ giữa nhiều instance và dynamic pages mang private/no-cache semantics ([Next.js](https://nextjs.org/docs/app/guides/self-hosting)).

## Acceptance and failure

Cross-user/role isolation tests, invalidation tests, Redis-loss test và stale-policy test phải pass. Nếu cache key dimensions không xác định đầy đủ, agent **MUST** không cache và ghi performance risk.

Traceability: `ARCH-004`, `ARCH-007`.

