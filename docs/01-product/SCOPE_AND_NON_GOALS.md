---
document_id: "DOC-PROD-003"
version: "1.0.0"
status: "reviewed"
owner: "Product Manager"
approvers: ["Product Owner", "Architecture Lead", "Security/Privacy Lead"]
last_updated: "2026-09-21"
---

# Scope and non-goals

## 1. Scope rule

Một capability chỉ thuộc V1 nếu được liệt kê `IN` bên dưới và có requirement `P0` hoặc `P1` trong `requirements.yaml`. “Có thể mở rộng sau” MUST NOT được hiểu là được phép thêm vào V1.

## 2. V1 in-scope

| Capability | Mức V1 | Boundary |
|---|---|---|
| Grounded FAQ/RAG | Production-grade simulated | Citation tới nguồn đã duyệt; abstain khi thiếu evidence |
| Conversation | Production-grade simulated | Vietnamese, multi-turn bounded context, feedback |
| Personal schedule | Mock integration | Chỉ dữ liệu của actor; adapter sẵn sàng thay nguồn |
| Ticket | Mock integration | Create, track, timeline, staff handling; write có confirmation |
| Document request | Trên ticket workflow | Loại giấy tờ cấu hình; không ký/cấp giấy thật |
| Room booking | Mock integration | Search, conflict, preview, confirm, cancel theo policy |
| HITL/handover | Internal simulated queue | Queue, reason, minimal context, business-hours status |
| Sensitive/emergency routing | Guardrail + simulated handover | Không chẩn đoán, không gọi hộ, không invent contact |
| Staff workspace | V1 web | Queue, assignment, timeline, response, status transition |
| Knowledge administration | V1 web | Ingest, metadata validation, review, publish/version/retire |
| Operations metrics | V1 web | KPI, cost estimate, latency, quality, queue health |
| Privacy baseline | V1 web/API | Notice, consent record where applicable, export/delete request intake |
| Simulated authentication | V1 | Role-specific demo accounts through internal identity contract |
| Microsoft Entra readiness | Boundary only | Không tích hợp Entra trong V1; contract phải thay adapter được |
| AWS production design | Documentation/IaC roadmap | Simulated implementation có thể chạy local; production topology do ADR duyệt |
| Synthetic data tooling | V1 support capability | Deterministic seed, provenance, scale profiles, no real records |

## 3. Future scope, không thuộc V1

- Microsoft Entra ID integration thật và group/claim mapping thật.
- SIS, LMS, ticketing, room booking, email/SMS integration thật.
- English localization.
- Native iOS/Android application.
- Advanced analytics, forecasting và proactive notifications.
- Omnichannel (Zalo, Teams, email ingestion, voice).
- Workflow builder cho nghiệp vụ mới.
- E-signature và cấp tài liệu điện tử thật.
- Các capability cho giảng viên, cố vấn học tập hoặc khách.
- Multi-campus trong cùng tổ chức sau khi có nhu cầu xác thực.

Future scope MUST có change request, requirement và security/privacy review riêng trước khi task được tạo.

## 4. Explicit non-goals

V1 MUST NOT:

- triển khai SaaS, multi-tenancy, tenant isolation, tenant billing hoặc marketplace;
- sử dụng hồ sơ sinh viên thật, credential thật hoặc contact khẩn cấp chưa được phê duyệt;
- đại diện rằng HUCE tài trợ, phê duyệt hoặc vận hành `HUCE Demo`;
- đưa ra chẩn đoán y tế/tâm lý, tư vấn pháp lý cá nhân hoặc quyết định kỷ luật;
- thay đổi điểm, trạng thái học vụ, học phí, khoản thu hoặc quyền lợi sinh viên;
- tự phê duyệt hồ sơ, ngoại lệ, khiếu nại hoặc room booking cần cán bộ duyệt;
- tự liên hệ cơ quan cứu hộ, công an, bệnh viện hoặc người thân;
- cấp giấy xác nhận chính thức hoặc ký điện tử;
- truy cập trực tiếp database nguồn;
- cho LLM chạy SQL, sở hữu credential nghiệp vụ hoặc thực thi side effect;
- hứa rằng cán bộ trực 24/7;
- dùng dữ liệu mạng xã hội hoặc nội dung không được duyệt làm bằng chứng chính sách;
- tối ưu để thay thế cán bộ hoặc loại bỏ human review trong ca tác động cao.

## 5. Data scope

### 5.1 Được phép

- Nội dung công khai chính thức được dùng để nghiên cứu taxonomy/provenance theo điều khoản nguồn.
- Corpus synthetic có seed, version, generator manifest và nhãn `synthetic`.
- Identity, lịch, ticket, booking, chat và audit synthetic.
- Gold eval data do dự án tạo, có expected answer/evidence.

### 5.2 Không được phép

- Copy hàng loạt hoặc tái phân phối tài liệu công khai khi chưa có quyền.
- Scrape nguồn cần đăng nhập hoặc vượt robots/terms.
- Dùng tên, mã sinh viên, email, số điện thoại hoặc nội dung ticket thật.
- Trộn dữ liệu thật vào environment simulation.

Nếu provenance hoặc quyền sử dụng không xác định, ingestion MUST dừng và tạo blocker.

## 6. Scope-change test

Mọi đề xuất mới phải trả lời tuần tự:

1. Có phục vụ trực tiếp OBJ-001..OBJ-007 không?
2. Có nằm trong bảng V1 in-scope không?
3. Có requirement/acceptance criteria đã approved không?
4. Có owner và downstream contract/test không?
5. Có làm thay đổi dữ liệu, quyền, integration, chi phí hoặc SLO không?

Nếu câu 2 hoặc 3 là “không”, agent MUST dừng và yêu cầu Product Owner phát hành change request. Nếu câu 5 là “có”, MUST có architecture/security/privacy review trước khi triển khai.

