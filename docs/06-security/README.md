---
document_id: "DOC-SEC-000"
version: "1.0.0"
status: "approved"
owner: "Security Architect"
approvers: ["Privacy/Legal Owner", "Product Owner", "Architecture Owner"]
last_updated: "2026-09-22"
---

# Security, privacy, compliance and threat-model package

## 1. Mục đích và hiệu lực

Thư mục này là đặc tả chuẩn cho bảo mật, quyền riêng tư và tuân thủ của Campus 24/7. Toàn bộ gói tài liệu bảo mật, quyền riêng tư và danh mục kiểm soát an ninh đã được Security Architect và các bên phê duyệt chính thức (`status: approved`) cho phạm vi triển khai mô phỏng dữ liệu tổng hợp (synthetic implementation only) ngày 2026-09-22 theo `TASK-DOC-SEC-001`. Tài liệu được viết để một coding agent năng lực hạn chế có thể thực thi từng thay đổi nhỏ mà không tự suy đoán chính sách. Triển khai production và dữ liệu thật tiếp tục bị chặn bởi OQ-001..OQ-008.

## 2. Ranh giới bất biến

- `DEC-001`: V1 chỉ phục vụ một trường; agent MUST NOT bổ sung multi-tenancy hoặc SaaS billing.
- `DEC-002`: mọi bản demo MUST hiển thị `HUCE Demo` và tuyên bố đây là mô phỏng không chính thức.
- `DEC-004`: development, test và demonstration MUST NOT chứa PII thật. Dữ liệu nhận diện được MUST là dữ liệu tổng hợp có thể tái tạo.
- `DEC-007`: mock authentication chỉ là adapter; domain MUST phụ thuộc internal identity contract, không phụ thuộc mock headers/cookies.
- `DEC-014` và `DEC-015`: LLM MUST NOT truy cập database hoặc thực thi side effect trực tiếp; mọi write action MUST có preview, authorization, confirmation và idempotency.
- `DEC-020`: thay đổi authentication, authorization, encryption, security policy, destructive migration, secret thật, paid service hoặc production deployment MUST dừng chờ phê duyệt con người.

## 3. Bản đồ tài liệu

| Tài liệu | Nội dung chính | ID chuẩn |
|---|---|---|
| `01_SECURITY_ARCHITECTURE.md` | Kiến trúc zero-trust, trust boundary, fail-closed | `SEC-ARCH-*` |
| `02_DATA_CLASSIFICATION.md` | Phân loại và quy tắc xử lý dữ liệu | `SEC-DATA-*`, `PRIV-DATA-*` |
| `03_DATA_FLOW_AND_PRIVACY.md` | Data flow, mục đích xử lý, data minimization | `PRIV-FLOW-*` |
| `04_PRELIMINARY_DPIA.md` | DPIA sơ bộ và rủi ro quyền riêng tư | `PRIV-DPIA-*` |
| `05_AUTHORIZATION_MATRIX.md` | RBAC + ABAC, object/function authorization | `SEC-AUTHZ-*` |
| `06_AUTHENTICATION_AND_ENTRA_MIGRATION.md` | Mock auth và lộ trình Microsoft Entra ID | `SEC-AUTHN-*` |
| `07_CRYPTOGRAPHY_AND_SECRETS.md` | Mã hóa, key và secret lifecycle | `SEC-CRYPTO-*` |
| `08_RETENTION_AND_DELETION.md` | Retention, deletion, legal hold | `PRIV-RET-*` |
| `09_AUDIT_AND_MONITORING.md` | Audit schema, detection và log privacy | `SEC-AUDIT-*` |
| `10_THREAT_MODEL.md` | STRIDE và LLM-specific threats | `THR-*` |
| `11_ABUSE_CASES.md` | Abuse cases có expected response và test evidence | `THR-ABUSE-*` |
| `12_SECURITY_CONTROLS.md` | Control catalog và mapping threat → control | `SEC-CTRL-*` |
| `13_SECURE_SDLC_GATES.md` | Security gates trong SDLC | `SEC-SDLC-*` |
| `14_INCIDENT_RESPONSE.md` | Severity, playbook, điều phối sự cố | `SEC-IR-*`, `PRIV-IR-*` |
| `15_VENDOR_AND_CROSS_BORDER.md` | Vendor due diligence và chuyển dữ liệu xuyên biên giới | `PRIV-VEND-*`, `PRIV-XFER-*` |
| `16_LAUNCH_BLOCKERS.md` | Điều kiện bắt buộc trước demo và production | `SEC-LAUNCH-*`, `PRIV-LAUNCH-*` |

