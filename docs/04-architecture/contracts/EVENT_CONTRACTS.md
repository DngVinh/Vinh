---
document_id: "DOC-EVT-001"
version: "1.0.0"
status: "reviewed"
owner: "Event Architect"
approvers: ["Solution Architect", "Data Architect", "Operations Lead", "Security Lead"]
last_updated: "2026-09-21"
---

# Event contracts V1

## 1. Vì sao V1 cần event

Event được dùng cho notification, indexing, operations metrics và reliable integration sau commit. Event không thay thế synchronous authorization/validation và không được dùng để trì hoãn control bắt buộc của write action. `contracts/asyncapi/v1/asyncapi.yaml` mô tả catalog theo [AsyncAPI 3.0.0](https://www.asyncapi.com/docs/reference/specification/v3.0.0).

## 2. Delivery semantics

| ID | Rule |
|---|---|
| EVT-BASE-001 | Delivery là at-least-once; exactly-once end-to-end không được tuyên bố. |
| EVT-BASE-002 | Producer MUST ghi transactional outbox cùng aggregate transaction. |
| EVT-BASE-003 | Consumer MUST deduplicate bằng `(consumer_name, event_id)` và commit inbox receipt cùng side effect. |
| EVT-BASE-004 | Per-aggregate ordering dùng `partition_key=aggregate_id`; không có global ordering guarantee. |
| EVT-BASE-005 | Consumer MUST không phụ thuộc event arrival time; dùng `occurred_at` và aggregate version. |
| EVT-BASE-006 | Event payload MUST chứa dữ liệu tối thiểu, không raw chat, email, student code, token, secret hoặc chain-of-thought. |
| EVT-BASE-007 | Event chỉ phát sau successful commit. Failed attempts belong to audit/metrics, not domain event unless explicitly cataloged. |

## 3. Envelope

Mọi event có fields:

```json
{
  "event_id": "0199c9ac-4d7c-7f35-a1b2-1234567890ab",
  "event_type": "ticket.status_changed",
  "event_version": 1,
  "occurred_at": "2026-09-21T10:30:00Z",
  "producer": "ticket-service",
  "aggregate_type": "ticket",
  "aggregate_id": "0199c9ac-4d7c-7f35-a1b2-1234567890ab",
  "aggregate_version": 4,
  "partition_key": "0199c9ac-4d7c-7f35-a1b2-1234567890ab",
  "correlation_id": "0199c9ac-4d7c-7f35-a1b2-1234567890ab",
  "causation_id": "0199c9ac-4d7c-7f35-a1b2-1234567890ab",
  "data_classification": "INTERNAL",
  "payload": {}
}
```

`event_id` unique; `event_version` integer bắt đầu 1. `correlation_id` liên kết business flow; `causation_id` trỏ command/event trực tiếp gây ra event nếu có.

## 4. Catalog

### EVT-TICKET-001 `ticket.created.v1`

- Producer: Ticket domain.
- Consumers: notification, operations metrics, staff queue projection.
- Partition: ticket ID.
- Payload: `ticket_id`, `requester_user_id` opaque, `category`, `priority`, `queue_key`, `status`, `created_at`.
- PII: PERSONAL vì có opaque user reference; transport access restricted.

### EVT-TICKET-002 `ticket.status_changed.v1`

- Payload: `ticket_id`, `from_status`, `to_status`, `actor_type`, `reason_code`, `changed_at`.
- MUST NOT include comment body.
- Consumers MUST discard older `aggregate_version` after recording duplicate/stale telemetry.

### EVT-HANDOVER-001 `handover.queued.v1`

- Consumers: staff queue, notification, urgent operations monitor.
- Payload matches minimized subset of handover schema: IDs, queue, reason code, risk level, created time; summary omitted from broad topic.
- Critical event delivery target is operational SLO, not promise of human response.

### EVT-HANDOVER-002 `handover.status_changed.v1`

- Payload: `handover_id`, `from_status`, `to_status`, `queue_key`, `assignee_user_id` nullable opaque, `changed_at`, `reason_code` nullable.

### EVT-ACTION-001 `action.execution_completed.v1`

- Payload: `execution_id`, `preview_id`, `action_type`, `status`, `target_type`, `target_id`, `completed_at`, `failure_code` nullable.
- No normalized payload.
- Consumers: notification, metrics, reconciliation.

### EVT-KNOWLEDGE-001 `knowledge.version_published.v1`

- Payload: `source_id`, `document_version_id`, `version_label`, `content_checksum`, `effective_from`, `effective_until`, `published_at`.
- Consumers: retrieval index activation, cache invalidation, audit projection.

### EVT-KNOWLEDGE-002 `knowledge.index_requested.v1`

- This is a command-like integration message, not a domain fact; name intentionally imperative.
- Payload: `document_version_id`, `content_checksum`, `requested_at`, `index_profile_version`.
- Consumer MUST verify document version is `APPROVED`/eligible before work.

### EVT-NOTIFY-001 `notification.requested.v1`

- Payload: `notification_id`, `recipient_user_id`, `template_id`, safe structured `template_variables`, `channel`, `priority`, `dedupe_key`.
- Arbitrary HTML/text MUST NOT be accepted.

## 5. Schema evolution

- Compatible: add optional field with safe default; consumer ignores unknown fields.
- Breaking: remove/rename field, change type/meaning, make optional required, change enum semantics. Breaking change creates `.v2` event type and parallel migration.
- Producer MUST publish one semantic event version per outbox row. Dual publish needs ADR and end date.
- Event schema artifact MUST have fixtures for minimum and full valid payload plus invalid examples.

## 6. Retry, DLQ và replay

- Consumer transient failure: exponential backoff with bounded attempts.
- Permanent validation/authorization failure: DLQ with safe reason code; never retry forever.
- Replay MUST use original event ID so inbox dedupe protects already-processed consumers; targeted rebuild consumer MAY use a new consumer name/version.
- DLQ payload access is restricted and audited.
- Event cannot be manually edited in DLQ; remediation creates a new corrective event/command with linkage.

## 7. Security

- Broker authorization MUST separate producer and consumer identities by channel.
- Payload schema validation occurs at publish and consume boundaries.
- Event fields are not proof of authorization; consumer re-applies its own policy.
- Event signature/encryption transport details belong to platform ADR, but TLS and encryption at rest are mandatory production expectations.

## 8. Acceptance evidence và failure behavior

Required evidence: AsyncAPI validation, event schema fixtures, outbox atomicity test, duplicate delivery test, stale version test, DLQ test, replay test and PII scan. Nếu một consumer cần raw content/PII chưa có security/privacy approval, implementation MUST stop with `EVENT_DATA_SCOPE_BLOCKED`; không mở rộng payload.
