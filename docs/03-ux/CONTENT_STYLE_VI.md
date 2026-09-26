---
document_id: "DOC-UX-009"
version: "0.1.0"
status: "reviewed"
owner: "Content Design Lead"
approvers: ["Product Design Lead", "Student Support Lead", "Security/Privacy Lead"]
last_updated: "2026-09-21"
---

# Vietnamese content style

## 1. Voice và xưng hô

### UX-CONTENT-001 — Product voice

Nội dung MUST rõ, bình tĩnh, tôn trọng, cụ thể và trung thực về mức độ chắc chắn. Không dùng quảng cáo phóng đại như “thông minh tuyệt đối”, “chính xác 100%”, “giải quyết ngay lập tức”.

- UI/system dùng `Bạn` khi cần gọi người dùng; tránh lặp đại từ.
- AI có thể dùng `Mình` trong hội thoại thân thiện nhưng MUST giữ chuyên nghiệp; staff/system notifications không tự xưng `Mình`.
- Không gọi sinh viên là `em` vì quan hệ/tuổi không chắc chắn.
- Không dùng ngôn ngữ đổ lỗi: thay `Bạn nhập sai` bằng `Mã cần gồm 8 chữ số`.

### UX-CONTENT-002 — Plain Vietnamese

- Câu ưu tiên dưới 25 từ khi có thể; một câu một ý.
- Động từ/action đặt sớm; dùng từ người dùng hiểu thay tên hệ thống nội bộ.
- Technical term cần thiết được giải thích lần đầu; code/API identifiers không xuất hiện ở student UI.
- Không dùng English khi có thuật ngữ Việt rõ. Tên chuẩn như `ticket`, `SLA`, `AI` có thể dùng sau khi giải thích.

## 2. Names và labels

### UX-CONTENT-003 — Product/institution labels

- Product: `Campus 24/7`.
- Environment/institution label: `HUCE Demo`.
- Required disclosure: `Mô phỏng không chính thức`.
- MUST NOT viết như thể Trường Đại học Xây dựng đã bảo trợ/phê duyệt nếu chưa có authorization.

### UX-CONTENT-004 — Action labels

Use specific verbs:

| Intent | Use | Do not use |
|---|---|---|
| Create ticket | `Gửi yêu cầu` | `OK`, `Xong` |
| Room | `Xác nhận đặt phòng` hoặc `Gửi yêu cầu đặt phòng` theo result | `Đặt ngay` nếu còn approval |
| Handover | `Chuyển cho cán bộ` | `Gọi trợ giúp` nếu không gọi |
| Retry read | `Thử tải lại` | `Thử lại` khi effect mơ hồ |
| Reconcile write | `Kiểm tra kết quả` | `Gửi lại` |
| Publish | `Xuất bản phiên bản` | `Lưu` |
| Safe mode | `Chuyển sang chế độ an toàn` | `Tắt AI` nếu scope khác |

## 3. Status vocabulary

### UX-CONTENT-005 — Ticket/case status

| Internal state | Student label | Staff label |
|---|---|---|
| `queued` | `Đã tiếp nhận` | `Trong hàng chờ` |
| `claimed` | `Đã chuyển cán bộ phụ trách` | `Đã nhận` |
| `in_progress` | `Đang xử lý` | `Đang xử lý` |
| `waiting_student` | `Cần bạn bổ sung thông tin` | `Chờ sinh viên` |
| `transferred` | `Đã chuyển đơn vị phù hợp` | `Đã chuyển` |
| `resolved` | `Đã có kết quả` | `Đã xử lý` |
| `closed` | `Đã đóng` | `Đã đóng` |
| `escalated` | `Đang được ưu tiên xem xét` | `Đã chuyển cấp` |

Label student MUST không tiết lộ restricted queue/internal escalation detail. `claimed` chỉ hiển thị sau authoritative assignment.

### UX-CONTENT-006 — Data/system status

- `Đang tải…`, `Đang kiểm tra nguồn…`, `Dữ liệu chưa đầy đủ`, `Dữ liệu có thể đã cũ`, `Chưa xác định trạng thái`, `Không có dữ liệu`, `Không có kết quả phù hợp` là trạng thái khác nhau.
- MUST NOT dùng `0` thay `Chưa có dữ liệu`/`Chưa xác định`.
- `Thành công` chỉ khi action authoritative succeeded.

## 4. Date, time, number, identifier

### UX-CONTENT-007 — Formatting

- Date UI: `21/09/2026`; khi có rủi ro hiểu nhầm, thêm `21 tháng 9 năm 2026`.
- Time: 24-hour `14:30`; nêu timezone ở scheduling/action preview.
- Relative time MAY dùng kèm absolute timestamp trong detail (`5 phút trước · 14:30, 21/09/2026`).
- Number theo locale `vi-VN`; unit có khoảng trắng (`10 MB`, `5 phút`).
- Ticket/case/reference ID MUST giữ nguyên và có copy control với accessible feedback.

