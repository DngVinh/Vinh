---
document_id: "DOC-DATA-001"
version: "1.0.0"
status: "reviewed"
owner: "Data Architect"
approvers: ["Solution Architect", "Security Lead", "Product Owner"]
last_updated: "2026-09-21"
---

# Logical data model V1

## 1. Phạm vi

Tài liệu này định nghĩa aggregate boundary, định danh, quan hệ và invariant cho Campus 24/7 V1. Đây là logical model; tên index vật lý, partition và lựa chọn ORM sẽ được chốt trong thiết kế database nhưng MUST bảo toàn các invariant tại đây.

## 2. Quy tắc toàn cục

| ID | Quy tắc |
|---|---|
| DATA-MOD-001 | Primary key public và internal MUST là UUIDv7; không dùng email, student code hoặc số điện thoại làm key. |
| DATA-MOD-002 | Mọi timestamp MUST lưu UTC, dạng `timestamptz`; API serialize RFC 3339 với hậu tố `Z`. |
| DATA-MOD-003 | Mọi mutable aggregate MUST có `version` integer tăng đơn điệu để optimistic concurrency. |
| DATA-MOD-004 | V1 là single-institution. Không entity nào được thêm `tenant_id`; institution profile là cấu hình deployment. |
| DATA-MOD-005 | Synthetic identity MUST mang cờ `is_synthetic=true`; production mode MUST từ chối synthetic issuer và demo mode MUST từ chối real issuer. |
| DATA-MOD-006 | PII MUST NOT nằm trong vector embedding, event payload hoặc log. Reference bằng opaque ID khi cần. |
| DATA-MOD-007 | Mọi side effect durable MUST có `idempotency_record` và audit event tương ứng. |
| DATA-MOD-008 | Soft delete chỉ được dùng khi retention/audit yêu cầu. `deleted_at` không thay thế state machine. |
| DATA-MOD-009 | Giá trị enum trong database/API dùng `UPPER_SNAKE_CASE`; code MAY dùng enum native nhưng wire value không đổi. |
| DATA-MOD-010 | Foreign key quan trọng MUST được database enforce; application-only relation không được chấp nhận cho ownership/security boundary. |

