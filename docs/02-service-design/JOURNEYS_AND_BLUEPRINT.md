---
document_id: "DOC-SVC-003"
version: "0.1.0"
status: "draft"
owner: "Service Design Lead"
approvers: ["Product Owner", "Student Support Lead", "Knowledge Lead"]
last_updated: "2026-09-21"
---

# Student/staff journeys và service blueprint

## 1. Nguyên tắc

Journey mô tả outcome của người dùng, không phải cấu trúc component. Agent MUST NOT rút gọn journey bằng cách bỏ confirmation, citation, handover hoặc recovery. Mọi insight chưa có nghiên cứu người dùng thật được coi là giả định cần kiểm chứng, không phải sự thật về HUCE.

Hướng dẫn chính thức về service design nhấn mạnh phải nghiên cứu cả người dùng cuối và người cung cấp hỗ trợ, đồng thời duy trì traceability từ user need tới user story: <https://www.gov.uk/service-manual/user-research/start-by-learning-user-needs>.

## 2. Student journeys

### SVC-JRN-001 — Tìm hiểu quy định có căn cứ

| Giai đoạn | Mục tiêu sinh viên | Frontstage bắt buộc | Backstage bắt buộc | Failure/recovery |
|---|---|---|---|---|
| Discover | Biết đây là AI mô phỏng và khả năng của nó | Disclosure ngắn, ví dụ câu hỏi, link quyền riêng tư | Load service mode và knowledge freshness | Config thiếu -> search/ticket-only mode |
| Ask | Mô tả câu hỏi tự nhiên | Chat input, attachment policy, stop generation | Safety/intent classification | Input vượt giới hạn -> chỉ rõ giới hạn và giữ draft |
| Retrieve | Chờ có trạng thái rõ | Progress không giả phần trăm | Hybrid retrieval, filter hiệu lực, rerank | Timeout -> retry có kiểm soát hoặc ticket |
| Understand | Nhận câu trả lời và căn cứ | Answer, inline citation, source panel, confidence language | Evidence gate, response validation | Evidence thiếu -> abstain |
| Act | Biết bước tiếp theo | Link thủ tục, tạo ticket hoặc hỏi tiếp | Permission/policy check | Action ngoài V1 -> handover |
| Verify | Tự kiểm chứng | Mở đúng đoạn/trang nguồn | Signed source reference/audit | Link hỏng -> report citation + ticket |

**Exit criteria:** sinh viên hiểu câu trả lời và kiểm chứng được, hoặc biết rõ vì sao hệ thống không thể trả lời và có kênh tiếp theo.

### SVC-JRN-002 — Xem lịch cá nhân

1. Sinh viên mở `Lịch của tôi`; nếu phiên hết hạn, hệ thống giữ destination và yêu cầu đăng nhập lại.
2. Hệ thống lấy identity từ session, MUST NOT dùng mã sinh viên do prompt/query tùy ý cung cấp.
3. UI hiển thị ngày/tuần, múi giờ, thời điểm đồng bộ và nguồn mô phỏng.
4. Lịch trống MUST có empty state khác với adapter lỗi.
5. Nếu dữ liệu cache cũ được dùng, UI MUST hiển thị `Cập nhật lần cuối ...` và không gọi nó là dữ liệu mới nhất.

**Exit criteria:** sinh viên thấy lịch của chính mình hoặc nhận trạng thái có thể hành động: đăng nhập lại, thử lại, hoặc tạo ticket.

### SVC-JRN-003 — Tạo và theo dõi ticket

1. Chọn loại yêu cầu hoặc để hệ thống gợi ý; sinh viên luôn có quyền đổi loại.
2. Thu thập field từng bước; giải thích lý do cần dữ liệu nhạy cảm trước khi nhập.
3. Hiển thị bản preview bất biến gồm recipient/queue, payload, attachment, priority dự kiến và SLA đã được phép công bố.
4. Sinh viên xác nhận rõ ràng; backend thực thi bằng confirmation token và idempotency key.
5. UI hiển thị trạng thái `Đang kiểm tra kết quả` nếu response bị mất; MUST NOT khuyến khích submit lại ngay.
6. Thành công hiển thị ticket ID, trạng thái, next step và timeline.
7. Mọi thay đổi trạng thái về sau hiển thị actor type và timestamp; không hiển thị ghi chú nội bộ.

