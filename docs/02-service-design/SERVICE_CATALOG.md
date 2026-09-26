---
document_id: "DOC-SVC-002"
version: "0.1.0"
status: "draft"
owner: "Product Owner"
approvers: ["Service Design Lead", "Operations Lead", "Security/Privacy Lead"]
last_updated: "2026-09-21"
---

# Service catalog

## 1. Quy ước contract

Mỗi service entry dưới đây là boundary chuẩn. Agent MUST chỉ triển khai hành vi được liệt kê. Mọi capability mới cần requirement và quyết định được duyệt; agent MUST NOT suy rộng từ tên dịch vụ.

Trạng thái kết thúc chuẩn:

- `completed`: kết quả nghiệp vụ đã được lưu/hiển thị và có evidence.
- `handed_over`: case đã được ghi vào queue hợp lệ, không đồng nghĩa cán bộ đã xử lý.
- `abstained`: AI không trả lời vì thiếu căn cứ hoặc vượt quyền.
- `failed_recoverable`: người dùng có thể retry an toàn hoặc chuyển kênh.
- `blocked`: thiếu cấu hình/quyền/contract bắt buộc.

## 2. Danh mục V1

### SVC-CAT-001 — Grounded policy and procedure answer

- **Actor:** sinh viên đã hoặc chưa bắt đầu phiên chat; câu hỏi không yêu cầu dữ liệu cá nhân có thể được xử lý trước xác thực nếu policy cho phép.
- **Outcome:** người dùng nhận câu trả lời tiếng Việt ngắn gọn, có citation tới nguồn đang hiệu lực, hoặc nhận lời từ chối có lý do và lối thoát.
- **MUST:** hiển thị tên nguồn, số/phiên bản nếu có, mục/trang, ngày hiệu lực và link mở citation; đánh dấu nguồn mô phỏng.
- **MUST NOT:** dùng ký ức hội thoại làm căn cứ chính sách; che giấu thiếu evidence; suy diễn ngoại lệ cá nhân.
- **Failure:** nếu evidence gate không đạt, trả `abstained`, nêu phần chưa xác minh và đưa lựa chọn đặt câu hỏi rõ hơn hoặc tạo ticket.
- **Telemetry:** intent, retrieval/model version, citation IDs, abstention reason, latency; MUST NOT log nội dung nhạy cảm không cần thiết.
- **Acceptance evidence:** test có citation hợp lệ; test nguồn hết hiệu lực bị loại; test không đủ evidence dẫn tới abstain.
- **Traceability:** `DEC-012`, `DEC-013`, `SVC-JRN-001`, `UX-TRUST-001`–`UX-TRUST-006`.

### SVC-CAT-002 — Personal schedule lookup

- **Actor/precondition:** sinh viên đã xác thực; identity context chứa internal subject ID.
- **Outcome:** xem lịch của chính mình theo ngày/tuần với nguồn dữ liệu và thời điểm đồng bộ.
- **MUST:** resolve actor từ auth context; hiển thị timezone `Asia/Bangkok`; phân biệt lịch trống, chưa đồng bộ và lỗi nguồn.
- **MUST NOT:** nhận student ID từ prompt để thay actor; cho phép xem lịch người khác; tạo/sửa lịch trong V1.
- **Failure:** auth thiếu/hết hạn -> yêu cầu đăng nhập lại; adapter unavailable -> giữ dữ liệu cache nếu còn hợp lệ và dán nhãn stale, nếu không thì cung cấp ticket.
- **Acceptance evidence:** authorization tests; empty/stale/error UI states; audit event cho access dữ liệu cá nhân.
- **Traceability:** `DEC-004`, `DEC-007`, `SVC-JRN-002`, `UX-SCR-004`, `UX-STATE-013`.

### SVC-CAT-003 — Support ticket creation and tracking

- **Actor/precondition:** sinh viên đã xác thực; loại yêu cầu nằm trong catalog.
- **Outcome:** ticket có ID, queue, priority, trạng thái và dấu thời gian; sinh viên theo dõi được timeline.
- **MUST:** thu thập tối thiểu dữ liệu cần thiết; preview normalized payload; xác nhận; sử dụng idempotency key; cho phép rút bản nháp trước confirm.
- **MUST NOT:** hứa thời gian xử lý chưa được duyệt; đánh dấu `resolved` thay cán bộ; tạo ticket trùng khi retry.
- **Failure:** validation -> giữ dữ liệu người dùng và chỉ lỗi field; timeout sau confirm -> tra cứu bằng idempotency key trước khi cho retry; routing fail -> đưa `SVC-QUE-OPS-001`.
- **Acceptance evidence:** preview/confirm tests; duplicate retry test; routing test; timeline accessibility test.
- **Traceability:** `DEC-014`, `DEC-015`, `SVC-JRN-003`, `UX-ACT-001`–`UX-ACT-009`.

### SVC-CAT-004 — Document request

