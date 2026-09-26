---
document_id: "DOC-PRIV-001"
version: "0.1.0"
status: "draft"
owner: "Privacy/Legal Owner"
approvers: ["Data Owner", "Security Architect", "Product Owner"]
last_updated: "2026-09-21"
---

# Data-flow and privacy analysis

## 1. Phạm vi và vai trò xử lý

V1 chỉ dùng dữ liệu tổng hợp. Thiết kế production giả định nhà trường có thể là `Data Controller`, còn đơn vị vận hành sản phẩm có thể là `Data Processor` hoặc `Controller and Processor` tùy hợp đồng và quyền quyết định mục đích/phương tiện. Đây chỉ là giả định thiết kế; `OQ-002` và `OQ-005` MUST được Legal Owner giải quyết trước dữ liệu thật.

Không implementation agent nào được tự chọn lawful basis, viết consent thay legal review hoặc coi acceptance của Terms of Service là consent cho mọi mục đích.

## 2. Data-flow inventory

### `PRIV-FLOW-001` — Authentication and session

```text
User -> Browser/BFF -> Mock IdP (simulation) or Microsoft Entra ID (future)
                    -> internal IdentityContext -> API
```

- Input tối thiểu: external subject ID, issuer, account state, approved role/attributes.
- API MUST NOT nhận password; mock auth MUST NOT mô phỏng bằng password thật.
- ID token/access token MUST không được ghi log.
- Production purpose/legal basis và privacy notice: `UNRESOLVED`, launch blocker.

### `PRIV-FLOW-002` — Grounded public FAQ

```text
Question -> Privacy gateway -> Retrieval (C0 approved corpus)
         -> LLM gateway -> DeepSeek -> validated answer + citations
```

- V1 MUST dùng synthetic question hoặc câu hỏi không chứa PII.
- Retrieval MUST chỉ dùng published, effective, approved sources.
- External LLM payload MUST exclude user identity, session ID, IP, email, ticket ID và raw internal metadata.
- Response MUST qua citation/evidence check và output DLP.

### `PRIV-FLOW-003` — Personal schedule read

```text
IdentityContext -> Schedule tool -> synthetic schedule store -> minimized response
```

- Tool MUST derive subject from trusted context, không từ model/user-supplied `student_id`.
- Full schedule MUST không được gửi tới LLM nếu deterministic formatter đáp ứng use case.
- Cross-user lookup bị cấm cho student role.

### `PRIV-FLOW-004` — Ticket/document request/room booking write

```text
User intent -> normalized draft -> policy check -> action preview
            -> explicit confirmation -> idempotent tool -> operational store
```

- Preview MUST hiển thị mục đích, trường dữ liệu, người nhận/queue và hậu quả.
- Confirmation MUST bind actor + payload hash + action + expiry.
- LLM MAY hỗ trợ trích xuất draft từ synthetic text; LLM MUST NOT xác nhận hoặc phê duyệt thay người dùng.

### `PRIV-FLOW-005` — HITL and staff queue

```text
Risk/policy trigger -> data minimization -> queue assignment -> authorized staff workspace
```

- Chỉ chuyển thông tin cần thiết: intent, concise summary, relevant transcript excerpt, citations, risk reason.
- Sensitive disclosure MUST không xuất hiện trong notification subject/push/email; notification chỉ chứa case ID opaque.
- Staff access MUST theo queue/unit và need-to-know.

### `PRIV-FLOW-006` — External LLM transfer

```text
Application -> PII/secret detector -> minimizer/pseudonymizer -> egress policy
            -> provider adapter -> DeepSeek API
```

- Trong V1, gate MUST chỉ cho `PUBLIC` và approved `INTERNAL` synthetic data.
- C2/C3 MUST bị chặn, kể cả người dùng chủ động nhập.
- Provider request ID MAY được lưu; prompt/response raw MUST không vào general logs.
- Nếu redaction confidence không đạt ngưỡng deterministic policy, request MUST không rời boundary.

### `PRIV-FLOW-007` — Knowledge ingestion

```text
Approved source -> malware/file validation -> OCR/parser -> PII/secret scan
                -> quarantine/review -> chunks -> lexical/vector indexes
```

- Public URL không đồng nghĩa nội dung đã được phép redistribute.
- Ingestion MUST preserve provenance, checksum, effective dates và reviewer.
- Hidden text/instructions MUST được đánh dấu untrusted; system prompt MUST không làm theo document instructions.

### `PRIV-FLOW-008` — Telemetry and audit

```text
Services -> structured redaction -> metrics/log/audit pipelines -> restricted viewers
```

- Metrics MUST dùng aggregate hoặc pseudonymous identifiers.
- Security audit và conversation content MUST tách storage/access policy.
- Trace exporter MUST có field allowlist; arbitrary baggage/header forwarding bị cấm.

