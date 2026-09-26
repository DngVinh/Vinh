---
document_id: "DOC-PRIV-002"
version: "0.1.0"
status: "draft"
owner: "Privacy/Legal Owner"
approvers: ["Data Owner", "Security Architect", "University Sponsor"]
last_updated: "2026-09-21"
---

# Preliminary Data Protection Impact Assessment

## 1. Kết luận sơ bộ

Campus 24/7 có mức rủi ro quyền riêng tư tiềm tàng cao khi chuyển sang dữ liệu thật vì kết hợp hồ sơ sinh viên, hội thoại tự do, lịch học, ticket, nội dung nhạy cảm, AI và nhà cung cấp xuyên biên giới. Simulation hiện tại giảm rủi ro bằng cách cấm tuyệt đối PII thật, nhưng không thay thế DPIA production.

**Quyết định hiện tại:**

- Simulation với synthetic data: `CONDITIONALLY_ACCEPTABLE` nếu mọi control trong `PRIV-DPIA-001` đến `PRIV-DPIA-010` được kiểm chứng.
- Pilot với real users hoặc real personal data: `NOT_APPROVED`.
- Gửi PII hoặc sensitive data tới DeepSeek/AWS Singapore: `PROHIBITED_PENDING_LEGAL_AND_VENDOR_APPROVAL`.

## 2. Mục đích, sự cần thiết và tính tương xứng

| Processing purpose | Cần thiết | Phương án ít xâm phạm hơn | Quyết định sơ bộ |
|---|---|---|---|
| Trả lời FAQ có citation | Có | Search deterministic trước; LLM chỉ tổng hợp nguồn công khai | Cho phép với C0 corpus |
| Xem lịch cá nhân | Có | Tool deterministic; không gửi lịch cho LLM | Cho phép sau authz test |
| Tạo ticket/document request | Có | Form deterministic + optional AI drafting | Cho phép với preview/confirmation |
| Đặt phòng | Có | Tool deterministic kiểm tra xung đột | Cho phép sau policy/idempotency |
| HITL | Có cho ngoại lệ/nhạy cảm | Chuyển summary tối thiểu thay toàn transcript | Cho phép có queue scope |
| Conversation memory dài hạn | Chưa chứng minh | Session memory ngắn hạn | Không cho V1 production |
| Profiling/chấm điểm sinh viên | Không thuộc mục tiêu | Không thực hiện | Cấm |
| Model training từ conversation | Không cần để cung cấp dịch vụ | Synthetic eval dataset | Cấm nếu chưa có mục đích/DPIA riêng |

## 3. Phương pháp đánh giá

- Likelihood `1..5`: hiếm → gần như chắc chắn.
- Impact `1..5`: không đáng kể → nghiêm trọng tới quyền, an toàn, học tập hoặc pháp lý.
- Inherent score = `Likelihood × Impact`.
- `1–4 Low`, `5–9 Medium`, `10–16 High`, `17–25 Critical`.
- Residual risk chỉ được hạ khi control có evidence, không hạ dựa trên kế hoạch chưa triển khai.

## 4. Risk register sơ bộ

| ID | Rủi ro | Inherent | Biện pháp bắt buộc | Residual target | Owner |
|---|---|---:|---|---:|---|
| `PRIV-DPIA-001` | PII thật lọt vào synthetic dataset/log | 4×5=20 Critical | generator provenance, DLP scan, no-prod-copy policy, manual sampling | ≤4 | Data Owner |
| `PRIV-DPIA-002` | Cross-user disclosure qua BOLA/RAG/memory | 4×5=20 | object authz, RLS defense-in-depth, isolated indexes, canary tests | ≤5 | Security Architect |
| `PRIV-DPIA-003` | Prompt chứa PII được gửi DeepSeek ngoài Việt Nam | 4×5=20 | local blocker, C2/C3 deny, egress allowlist, vendor gate | ≤4 trong simulation | Privacy Owner |
| `PRIV-DPIA-004` | Staff xem ticket ngoài phạm vi nhiệm vụ | 3×4=12 | queue/unit ABAC, break-glass workflow, audit review | ≤6 | Operations Owner |
| `PRIV-DPIA-005` | Retention vô thời hạn hoặc deletion không hoàn tất | 4×4=16 | retention jobs, legal hold, vendor/backup tracking, deletion evidence | ≤6 | Records Owner |
| `PRIV-DPIA-006` | AI misinformation ảnh hưởng quyền lợi học tập | 4×4=16 | approved corpus, citations, abstention, HITL, no autonomous approval | ≤6 | Product/Knowledge Owner |
| `PRIV-DPIA-007` | Sensitive/emergency disclosure bị đưa vào email/log | 3×5=15 | notification minimization, payload redaction, restricted case store | ≤5 | Security Owner |
| `PRIV-DPIA-008` | Consent không hợp lệ/dark pattern | 3×4=12 | granular opt-in, no pre-check, versioned evidence, withdrawal | ≤4 | Privacy Owner |
| `PRIV-DPIA-009` | Provider thay policy/subprocessor/location âm thầm | 3×5=15 | contractual notice, periodic reassessment, kill switch, data minimization | ≤5 | Vendor Owner |
| `PRIV-DPIA-010` | Re-identification từ analytics/embeddings | 3×4=12 | aggregation threshold, no personal embeddings, export review | ≤4 | Data Owner |
| `PRIV-DPIA-011` | Incident response thu thập forensic data quá mức | 3×4=12 | scoped capture, C3 evidence vault, access expiry, legal hold | ≤6 | Incident Commander |
| `PRIV-DPIA-012` | Mock auth bị bật ngoài non-production | 3×5=15 | environment hard gate, synthetic-only assertion, production test | ≤3 | Identity Owner |