UUIDv7 được định nghĩa trong [RFC 9562](https://www.rfc-editor.org/rfc/rfc9562.html). Nếu runtime chưa hỗ trợ UUIDv7 an toàn, implementation MUST dùng UUIDv4 và tạo ADR; không tự triển khai thuật toán UUID.

## 3. Bounded contexts và aggregate roots

### 3.1 Identity & Access

- `UserIdentity` (`DATA-ENT-001`) là aggregate root cho subject nội bộ.
- `RoleBinding` (`DATA-ENT-002`) gắn một role V1 với user và scope đơn vị.
- `StudentProfile` (`DATA-ENT-003`) chứa thông tin học vụ tổng hợp tối thiểu; không chứa credential.
- `IdentityLink` (`DATA-ENT-004`) ánh xạ `issuer + subject` ngoài sang `user_id` nội bộ.

Invariant:

- Cặp `(issuer, subject)` MUST unique.
- `student_code` MUST unique khi profile active; không được suy ra quyền từ định dạng mã.
- Chỉ bốn role theo DEC-006: `STUDENT`, `SUPPORT_OFFICER`, `KNOWLEDGE_ADMIN`, `SYSTEM_ADMIN`.
- Authorization MUST đọc identity từ verified request context, không đọc user ID do client gửi trong body.

### 3.2 Student Operations

- `ScheduleEntry` (`DATA-ENT-010`) là snapshot read model của lịch cá nhân.
- `Ticket` (`DATA-ENT-011`) là aggregate root cho yêu cầu hỗ trợ.
- `TicketEvent` (`DATA-ENT-012`) là journal append-only của transition/comment/assignment.
- `DocumentRequest` (`DATA-ENT-013`) là aggregate riêng cho yêu cầu giấy tờ; có thể liên kết một ticket hỗ trợ nhưng không dùng ticket state thay thế state nghiệp vụ.
- `Room` (`DATA-ENT-014`) và `RoomBooking` (`DATA-ENT-015`) quản lý khả dụng và booking.

Invariant:

- Sinh viên chỉ được đọc `ScheduleEntry`, `Ticket`, `DocumentRequest`, `RoomBooking` có `student_user_id` bằng actor hiện tại.
- `Ticket.status` chỉ đổi qua transition hợp lệ; mọi transition tạo một `TicketEvent` trong cùng transaction.
- Một `RoomBooking` `CONFIRMED` không được chồng thời gian với booking `CONFIRMED` khác của cùng room. Database MUST enforce bằng exclusion constraint hoặc serializable transaction tương đương.
- `DocumentRequest` và `RoomBooking` là write action; tạo/chốt MUST có `ActionPreview` đã confirm.

### 3.3 Conversation & Handover

- `Conversation` (`DATA-ENT-020`) là aggregate root.
- `Message` (`DATA-ENT-021`) thuộc conversation và immutable sau khi ghi, ngoại trừ trạng thái redaction được audit.
- `Handover` (`DATA-ENT-022`) là aggregate chuyển tuyến đến staff queue.
- `HandoverAssignment` (`DATA-ENT-023`) ghi ownership hiện tại và lịch sử phân công.

Invariant:

- Message sequence MUST tăng liên tục trong một conversation và unique `(conversation_id, sequence_no)`.
- Handover payload chỉ chứa minimum necessary context; citation và opaque IDs được ưu tiên hơn full document/user record.
- Handover `QUEUED` MUST có `queue_key`; `ASSIGNED` trở đi MUST có active assignee.

### 3.4 Knowledge & Evidence

- `KnowledgeSource` (`DATA-ENT-030`) là nguồn logic có owner và authority.
- `DocumentVersion` (`DATA-ENT-031`) là file/nội dung immutable theo checksum.
- `KnowledgeChunk` (`DATA-ENT-032`) là đoạn được index, chỉ thuộc một version.
- `Citation` (`DATA-ENT-033`) là value object trỏ đến version/chunk/page/section.
- `RetrievalRun` (`DATA-ENT-034`) ghi query redacted, candidates, ranking metadata và prompt-independent evidence trace.

Invariant:

- Chỉ `DocumentVersion.status=PUBLISHED` và đang trong hiệu lực mới được retrieval production sử dụng.
- `(knowledge_source_id, version_label)` và `content_checksum` MUST unique theo nguồn.
- Khi version mới publish, version cũ chuyển `SUPERSEDED` trong cùng transaction hoặc workflow có compensating action rõ ràng.
- Citation MUST resolve được đến source/version còn lưu; superseded source vẫn giữ để audit nhưng UI phải hiển thị trạng thái.
- Embedding vector MUST không chứa PII hoặc dữ liệu hồ sơ sinh viên.

### 3.5 Confirmed Actions

- `ActionPreview` (`DATA-ENT-040`) là aggregate root bất biến về `actor_id`, `action_type`, `normalized_payload`, `payload_hash`, `policy_decision` và expiry sau khi phát hành.
- `ActionConfirmation` (`DATA-ENT-041`) là bằng chứng actor đã xác nhận đúng preview.
- `ActionExecution` (`DATA-ENT-042`) ghi kết quả thực thi side effect.
- `IdempotencyRecord` (`DATA-ENT-043`) ràng buộc key với actor, operation và request fingerprint.

Invariant:

- Confirmation MUST bind actor, preview ID, payload hash, policy decision version và expiry.
- Preview hết hạn, bị hủy hoặc đã dùng MUST NOT được execute.
- Một preview chỉ có tối đa một successful execution.
- Cùng idempotency key + cùng fingerprint trả lại cùng semantic result; cùng key + khác fingerprint trả `409 IDEMPOTENCY_KEY_REUSED`.
- Policy denial không được client override bằng confirmation.

### 3.6 Operations & Audit

- `AuditEvent` (`DATA-ENT-050`) là append-only security/business audit.
- `OutboxEvent` (`DATA-ENT-051`) là event chờ publish.
- `InboxReceipt` (`DATA-ENT-052`) chống xử lý event trùng ở consumer.
- `NotificationDelivery` (`DATA-ENT-053`) ghi attempt, provider reference và kết quả.

Invariant:

- AuditEvent MUST không chứa secret, raw access token, model API key hoặc unrestricted message content.
- OutboxEvent được tạo trong cùng transaction với aggregate mutation.
- Consumer MUST ghi InboxReceipt atomically với side effect của mình.
- Event retention và audit retention là cấu hình riêng; xóa event transport không được xóa audit record.

## 4. Quan hệ logic

```text
UserIdentity 1---0..1 StudentProfile
UserIdentity 1---* RoleBinding
UserIdentity 1---* Conversation 1---* Message
Conversation 1---0..* Handover 1---* HandoverAssignment
UserIdentity 1---* Ticket 1---* TicketEvent
UserIdentity 1---* DocumentRequest
UserIdentity 1---* RoomBooking *---1 Room
KnowledgeSource 1---* DocumentVersion 1---* KnowledgeChunk
RetrievalRun *---* KnowledgeChunk (through retrieval_candidate)
Message 1---* Citation *---1 DocumentVersion
ActionPreview 1---0..1 ActionConfirmation 1---0..1 ActionExecution
Any mutable aggregate 1---* AuditEvent / OutboxEvent
```

## 5. Transaction boundaries

| ID | Transaction bắt buộc |
|---|---|
| DATA-TXN-001 | Ticket state update + TicketEvent + AuditEvent + OutboxEvent. |
| DATA-TXN-002 | Action confirmation consume + ActionExecution creation + target aggregate mutation + OutboxEvent. |
| DATA-TXN-003 | Room availability check + confirmed booking insert; MUST chống race. |
| DATA-TXN-004 | Publish DocumentVersion + supersede prior version + outbox event. |
| DATA-TXN-005 | Handover assignment + assignment history + event. |

External HTTP call MUST NOT được giữ bên trong database transaction dài. Với external side effect, transaction đầu tiên ghi execution `PENDING` và outbox command; worker thực thi idempotently rồi ghi terminal result.

## 6. Delete và retention semantics

- Hard delete user-owned business records MUST NOT tồn tại trong API V1.
- Privacy deletion request phải pseudonymize identifier có thể xóa trong khi giữ audit tối thiểu theo policy; chi tiết cần `PRIV` contract được phê duyệt.
- Knowledge version đã từng được trích dẫn MUST NOT hard-delete nếu chưa hết audit retention.
- Synthetic dataset MAY được tái tạo, nhưng reset toàn bộ database là destructive operation và không được giao cho coding agent mặc định.

## 7. Acceptance evidence và failure behavior

Evidence tối thiểu:

- ERD triển khai ánh xạ đủ mọi `DATA-ENT-*` được dùng trong V1.
- Migration tests chứng minh unique/FK/check/exclusion constraints.
- Concurrency tests chứng minh không double booking và không double execution.
- Authorization tests chứng minh cross-user reads/writes bị từ chối.
- Fixture tests chứng minh real identity bị từ chối trong demo mode.

Nếu một invariant không thể database-enforce, implementation agent MUST dừng và tạo blocker gồm invariant ID, lý do, race condition có thể xảy ra và đề xuất ADR. Không được thay bằng comment/TODO.
