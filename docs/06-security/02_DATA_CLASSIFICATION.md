---
document_id: "DOC-SEC-002"
version: "0.1.0"
status: "draft"
owner: "Privacy/Legal Owner"
approvers: ["Security Architect", "Data Owner", "Product Owner"]
last_updated: "2026-09-21"
---

# Data classification and handling standard

## 1. Quy tắc phân loại

Mỗi dataset, table/column, object prefix, event field và exported artifact MUST có một classification. Nếu chưa xác định được, hệ thống MUST dùng mức cao hơn hợp lý. `synthetic=true` không tự động biến dữ liệu thành `PUBLIC`.

| Level | Nhãn máy đọc | Định nghĩa | Ví dụ V1 |
|---|---|---|---|
| C0 | `PUBLIC` | Được chủ sở hữu phê duyệt công khai; không chứa secret/PII | Quy định công khai đã duyệt, FAQ công khai, status page |
| C1 | `INTERNAL` | Không công khai; lộ lọt gây ảnh hưởng thấp-vừa | Source code private, system architecture, synthetic dataset, prompt template không chứa secret |
| C2 | `CONFIDENTIAL` | Dữ liệu cá nhân cơ bản, dữ liệu nghiệp vụ hoặc bảo mật có ảnh hưởng đáng kể | Tài khoản, lịch học gắn cá nhân, ticket, transcript, IP/device metadata, staff queue |
| C3 | `RESTRICTED` | Dữ liệu cá nhân nhạy cảm, credential, cryptographic material, incident evidence hoặc dữ liệu có thể gây thiệt hại nghiêm trọng | Health/self-harm disclosure, disciplinary complaint, access/refresh token, API key, KMS key material, unredacted forensic capture |