## 5. Nghĩa vụ và evidence cần hoàn tất

| ID | Requirement | Required evidence | Failure behavior |
|---|---|---|---|
| `PRIV-DPIA-013` | Data Owner MUST lập processing inventory đầy đủ theo `PRIV-FLOW-*` trước khi real-data test. | Signed inventory export. | Real-data gate blocked. |
| `PRIV-DPIA-014` | Privacy Owner MUST xác nhận lawful basis, notice, consent/exception và controller/processor roles cho từng purpose. | Legal memorandum/change record. | Feature disabled. |
| `PRIV-DPIA-015` | Cross-border DPIA/filing và contract MUST hoàn tất trước transfer thật, không đợi sau first transfer như một implementation strategy. | Approved assessment, filing plan/receipt khi áp dụng. | Egress deny. |
| `PRIV-DPIA-016` | Sensitive/emergency processing MUST có approved operating model, contacts, wording và staffed hours. | Approved service runbook. | Chỉ hiển thị safe placeholder; no real launch. |
| `PRIV-DPIA-017` | Rights workflow MUST kiểm chứng access, correction, deletion, restriction/objection và vendor coordination. | End-to-end rights-request test pack. | Production gate blocked. |
| `PRIV-DPIA-018` | Mỗi thay đổi purpose, field, recipient, provider, region, retention hoặc automated decision MUST trigger DPIA review. | CI change declaration + reviewer approval. | Release gate fails. |
| `PRIV-DPIA-019` | Residual High/Critical risk MUST có written risk treatment; chỉ University Sponsor + Privacy + Security Owner mới được accept, nếu pháp luật cho phép. | Signed risk acceptance with expiry. | No launch. |
| `PRIV-DPIA-020` | DPIA MUST được rà soát ít nhất hằng năm và sau material change/incident. | Review record and updated version. | New release blocked after expiry. |

## 6. Quyền và nhóm có nguy cơ cao

- Sinh viên có thể có vị thế phụ thuộc vào nhà trường; consent không được coi là tự nguyện cho chức năng không cần thiết nếu từ chối dẫn tới bất lợi không tương xứng.
- Hội thoại tự do có thể chứa health, self-harm, harassment, disciplinary hoặc family information; classifier không làm giảm classification của raw content.
- Người dùng dưới 18 tuổi có thể tồn tại trong phạm vi trường đại học; age-related policy và representative/guardian rules là `OPEN`, phải legal review.
- Hệ thống MUST không đưa ra quyết định cuối về điểm, kỷ luật, tài chính, sức khỏe, an toàn hoặc quyền học tập.

## 7. Legal baseline

[Luật Bảo vệ dữ liệu cá nhân 91/2025/QH15](https://vanban.chinhphu.vn/?classid=1&docid=214590&pageid=27160&typegroup=) có hiệu lực từ 01/01/2026. Luật quy định đánh giá tác động xử lý và chuyển dữ liệu cá nhân xuyên biên giới; Điều 20 mô tả các trường hợp transfer và việc gửi hồ sơ trong thời hạn luật định. [Nghị định 356/2025/NĐ-CP](https://vbpl.vn/bocongan/Pages/vbpq-toanvan.aspx?ItemID=187276) quy định chi tiết về consent, rights handling, nhân sự/bộ phận bảo vệ dữ liệu và hồ sơ liên quan. Legal Owner MUST kiểm tra bản có hiệu lực và ngoại lệ áp dụng tại thời điểm triển khai; tài liệu này không phải hồ sơ pháp lý đã nộp.

## 8. Traceability

- Decisions: `DEC-003`, `DEC-004`, `DEC-008`, `DEC-010`, `DEC-016`.
- Open questions: `OQ-001` đến `OQ-008`.
- Flows: `PRIV-FLOW-001` đến `PRIV-FLOW-018`.
- Launch blockers: `PRIV-LAUNCH-001` đến `PRIV-LAUNCH-010`.

Nguồn được truy cập ngày `2026-09-21`.