**Exit criteria:** ticket tồn tại đúng một lần và sinh viên có bằng chứng, hoặc hệ thống xác nhận chưa tạo và giữ dữ liệu nháp.

### SVC-JRN-004 — Yêu cầu giấy tờ

Journey kế thừa `SVC-JRN-003` và thêm: điều kiện đủ, mục đích sử dụng, số bản/định dạng nếu catalog cho phép. UI MUST nói “gửi yêu cầu” thay vì “được cấp”. Nếu loại giấy không cấu hình, chuyển ticket chung; MUST NOT tự tạo quy trình.

### SVC-JRN-005 — Đặt phòng

1. Chọn ngày/giờ/phòng hoặc tiêu chí.
2. Hệ thống hiển thị availability hiện tại và thời điểm kiểm tra.
3. Sinh viên nhập mục đích; policy check quyền đặt.
4. Preview hiển thị phòng, ngày, giờ, duration, timezone, mục đích, policy và cơ chế hủy.
5. Ngay trước confirm, re-check conflict.
6. Conflict -> không ghi, giải thích trung tính và đưa lựa chọn khác.
7. Thành công -> booking/reference ID; nếu cần duyệt, trạng thái MUST là `pending_approval`, không phải `confirmed`.

### SVC-JRN-006 — Yêu cầu gặp cán bộ

1. Sinh viên chọn `Gặp cán bộ` ở bất kỳ thời điểm nào hoặc policy đề xuất handover.
2. UI giải thích dữ liệu sẽ được chuyển, queue dự kiến và giờ hỗ trợ đã được phê duyệt.
3. Sinh viên có thể loại bỏ nội dung không cần thiết trừ field bắt buộc được giải thích.
4. Sau khi gửi, UI hiển thị `Đã đưa vào hàng chờ`, queue, case ID và thời điểm; MUST NOT nói “cán bộ đang xử lý” khi chưa assigned.

### SVC-JRN-007 — Trường hợp nhạy cảm/khẩn cấp

1. Safety policy có thể kích hoạt bất cứ lúc nào, kể cả trước auth.
2. Luồng hội thoại thường dừng; hệ thống hiển thị nội dung hỗ trợ đã duyệt, mức độ giới hạn của AI và lựa chọn handover.
3. Chỉ hiển thị contact khi configuration có trạng thái `approved_active`.
4. Nếu contact chưa cấu hình, môi trường public MUST bị launch-block; môi trường demo hiển thị rõ `DEMO — chưa cấu hình đầu mối chính thức` và không tạo số giả.
5. Việc queue thành công chỉ xác nhận đã ghi case; không hứa con người đã đọc hoặc hành động.

## 3. Staff journeys

### SVC-JRN-101 — Nhận và xử lý case

1. Cán bộ mở queue được cấp quyền; default sort theo priority, breach risk và age, không theo AI confidence.
2. Cán bộ claim case bằng optimistic lock; claim conflict phải hiện rõ và refresh.
3. Workspace hiển thị reason, student-visible transcript tối thiểu, citations, policy flags và timeline.
4. Cán bộ xác minh nguồn trước khi gửi câu trả lời ảnh hưởng quyền lợi.
5. Cán bộ có thể reply, request information, transfer với reason, resolve với resolution code hoặc escalate.
6. Resolve bắt buộc note phù hợp và outcome; sinh viên nhận bản tóm tắt không chứa internal note.

### SVC-JRN-102 — Chuyển tuyến

1. Chọn target queue từ allowlist và reason code.
2. UI preview ownership/SLA impact và dữ liệu chuyển.
3. Transfer là atomic: target nhận ownership thì source mới mất ownership.
4. Nếu transfer fail, source giữ ownership; case MUST NOT rơi vào trạng thái không owner.

### SVC-JRN-103 — Quản trị tri thức