- **Actor/precondition:** sinh viên đã xác thực; request type được cấu hình.
- **Outcome:** tạo yêu cầu giấy tờ như một ticket có field nghiệp vụ; không phải phê duyệt hoặc phát hành giấy tự động.
- **MUST:** giải thích điều kiện, dữ liệu cần nộp và trạng thái; preview toàn bộ dữ liệu gửi; xác nhận.
- **MUST NOT:** tuyên bố hồ sơ được chấp nhận/phê duyệt khi chưa có cán bộ; tự tạo chữ ký, con dấu hoặc văn bản chính thức.
- **Failure:** thiếu loại giấy/config -> tạo general support ticket hoặc handover, không tự sinh quy trình.
- **Acceptance evidence:** schema per request type; preview test; no-false-approval copy test.
- **Traceability:** `DEC-005`, `DEC-015`, `SVC-JRN-004`, `UX-ACT-004`.

### SVC-CAT-005 — Room booking request

- **Actor/precondition:** sinh viên đã xác thực và có entitlement mô phỏng; room inventory khả dụng.
- **Outcome:** tạo booking request hoặc reservation theo policy mô phỏng, có thời gian/phòng/mục đích rõ ràng.
- **MUST:** kiểm tra conflict ngay trước confirm; hiển thị timezone, duration, rules và hậu quả; retry idempotent.
- **MUST NOT:** vượt policy, tự phê duyệt ngoại lệ, che giấu booking conflict hoặc tạo booking khi source state unknown.
- **Failure:** conflict -> không ghi, đưa tối đa ba lựa chọn hợp lệ; source unavailable -> không suy đoán availability.
- **Acceptance evidence:** conflict race test; preview test; unknown-source test; idempotency test.
- **Traceability:** `DEC-014`, `DEC-015`, `SVC-JRN-005`, `UX-ACT-005`.

### SVC-CAT-006 — Human handover

- **Actor:** sinh viên, AI policy, support officer hoặc operations admin.
- **Outcome:** case có queue, priority, reason code, transcript tối thiểu, citations, consent basis và ownership rõ ràng.
- **MUST:** cho phép người dùng yêu cầu gặp cán bộ bất kỳ lúc nào; thông báo chính xác trạng thái `queued`, không nói đã có người nhận khi chưa assigned.
- **MUST NOT:** gửi toàn bộ transcript nếu không cần; gộp case của hai người; loại handover chỉ vì classifier confidence thấp.
- **Failure:** target queue unavailable -> fallback queue `SVC-QUE-OPS-001` và alert vận hành; persist fail -> hiển thị lỗi rõ, không tuyên bố đã chuyển.
- **Acceptance evidence:** explicit-request handover; policy-trigger handover; minimal-data payload; queue-failure test.
- **Traceability:** `DEC-016`, `HITL-001`–`HITL-009`, `UX-HITL-001`–`UX-HITL-006`.

### SVC-CAT-007 — Knowledge administration

- **Actor/precondition:** knowledge administrator đã xác thực và được ủy quyền.
- **Outcome:** nguồn được nhập, kiểm tra, xem trước và publish/retire theo workflow có audit.
- **MUST:** hiển thị provenance, owner, status, version, effective dates và ingestion errors; yêu cầu review trước publish.
- **MUST NOT:** biến upload thành nguồn được trả lời ngay; cho phép nội dung tài liệu điều khiển agent; xóa audit/version history.
- **Failure:** malware/parser/prompt-injection suspicion -> quarantine; metadata thiếu -> `draft_invalid`; regression fail -> không publish.
- **Acceptance evidence:** lifecycle tests; quarantine UI; publish authorization; source-version rollback evidence.
- **Traceability:** `DEC-012`, `DEC-013`, `UX-SCR-020`–`UX-SCR-024`.

### SVC-CAT-008 — Operations oversight

- **Actor/precondition:** system/operations administrator đã xác thực, MFA requirement được policy xác nhận.
- **Outcome:** theo dõi health, queue, SLA, AI quality/cost và bật safe mode/kill switch theo quyền.
- **MUST:** phân biệt product KPI, system SLO và provisional human SLA; mọi thay đổi policy có audit và lý do.
- **MUST NOT:** cho phép xem plaintext secrets; thay citation/eval result thủ công; hạ guardrail không qua approval.
- **Failure:** telemetry thiếu -> dashboard hiển thị `unknown`, không hiển thị `0`; control action thất bại -> giữ trạng thái trước và alert.
- **Acceptance evidence:** unknown-data states; audit of control changes; permission tests; safe-mode drill.
- **Traceability:** `DEC-003`, `DEC-020`, `SVC-OPS-006`, `UX-SCR-025`–`UX-SCR-029`.

## 3. Ngoài phạm vi V1

Hệ thống MUST NOT triển khai trong V1: khách/phụ huynh/giảng viên/cố vấn, native mobile app, thanh toán, billing SaaS, quyết định điểm hoặc kỷ luật, tư vấn y khoa/pháp lý, tự liên hệ cơ quan bên ngoài, tự phê duyệt giấy tờ, hoặc truy cập database nguồn trực tiếp.

## 4. Điều kiện nghiệm thu catalog

- Mỗi endpoint/tool/UI task MUST nêu chính xác một hoặc nhiều `SVC-CAT-*`.
- Mỗi service MUST có ít nhất một positive test, một authorization/failure test và một recovery test.
- Không task nào được đổi outcome, actor hoặc forbidden behavior nếu không có behavioral change approval.
- Test report MUST map từng acceptance evidence về test ID hoặc ảnh/trace có timestamp.