Danh mục dữ liệu cá nhân cơ bản và nhạy cảm MUST được đối chiếu với Điều 3–4 của [Nghị định 356/2025/NĐ-CP](https://vbpl.vn/bocongan/Pages/vbpq-toanvan.aspx?ItemID=187276). Classification nội bộ có thể nghiêm hơn pháp luật; agent MUST NOT hạ mức chỉ vì một trường dữ liệu không xuất hiện nguyên văn trong danh mục pháp lý.

## 2. Classification catalog

| Data object | Class | PII | Synthetic V1 | Cho phép gửi LLM ngoài hệ thống |
|---|---:|---:|---:|---:|
| Approved public knowledge chunks | C0 | No | Có thể | Có, sau injection scanning và allowlist |
| Draft/unpublished policy | C1 | No mặc định | Có thể | Không mặc định |
| Synthetic student profile/schedule | C1 | No, nếu chứng minh tổng hợp | Bắt buộc | Chỉ minimized fixture trong automated test, fake provider ưu tiên |
| Real student identity/profile | C2 | Yes | Cấm V1 | Không được phép |
| Ticket/document request | C2; C3 nếu chứa sensitive disclosure | Có thể | Chỉ synthetic | Không được phép khi có PII; redacted abstract chỉ sau approval |
| Conversation transcript | C2; nâng C3 khi nhạy cảm | Có thể | Chỉ synthetic | Chỉ redacted/minimized; production bị chặn |
| Citation metadata/public source URL | C0/C1 | No | Có thể | Có |
| Prompt/system policy | C1 | No | N/A | Chỉ phần cần thiết; không coi là secret control |
| Audit event metadata | C2 | Pseudonymous | Synthetic actor trong V1 | Không |
| Raw HTTP headers/cookies/tokens | C3 | Có thể | Không lưu | Không |
| DeepSeek API key, DB password, signing key | C3 | No | Secret giả cục bộ | Không bao giờ |
| Security incident evidence | C3 | Có thể | Synthetic drill | Không nếu chưa legal approval |
| Aggregated metrics đạt k-anonymity policy | C1 hoặc C0 sau duyệt | No | Có thể | Có theo purpose |

## 3. Handling matrix

| Control | C0 | C1 | C2 | C3 |
|---|---|---|---|---|
| Storage | Approved public store | Authenticated store | Encrypted private store | Encrypted restricted store/field protection |
| Transit | HTTPS | TLS | TLS 1.2+; private path ưu tiên | TLS 1.2+; explicit destination allowlist |
| Access | Public read/controlled write | Workforce/service need | Least privilege + object scope | Named privileged role + MFA/step-up + audit |
| Logging | Có thể log metadata | Metadata only | Pseudonymous metadata; no raw payload mặc định | No payload; security case store riêng |
| Export | Public approval | Owner approval | Owner + privacy approval | Security + privacy/legal approval |
| LLM | Approved | Minimize | Block unless approved redaction flow | MUST NOT send external LLM |
| Backup | Theo availability | Encrypted | Encrypted + access audit | Encrypted + separate key/access review |
| Deletion | Source lifecycle | Owner schedule | `PRIV-RET-*` | `PRIV-RET-*` + evidence/legal hold check |

## 4. Normative requirements

| ID | Requirement | Acceptance evidence | Failure behavior |
|---|---|---|---|
| `SEC-DATA-001` | Schema/IaC MUST attach classification metadata to every persistent dataset and object prefix. | Automated inventory report có 100% coverage. | Unknown item treated C3; launch report fails. |
| `SEC-DATA-002` | API response MUST use explicit allowlist schema; ORM/entity object MUST NOT được serialize trực tiếp. | Contract test chèn hidden/admin fields nhưng response không lộ. | Serialization fails closed. |
| `SEC-DATA-003` | C2/C3 MUST không xuất hiện trong URL query, analytics tags, client error telemetry hoặc notification subject. | DLP test trên access logs và telemetry fixture. | Request rejected/redacted; security alert. |
| `SEC-DATA-004` | C3 MUST không nằm trong Redis cache trừ khi use case được duyệt, TTL hữu hạn và encryption/access control có test. | Cache key inventory và TTL test. | Skip cache. |
| `SEC-DATA-005` | C2/C3 export MUST tạo immutable audit event và dùng single-use, short-lived download authorization. | Export integration tests và audit evidence. | Export denied. |
| `SEC-DATA-006` | Knowledge ingestion MUST reject PII/secrets before chunking/embedding; quarantine MUST tách khỏi searchable index. | Seeded PII/secret corpus đạt 100% reject đối với deterministic patterns bắt buộc. | Quarantine entire document; no partial publish. |
| `PRIV-DATA-001` | V1 simulation MUST sử dụng `synthetic=true`, generator seed, provenance và assertion không ánh xạ tới cá nhân thật. | Dataset manifest + reproducibility test + manual sample review. | Dataset blocked from environment. |
| `PRIV-DATA-002` | Agent MUST NOT scrape, copy hoặc synthesize từ hồ sơ cá nhân công khai để tạo “realistic” identities. | Provenance review; source allowlist. | Stop ingestion task. |
| `PRIV-DATA-003` | Direct identifiers MUST không xuất hiện trong embeddings; production personal memory design cần DPIA amendment riêng. | Vector metadata/schema scan. | Ingestion denied. |
| `PRIV-DATA-004` | Reclassification xuống mức thấp hơn MUST có Data Owner và Privacy Owner approval cùng evidence. | Approved change record. | Keep higher class. |

## 5. Synthetic data manifest

Mọi dataset mô phỏng MUST có manifest:

```yaml
dataset_id: "SYN-..."
synthetic: true
generator_version: "git-sha-or-version"
seed: "non-secret-reproducible-seed"
contains_real_personal_data: false
source_taxonomy_refs: ["public-source-id"]
classification: "INTERNAL"
allowed_environments: ["local", "development", "staging", "demo"]
prohibited_uses: ["identity_proofing", "production_decision", "model_training_without_review"]
reviewed_by: ["Data Owner", "Privacy Owner"]
```

Tên, email, mã sinh viên và lịch MUST được tạo từ danh sách/thuật toán giả, không lấy từ directory, social network hoặc website thật. Domain email SHOULD dùng `.example` hoặc domain được dành riêng cho test; số điện thoại MUST dùng pattern không định tuyến.

## 6. Traceability

- Decisions: `DEC-004`, `DEC-010`, `DEC-013`.
- Open questions: `OQ-002`, `OQ-005`, `OQ-006`.
- Privacy flows: `PRIV-FLOW-001` đến `PRIV-FLOW-009`.
- Threats: `THR-I-001`, `THR-I-002`, `THR-LLM-002`, `THR-LLM-008`.

## 7. Nguồn chính

- [Luật Bảo vệ dữ liệu cá nhân 91/2025/QH15](https://vbpl.vn/TW/Pages/ivbpq-toanvan.aspx?ItemID=179252&Keyword=).
- [Nghị định 356/2025/NĐ-CP](https://vbpl.vn/bocongan/Pages/vbpq-toanvan.aspx?ItemID=187276).
- [AWS KMS encryption guidance](https://docs.aws.amazon.com/prescriptive-guidance/latest/aws-kms-best-practices/data-protection-encryption.html).

Nguồn được truy cập ngày `2026-09-21`.
