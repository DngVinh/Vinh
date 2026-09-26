---
document_id: "DOC-ADR-008"
version: "1.0.0"
status: "draft"
owner: "Backend Architecture Lead"
approvers: ["Architecture Lead", "Data Lead", "Operations Lead"]
last_updated: "2026-09-21"
decision_status: "proposed"
---

# ADR-008 — Transactional outbox và SQS at-least-once

## Context

Domain writes cần kích hoạt ingestion, notification, projection và integrations. Ghi DB rồi publish queue là dual write: crash giữa hai bước gây mất hoặc ghost event. SQS Standard có thể duplicate và không bảo đảm global ordering.

## Decision

Domain state và outbox event **MUST** commit trong cùng PostgreSQL transaction. Outbox relay publish tới SQS và đánh dấu receipt. Consumer **MUST** idempotent bằng `event_id`/business idempotency và atomic processed record.

SQS Standard là mặc định; FIFO chỉ dùng khi requirement ordering/dedup rõ và throughput/cost trade-off được review. Mỗi queue có DLQ/redrive policy.

## Alternatives

- Direct publish after commit: từ chối vì lost event.
- Distributed transaction/2PC: từ chối vì external systems/SQS không phù hợp và operations phức tạp.
- Kafka/MSK: chưa cần ở scale/team V1; revisit khi replay/high-throughput ordered stream là requirement.

## Consequences

At-least-once tạo duplicate và eventual consistency; cần relay, outbox cleanup, lag monitoring, idempotent consumers. Đổi lại không mất event do dual write và vận hành đơn giản hơn Kafka.

## Constraints

- Event schema versioned, minimal, không raw transcript/secret.
- Relay claim concurrent-safe; publish receipt/audit.
- Consumer ack/delete chỉ sau durable success.
- Poison message vào DLQ, không retry vô hạn.
- Outbox age và oldest message age có alarm.
- Agent **MUST NOT** claim exactly-once end-to-end.

AWS transactional outbox guidance nêu duplicate và yêu cầu idempotent consumer; SQS message có thể hiện lại sau visibility timeout ([outbox](https://docs.aws.amazon.com/en_en/prescriptive-guidance/latest/cloud-design-patterns/transactional-outbox.html), [SQS receive](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/APIReference/API_ReceiveMessage.html)).

## Acceptance and failure

Crash-point tests: before commit, after commit/before publish, after publish/before mark, consumer after effect/before ack. Duplicate/out-of-order/DLQ/redrive tests pass. Nếu handler không idempotent, queue integration **MUST** remain disabled.

Traceability: `ARCH-003`, `ARCH-006`, `ARCH-007`.

