---
document_id: "DOC-PRIV-003"
version: "0.1.0"
status: "draft"
owner: "Records and Privacy Owner"
approvers: ["Data Owner", "Security Architect", "Operations Owner"]
last_updated: "2026-09-21"
---

# Retention, deletion and data-subject rights

## 1. Policy status

`OQ-006` chưa được giải quyết. Các thời hạn dưới đây chỉ là **simulation defaults**, không phải lịch lưu trữ production hoặc kết luận pháp lý. Real-data launch MUST bị chặn cho tới khi Records/Privacy Owner phê duyệt purpose-specific schedule.

## 2. Simulation retention schedule

| ID | Data set | Simulation default | Trigger | Disposition |
|---|---|---:|---|---|
| `PRIV-RET-001` | Anonymous public FAQ request metadata | 30 days | Request completion | Delete or aggregate irreversibly |
| `PRIV-RET-002` | Synthetic conversation/messages | 90 days (`ASM-007`) | Message creation | Delete content; retain non-identifying aggregate |
| `PRIV-RET-003` | Synthetic ticket/document request/booking | 365 days after closure | Terminal state | Delete/anonymize according to relation constraints |
| `PRIV-RET-004` | Action preview | 24 hours | Preview creation | Delete payload and invalidate |
| `PRIV-RET-005` | Confirmation token | 10 minutes validity; metadata 90 days | Issue/use/expiry | Destroy token; retain hashed evidence metadata |
| `PRIV-RET-006` | Session | 12 hours max/idle policy configurable | Login/last activity | Revoke and delete server session |
| `PRIV-RET-007` | Retrieval/model/tool trace metadata | 90 days | Invocation | Delete; raw prompt/response not in generic trace |
| `PRIV-RET-008` | Security/audit events | 400 days simulation | Event time | Expire only through controlled lifecycle policy |
| `PRIV-RET-009` | Knowledge source/version | While authoritative + superseded audit period | Publish/retire | Preserve approved provenance; content rights govern |
| `PRIV-RET-010` | Quarantined failed upload | 7 days | Quarantine | Delete unless incident hold |
| `PRIV-RET-011` | Backup | 35 days rolling simulation | Backup creation | Cryptographic/lifecycle expiry; tested restore |
| `PRIV-RET-012` | Incident evidence | Case-specific; default unset | Case opening | Legal/Security Owner closes hold and sets disposition |

Production MUST NOT copy these values without legal, records, service and contractual review.

## 3. Data-subject request workflow

```text
Receive -> verify identity and scope -> acknowledge -> search systems/vendors
        -> legal hold/exception review -> approve action -> execute
        -> verify completion -> respond -> retain minimal case evidence
```

Theo [Nghị định 356/2025/NĐ-CP](https://vbpl.vn/TW/Pages/vbpq-toanvan.aspx?ItemID=187276), yêu cầu xóa đúng thủ tục phải được phản hồi về thủ tục trong 02 ngày làm việc và thực hiện trong 20 ngày; khi cần bên xử lý/bên thứ ba phối hợp, thời hạn được nêu là 30 ngày; việc gia hạn có giới hạn và phải giải thích. Đây là mốc pháp lý cần Legal Owner xác minh cho case thực tế tại thời điểm launch. Internal tracking MUST đặt due date sớm hơn statutory deadline để có thời gian review.

## 4. Deletion semantics

- `soft delete` không được coi là hoàn tất nếu record vẫn phục hồi/đọc được ngoài approved recovery window.
- Referential integrity MUST không làm lộ dữ liệu; thay direct identifier bằng tombstone chỉ khi retention/legal purpose cho phép.
- Deletion job MUST xử lý primary DB, search index, vector index, Redis/cache, object storage, queue/DLQ, analytics, model trace và processors/vendors.
- Backup MAY chờ lifecycle expiry nếu production legal policy cho phép; hệ thống MUST bảo đảm deleted data không được tái kích hoạt sau restore. Restore runbook MUST rerun deletion tombstones before service reopen.
- Audit record MAY giữ bằng chứng tối thiểu rằng yêu cầu đã được xử lý, nhưng MUST không giữ raw deleted content hoặc tạo đường vòng phục hồi.
- Legal hold MUST có case ID, authority, scope, owner, start, review date và release approval.

## 5. Normative requirements

| ID | Requirement | Acceptance evidence | Failure behavior |
|---|---|---|---|
| `PRIV-RET-013` | Mỗi persisted object MUST map tới một `PRIV-RET-*` rule; unknown retention is prohibited. | Automated data inventory coverage 100%. | Treat as launch blocker; no production writes. |
| `PRIV-RET-014` | Retention MUST start from explicit lifecycle event, not ambiguous “last seen” unless documented. | Schema/job tests with boundary times. | Do not delete; raise control failure for review. |
| `PRIV-RET-015` | Deletion MUST be idempotent, resumable and emit per-store evidence without raw data. | Partial-failure/retry integration tests. | Case remains `PARTIAL`; never mark complete. |
| `PRIV-RET-016` | User request identity verification MUST be proportionate and MUST not ask for full identity-document images by default. | UX/API test and approved verification method. | Request paused securely; no disclosure/deletion. |
| `PRIV-RET-017` | Export MUST use machine-readable approved format, field minimization and short-lived single-use delivery. | Export contract, authorization and expiry tests. | Export denied/expired. |
| `PRIV-RET-018` | Correction MUST preserve audit of who/when/which field without retaining unnecessary previous sensitive value. | Update/audit tests. | Transaction rollback. |
| `PRIV-RET-019` | Legal hold MUST override automated deletion only for explicit scope and expire/review; broad indefinite hold is prohibited. | Hold policy tests and quarterly review report. | Deletion case reports `HELD` with approved reason. |
| `PRIV-RET-020` | Vendor deletion MUST be tracked; no case is `COMPLETED` before processor confirmation or approved documented limitation. | Vendor receipt/API evidence. | Status `PENDING_PROCESSOR`. |
| `PRIV-RET-021` | Retention job MUST run at least daily in production and alert on backlog/failure. | Scheduler/alert test and lag dashboard. | New data writes MAY be disabled if sustained failure exceeds approved threshold. |
| `PRIV-RET-022` | Changing retention to a longer period is a privacy/security change requiring approval and DPIA review. | Change record linked to `PRIV-DPIA-018`. | Release blocked. |
| `PRIV-RET-023` | Production MUST publish a notice consistent with actual retention, not simulation defaults. | Notice-to-config automated comparison. | Launch blocked. |

## 6. Deletion evidence schema

```yaml
deletion_case:
  case_id: "opaque-id"
  request_type: "access|correction|deletion|restriction|objection"
  requester_verified: true
  received_at: "RFC3339"
  acknowledged_at: "RFC3339"
  due_at: "RFC3339"
  applicable_rules: ["PRIV-RET-..."]
  legal_holds: []
  stores:
    - name: "logical-store-name"
      status: "completed|not_found|held|failed|pending_processor"
      completed_at: "RFC3339|null"
      evidence_hash: "sha256:..."
  final_status: "completed|partial|denied_with_legal_reason"
  approved_by: ["Privacy Owner"]
```

## 7. Traceability

- Assumption: `ASM-007`.
- Open question: `OQ-006`.
- Flows: `PRIV-FLOW-009`, `PRIV-FLOW-017`.
- DPIA: `PRIV-DPIA-005`, `PRIV-DPIA-017`.
- Controls: `SEC-CTRL-015`.

Nguồn được truy cập ngày `2026-09-21`.