### `PRIV-FLOW-009` — Data-subject request and deletion

```text
Verified requester -> privacy case -> locate/export/correct/delete workflows
                   -> processor/vendor coordination -> signed completion record
```

- Request MUST được identity-verified tương xứng, không thu thập quá mức.
- Legal hold/mandatory retention MAY ngăn xóa; lý do và phạm vi MUST được Privacy Owner phê duyệt.
- Không được tuyên bố xóa hoàn tất nếu backup/vendor copy chưa theo policy.

## 3. Processing inventory schema

Mỗi production flow MUST có record:

```yaml
processing_activity:
  id: "PRIV-FLOW-..."
  purpose: "approved purpose"
  controller: "named legal entity"
  processor: ["named legal entities"]
  data_subjects: ["student", "staff"]
  data_categories: ["explicit categories"]
  sensitive_data: false
  lawful_basis: "legal-owner-approved value"
  notice_version: "version"
  recipients: ["explicit recipient"]
  storage_locations: ["country/region/service"]
  cross_border: false
  retention_rule_id: "PRIV-RET-..."
  security_controls: ["SEC-CTRL-..."]
  owner: "role"
  approved: false
```

Missing `purpose`, `lawful_basis`, `storage_locations`, `retention_rule_id` hoặc owner MUST block real-data processing.

## 4. Privacy requirements

| ID | Requirement | Acceptance evidence | Failure behavior |
|---|---|---|---|
| `PRIV-FLOW-010` | UI MUST disclose AI use, data categories, purpose, recipients, retention và rights bằng privacy notice đã version. | UX test + notice version in consent/audit record. | Feature unavailable until notice configured. |
| `PRIV-FLOW-011` | Consent, khi được dùng, MUST là affirmative, granular, withdrawable và không pre-checked; controller MUST lưu bằng chứng kiểm chứng được. | Negative UI test + consent event schema. | Treat as no consent. |
| `PRIV-FLOW-012` | Service MUST collect minimum fields declared in active contract; unknown/additional properties MUST bị reject. | JSON Schema `additionalProperties: false` tests. | `422 VALIDATION_ERROR`. |
| `PRIV-FLOW-013` | Personal read/write MUST not require LLM where deterministic code can complete the operation. | Architecture review and provider-call assertion. | Skip LLM; execute deterministic path. |
| `PRIV-FLOW-014` | Analytics MUST không dùng raw identity/content; re-identification hoặc behavioral scoring là new processing purpose cần DPIA amendment. | Telemetry field inventory. | Analytics export blocked. |
| `PRIV-FLOW-015` | Data from one user MUST không xuất hiện trong prompt, memory, retrieval hoặc response của user khác. | Canary cross-session isolation test. | Stop affected service; open SEV-0/SEV-1 incident. |
| `PRIV-FLOW-016` | User-provided C2/C3 detected in an LLM-bound prompt MUST be blocked/redacted locally and MUST not be echoed in error text. | Seeded DLP tests. | Safe explanation + ticket/HITL option. |
| `PRIV-FLOW-017` | Every external transfer MUST map to `PRIV-XFER-*` approval and vendor version. | Runtime egress policy references approved record. | Network call denied. |
| `PRIV-FLOW-018` | New field, recipient, model provider or storage region MUST trigger processing-inventory and DPIA review before release. | Schema diff check in CI. | Security/privacy gate fails. |

## 5. Legal mapping và giới hạn

[Luật 91/2025/QH15](https://vbpl.vn/TW/Pages/ivbpq-toanvan.aspx?ItemID=179252&Keyword=) và [Nghị định 356/2025/NĐ-CP](https://vbpl.vn/bocongan/Pages/vbpq-toanvan.aspx?ItemID=187276) là nguồn pháp lý chính cho processing inventory, quyền của chủ thể, consent, impact assessment và transfer. Nghị định yêu cầu consent có khả năng kiểm chứng, không dùng default consent gây hiểu lầm, và quy định các mốc xử lý một số yêu cầu quyền. Tài liệu này không thay legal opinion; Legal Owner MUST đối chiếu văn bản có hiệu lực tại thời điểm launch.

## 6. Traceability

- Decisions: `DEC-004`, `DEC-007`, `DEC-008`, `DEC-010`, `DEC-014`, `DEC-015`.
- Open questions: `OQ-002`, `OQ-005`, `OQ-006`, `OQ-007`.
- Related: `SEC-DATA-*`, `PRIV-DPIA-*`, `PRIV-RET-*`, `PRIV-XFER-*`.
- Threats: `THR-I-001`, `THR-LINK-001`, `THR-LLM-001`, `THR-LLM-002`, `THR-LLM-008`.

Nguồn được truy cập ngày `2026-09-21`.