## 4. Contract chung cho implementation agent

Mọi task phát sinh từ gói này MUST có đủ:

```yaml
security_task_contract:
  requirement_ids: ["SEC-...", "PRIV-...", "THR-..."]
  allowed_files: ["explicit/path"]
  forbidden_files: ["explicit/path"]
  data_classification: "PUBLIC|INTERNAL|CONFIDENTIAL|RESTRICTED"
  dependencies: ["accepted task IDs"]
  acceptance_evidence:
    - "test command and exit code"
    - "negative authorization/security test"
    - "changed-file list"
    - "redacted output or screenshot when applicable"
  failure_behavior: "fail_closed|block_task"
```

Agent MUST:

1. đọc toàn bộ tài liệu được tham chiếu trước khi sửa;
2. chỉ sửa `allowed_files`;
3. viết negative test trước hoặc cùng implementation;
4. fail closed khi identity, policy, classification hoặc dependency không xác định;
5. không log token, secret, raw prompt chứa PII hoặc full response nhạy cảm;
6. trả về evidence có exit code, không chỉ mô tả “đã chạy”.

Agent MUST dừng khi:

- control yêu cầu một dependency/contract chưa tồn tại hoặc chưa `approved`;
- cần mở rộng quyền, giảm mức mã hóa, nới retention hoặc bỏ audit;
- cần dùng dữ liệu thật, secret thật hoặc gọi dịch vụ trả phí;
- test yêu cầu chứng minh production nhưng chỉ có mock/simulation;
- có xung đột giữa hai nguồn chuẩn.

## 5. Baseline và giới hạn tuyên bố

Pháp luật Việt Nam là bối cảnh bắt buộc. [Luật Bảo vệ dữ liệu cá nhân số 91/2025/QH15](https://vanban.chinhphu.vn/?classid=1&docid=214590&pageid=27160&typegroup=) có hiệu lực từ 01/01/2026; [Nghị định 356/2025/NĐ-CP](https://vbpl.vn/bocongan/Pages/vbpq-toanvan.aspx?ItemID=187276) quy định chi tiết một số nghĩa vụ và thay thế Nghị định 13/2023/NĐ-CP. Legal Owner MUST xác nhận cách áp dụng cho chủ thể, hợp đồng và luồng dữ liệu thực tế trước production.

Các baseline kỹ thuật gồm [NIST CSF 2.0](https://www.nist.gov/cyberframework), [NIST SP 800-61 Rev. 3](https://csrc.nist.gov/pubs/sp/800/61/r3/final), [OWASP ASVS](https://owasp.org/projects/asvs), [OWASP API Security Top 10 2023](https://api-security.owasp.org/editions/2023/en/0x11-t10/), [OWASP Top 10 for LLM Applications 2025](https://genai.owasp.org/resource/owasp-top-10-for-llm-applications-2025/) và [ISO/IEC 27001:2022](https://www.iso.org/standard/27001). Chúng được dùng để thiết kế và kiểm thử; dự án MUST NOT tuyên bố chứng nhận, phù hợp hay tuân thủ một tiêu chuẩn nếu chưa qua đánh giá độc lập có thẩm quyền.

Nguồn được truy cập ngày `2026-09-21`.