1. Upload/register source ở trạng thái `draft`.
2. Hoàn thiện metadata/provenance; chạy parsing, safety scan và preview chunks.
3. Chạy eval/regression; failure giữ tài liệu unpublished.
4. Reviewer khác hoặc approval rule phê duyệt publish theo policy.
5. Theo dõi citation failures/freshness; retire/supersede không xóa history.

### SVC-JRN-104 — Điều hành dịch vụ

1. Operations xem health, queue backlog, breach risk, AI quality/cost và data freshness.
2. `unknown` MUST được phân biệt với `zero`.
3. Khi vượt threshold, tạo incident/escalation; không chỉnh dữ liệu đo để “xanh hóa” dashboard.
4. Safe mode/kill switch yêu cầu confirmation và audit; kết quả phải được kiểm chứng bằng synthetic probe.

## 4. Service blueprint chuẩn

### SVC-BP-001 — Conversational service

| Layer | Thành phần | Owner | Evidence |
|---|---|---|---|
| User action | hỏi, đọc, mở citation, chọn next step | Student | UX analytics không chứa nội dung nhạy cảm |
| Frontstage | chat, disclosure, citation drawer, abstention, handover CTA | Product/UX | screenshot + accessibility result |
| Backstage | auth context, safety, retrieval, evidence gate, orchestration | AI/Backend | trace ID + policy/model/retrieval versions |
| Support process | source approval, eval, incident response | Knowledge/AI Quality/Ops | approval log + eval report |
| Data | conversation, retrieval run, citation, audit | Data owner | retention/access controls |
| Control boundary | no direct DB/tool side effects from LLM | Security/Architecture | authorization and negative tests |

### SVC-BP-002 — Transactional action

| Layer | Thành phần | MUST |
|---|---|---|
| User action | nhập dữ liệu -> review -> confirm | Người dùng có thể back/edit trước confirm |
| Frontstage | form/chat collection, action preview, result | Phân biệt preview, processing, success, unknown |
| Backstage | normalize, validate, authorize, create confirmation token, revalidate, execute idempotently | Token bind actor + payload hash + policy version + expiry |
| Support process | catalog owner, queue owner, incident/on-call | Có owner và fallback queue |
| Audit | preview_created, confirmation_received, tool_started, tool_result | Có correlation/idempotency ID; không log secret |

### SVC-BP-003 — Human-assisted service

| Layer | Thành phần | MUST |
|---|---|---|
| User action | yêu cầu trợ giúp/cung cấp consent context | Có thể yêu cầu người thật trực tiếp |
| Frontstage | handover preview, queue receipt, status timeline | Không hứa assignment/response chưa xảy ra |
| Backstage | classify, minimize payload, route, persist, notify | Persist trước khi acknowledge |
| Staff | triage, claim, verify, respond, transfer/resolve | Chỉ truy cập queue được cấp quyền |
| Oversight | backlog, breach risk, QA sample, escalation | Không dùng AI để tự đóng case |

## 5. Blueprint failure invariants

- Persist failure trước acknowledgement -> UI MUST báo chưa chuyển/chưa tạo.
- Response loss sau side effect -> lookup bằng idempotency/correlation trước retry.
- Queue routing failure -> fallback queue có alert; MUST NOT drop case.
- Citation resolver failure -> giữ answer nhưng dán nhãn citation unavailable và cung cấp report; với policy-critical answer, prefer abstain theo evidence policy.
- Auth expiry giữa flow -> giữ draft cục bộ an toàn, re-auth, re-authorize và tạo preview mới; confirmation cũ MUST invalid.
- Source/integration state `unknown` -> MUST NOT chuyển thành success/available/zero.

## 6. Acceptance evidence

Để nghiệm thu journey/blueprint, mỗi journey MUST có:

- happy-path screen recording hoặc E2E trace;
- ít nhất một recovery path và một authorization/safety path;
- event trace chứng minh trạng thái frontstage khớp backstage;
- accessibility evidence cho keyboard và screen reader của critical path;
- mapping sang các `UX-*` trong `docs/03-ux/UI_STATE_MATRIX.yaml`;
- review bởi ít nhất một đại diện student support; trước production phải có nghiên cứu với người dùng thật, gồm người có nhu cầu tiếp cận.

