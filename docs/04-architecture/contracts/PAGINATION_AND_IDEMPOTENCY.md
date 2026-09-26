---
document_id: "DOC-API-004"
version: "1.0.0"
status: "reviewed"
owner: "API Architect"
approvers: ["Solution Architect", "Data Architect", "Security Lead"]
last_updated: "2026-09-21"
---

# Pagination, concurrency and idempotency

## 1. Cursor pagination

| ID | Rule |
|---|---|
| API-PAGE-001 | List endpoint MUST dùng opaque cursor; offset pagination bị cấm cho mutable collections. |
| API-PAGE-002 | Default `limit=20`, minimum 1, maximum 100 trừ operation ghi khác trong OpenAPI. |
| API-PAGE-003 | Cursor MUST bind route, actor/scope, normalized filters, sort, boundary values, expiry và schema version. |
| API-PAGE-004 | Cursor MUST được authenticated (HMAC/AEAD) và base64url encoded; client không được suy diễn nội dung. |
| API-PAGE-005 | Invalid/tampered/expired cursor trả `422 VALIDATION_FAILED` với pointer `/cursor`; không fallback trang đầu. |
| API-PAGE-006 | Response order MUST deterministic với unique tiebreaker `id`. |

### 1.1 Canonical ordering

| Resource | Default order | Cursor boundary |
|---|---|---|
| tickets (student) | `updated_at DESC, id DESC` | updated_at + id |
| staff queue | `priority_rank DESC, created_at ASC, id ASC` | priority + created_at + id |
| conversations | `last_message_at DESC NULLS LAST, id DESC` | timestamp/null marker + id |
| schedule | `starts_at ASC, id ASC` | starts_at + id |
| knowledge sources | `updated_at DESC, id DESC` | updated_at + id |
| handovers | `risk_rank DESC, created_at ASC, id ASC` | risk + created_at + id |

Cursor payload logical form (never exposed unsigned):

```json
{
  "v": 1,
  "resource": "tickets",
  "scope_hash": "sha256:...",
  "filter_hash": "sha256:...",
  "sort": "updated_at_desc_id_desc",
  "boundary": {"updated_at": "2026-09-21T10:30:00Z", "id": "..."},
  "exp": "2026-09-21T10:45:00Z"
}
```

Implementation MUST use keyset comparison matching exact sort direction. Items inserted before boundary MAY appear only in a refreshed list; item duplication across pages MUST be prevented for an unchanged ordering key. If ordering keys mutate between requests, clients MAY observe movement; API makes no snapshot-isolation promise unless operation explicitly supplies snapshot token.

## 2. Filters

- Filters MUST be explicit allowlisted query parameters; no arbitrary field/operator DSL in V1.
- Multi-value enum filter uses repeated query parameters, not comma parsing.
- Date range is `[from, to)`; `to` exclusive.
- Server MUST normalize filters before cursor hash. Reusing cursor with different filter returns `422`.
- Search strings limited length, Unicode normalized and never interpolated into SQL.

## 3. Optimistic concurrency

| ID | Rule |
|---|---|
| API-CONC-001 | GET mutable aggregate MUST return `ETag: "<version>"`. |
| API-CONC-002 | State-changing command on existing aggregate MUST require `If-Match`. |
| API-CONC-003 | Missing `If-Match` returns `428 PRECONDITION_REQUIRED` (register when endpoint enabled); stale value returns `409 VERSION_CONFLICT`. |
| API-CONC-004 | Update query MUST include `WHERE id=? AND version=?` and increment version atomically. |
| API-CONC-005 | Idempotent replay of a previously completed command returns stored result even if current version advanced, provided request fingerprint matches. |

## 4. Idempotency

### 4.1 Operations requiring key

`Idempotency-Key` is mandatory for:

- confirm action;
- create ticket after confirmation;
- create/cancel room booking;
- submit/cancel document request;
- transition ticket/handover;
- publish knowledge version;
- any operation invoking an external write.

Pure GET/HEAD MUST NOT create idempotency records.

### 4.2 Key and scope

| ID | Rule |
|---|---|
| API-IDEM-001 | Key is caller-generated opaque 16–128 visible ASCII characters; UUID recommended but not required. |
| API-IDEM-002 | Uniqueness scope is `(actor_user_id, operation_id, key)`. Service credentials use service subject. |
| API-IDEM-003 | Record MUST bind canonical request fingerprint including path IDs, normalized body, relevant headers and action preview hash. |
| API-IDEM-004 | Same scope/key/fingerprint MUST return same status, semantic body and resource reference. Volatile headers MAY differ. |
| API-IDEM-005 | Same scope/key with different fingerprint MUST return `409 IDEMPOTENCY_KEY_REUSED`. |
| API-IDEM-006 | Concurrent duplicate while first execution active returns `409 IDEMPOTENCY_IN_PROGRESS` + `Retry-After`, hoặc waits within a short bounded server timeout then replays result. Behavior MUST be consistent per operation. |
| API-IDEM-007 | Key TTL minimum 24 hours for internal V1 writes; action confirmations MUST retain dedupe evidence at least through business audit window. |

Canonical fingerprint MUST exclude request ID, tracing headers, Authorization token and field ordering; MUST include semantic content type, actor, operation and normalized payload. Canonicalization algorithm/version is persisted.

### 4.3 Processing algorithm

```text
1. Authenticate and validate request.
2. Require Idempotency-Key.
3. Compute canonical fingerprint.
4. Atomically insert IN_PROGRESS record or load existing record.
5. Existing + different fingerprint -> 409.
6. Existing + COMPLETED -> replay stored semantic result.
7. Existing + IN_PROGRESS -> bounded wait or 409 in-progress.
8. Execute guarded transaction/external workflow.
9. Store terminal result/reference before releasing lock.
10. Return response.
```

Crash after side effect nhưng trước response MUST được recover bằng durable execution/outbox/provider receipt. Implementation MUST NOT simply mark failed and retry external write.

## 5. Action confirmation binding

The idempotency record for `confirmAction` MUST include:

- authenticated actor ID;
- preview ID;
- action type;
- preview payload hash;
- confirmation policy version;
- requested operation ID;
- client key.

If preview status already `SUCCEEDED`, replay returns original action result. If `EXPIRED`/`CANCELLED`, return terminal problem. Confirmation token mismatch MUST NOT reveal expected hash/token details.

## 6. Acceptance evidence và failure behavior

Tests MUST cover page traversal with equal sort keys, cursor tampering, filter mismatch, expiry, max limit, concurrent duplicate requests, same key/different body, server crash simulation, replay after success and room-booking race. Nếu durable result replay không thể bảo đảm cho một external provider, task MUST stop với `IDEMPOTENCY_GUARANTEE_GAP` và không enable write integration.