## 5. AI answers và certainty

### UX-CONTENT-008 — Grounded answer structure

1. Câu trả lời trực tiếp trong 1–3 câu.
2. Điều kiện/ngoại lệ quan trọng.
3. Các bước thực hiện dạng numbered list khi tuần tự.
4. Citation ngay sau claim.
5. Next action rõ.

Không mở đầu dài dòng hoặc lặp câu hỏi. Không nói `Theo hiểu biết của tôi`; dùng evidence state thực tế.

### UX-CONTENT-009 — Uncertainty/abstention

Approved pattern:

> Mình chưa tìm thấy nguồn đang còn hiệu lực đủ để xác nhận nội dung này nên sẽ không đoán. Bạn có thể nói rõ hơn câu hỏi hoặc chuyển yêu cầu cho cán bộ.

Do not use:

- `Có lẽ`, `chắc là` cho policy claim.
- `Hệ thống đảm bảo` hoặc `chắc chắn` nếu không có deterministic fact.
- Numeric confidence cho student-facing answer.

## 6. Error và recovery copy

### UX-CONTENT-010 — Error structure

Title: outcome không hoàn tất. Body: impact/effect status. Actions: recovery cụ thể.

Examples:

```text
Chưa thể tải lịch học
Dữ liệu lịch chưa được cập nhật. Không có thay đổi nào được thực hiện.
[Thử tải lại] [Tạo yêu cầu hỗ trợ]
```

```text
Đang kiểm tra kết quả gửi yêu cầu
Kết nối bị gián đoạn sau khi bạn xác nhận. Đừng gửi lại lúc này; hệ thống đang kiểm tra để tránh tạo yêu cầu trùng.
[Xem trạng thái]
```

MUST NOT expose stack trace, provider name, database error hoặc blame.

## 7. Sensitive/emergency content

### UX-CONTENT-011 — Tone

- Acknowledge ngắn, không phán xét, không phân tích tâm lý.
- Nêu giới hạn AI và lựa chọn thực tế.
- Contact copy lấy nguyên từ approved configuration; không chỉnh số/value bằng model.
- Không nói `Mọi chuyện sẽ ổn`, `Hãy bình tĩnh`, `Chúng tôi đã báo`, hoặc hứa người thật phản hồi khi chưa xảy ra.

Demo fallback duy nhất khi chưa có contact:

> DEMO — Chưa cấu hình đầu mối khẩn cấp chính thức. Phiên bản này không được dùng để xử lý tình huống khẩn cấp thực tế.

### UX-CONTENT-012 — Privacy explanation

Trước handover/sensitive field, nói dữ liệu nào được chia sẻ, với ai ở mức role/queue, để làm gì. Không dùng consent bundle mơ hồ; không hứa “bảo mật tuyệt đối”.

## 8. Accessibility/content mechanics

- Link text MUST mô tả destination; không dùng nhiều `Xem thêm` giống nhau không context.
- Heading/callout phải meaningful ngoài visual context.
- Alt text mô tả mục đích, không bắt đầu `Hình ảnh của`; decorative image alt rỗng.
- Acronym expanded first use: `thỏa thuận mức dịch vụ (SLA)`.
- Emoji không là status/label chính; decorative emoji nên ẩn assistive tech.
- All-caps chỉ cho short simulation token `DEMO`, không dùng đoạn dài.

## 9. Copy review và glossary

Glossary chuẩn:

| Symbol/internal term | User-facing Vietnamese |
|---|---|
| `ticket` | `yêu cầu hỗ trợ` (staff MAY dùng `ticket`) |
| `handover` | `chuyển cho cán bộ` |
| `queue` | `hàng chờ` hoặc `đơn vị tiếp nhận` theo audience |
| `citation` | `nguồn trích dẫn` |
| `abstain` | `chưa thể xác nhận` |
| `stale` | `dữ liệu có thể đã cũ` |
| `result_unknown` | `đang kiểm tra kết quả` |
| `safe mode` | `chế độ an toàn` |

Copy lặp lại MUST dùng catalog/localization key, không hard-code nhiều component. User-facing string change có ảnh hưởng policy/safety MUST được Content + domain owner review.

## 10. Acceptance evidence và failure behavior

- Copy lint không có raw internal enum/API/error/placeholder/contact chưa duyệt.
- Review consistency với glossary/status/action labels.
- Test long text, diacritics, line wrap và screen reader pronunciation.
- Safety, privacy, SLA và simulation copy có approver evidence.
- Nếu translation/copy chưa được duyệt cho safety/policy action, feature MUST dùng safe generic approved copy hoặc launch-block; model MUST không tự viết runtime instruction quan trọng.

