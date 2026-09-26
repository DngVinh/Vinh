---
document_id: "DOC-UX-005"
version: "0.1.0"
status: "reviewed"
owner: "Product Design Lead"
approvers: ["Knowledge Lead", "AI Quality Lead", "Accessibility Lead"]
last_updated: "2026-09-21"
---

# Trust, citation và AI disclosure UX

## 1. Mục tiêu

Trust UX phải giúp người dùng kiểm chứng, hiểu giới hạn và chọn bước tiếp theo; không được tạo “cảm giác đáng tin” chỉ bằng màu sắc, mascot hoặc ngôn ngữ chắc chắn. NIST AI RMF coi transparency, accountability và phân định human-AI roles là phần của quản trị rủi ro: <https://www.nist.gov/publications/artificial-intelligence-risk-management-framework-ai-rmf-10>.

## 2. AI disclosure

### UX-TRUST-001 — Persistent identity

- Assistant header MUST ghi `Trợ lý AI Campus 24/7` và `HUCE Demo — mô phỏng không chính thức`.
- First-use notice MUST nói AI có thể sai, câu trả lời quy định cần kiểm tra citation, và người dùng có thể chuyển cán bộ.
- Notice MUST ngắn; privacy/help page chứa chi tiết. User MAY dismiss first-use notice nhưng persistent label vẫn còn.
- Staff-authored message, system status và AI message MUST có label/visual semantics khác nhau.

Copy chuẩn:

> Đây là trợ lý AI trong môi trường mô phỏng, không phải kênh chính thức của Trường Đại học Xây dựng. Hãy kiểm tra nguồn trích dẫn trước khi thực hiện thủ tục. Bạn có thể yêu cầu gặp cán bộ bất kỳ lúc nào.

### UX-TRUST-002 — Capability and limit disclosure

Help/onboarding MUST liệt kê được/không được làm: tìm quy định, lịch mô phỏng, tạo yêu cầu sau xác nhận; không quyết định điểm/kỷ luật/tài chính, không chẩn đoán, không tự liên hệ khẩn cấp.

## 3. Citation presentation

### UX-TRUST-003 — Inline citation

- Mỗi claim về policy/procedure MUST có citation marker ngay sau câu/đoạn hỗ trợ, không chỉ danh sách cuối answer.
- Marker label dạng `[1]`, có accessible name `Nguồn 1: <source title>, <section/page>`.
- Một marker MAY support nhiều câu liền kề nếu phạm vi rõ; MUST không gắn một citation chung cho các claim khác nhau không được nguồn hỗ trợ.
- Citation count không được dùng như quality score.

### UX-TRUST-004 — Citation detail

Citation surface MUST hiển thị:

1. Tên nguồn và loại tài liệu.
2. Cơ quan/đơn vị ban hành nếu metadata có.
3. Số văn bản/version.
4. Điều/mục/trang hoặc anchor.
5. Ngày hiệu lực/hết hiệu lực và trạng thái tại thời điểm answer.
6. Excerpt đủ ngữ cảnh nhưng không vượt quyền/bản quyền.
7. Canonical URL hoặc document viewer.
8. Label `Dữ liệu mô phỏng` nếu source synthetic.
9. Thời điểm hệ thống truy xuất.

Missing metadata MUST hiển thị `Chưa có thông tin`, không đoán. Source link mở tab mới phải báo trước và dùng security-safe link behavior.

### UX-TRUST-005 — Citation-to-claim navigation

- Click/keyboard activate marker mở source và highlight đoạn nếu có anchor tin cậy.
- Nếu page/anchor resolver lỗi, vẫn hiển thị metadata và thông báo không định vị được đoạn; offer report.
- Back/close trả focus và scroll về marker ban đầu.

## 4. Evidence quality states

### UX-TRUST-006 — Sufficient evidence

Answer MAY dùng ngôn ngữ trực tiếp nhưng không vượt nội dung nguồn. UI không hiển thị numeric model confidence cho sinh viên. Evidence status là kết quả gate deterministic/eval, không phải cảm nhận model.

### UX-TRUST-007 — Insufficient evidence / abstention

Copy structure bắt buộc:

1. Nói phần nào chưa thể xác minh.
2. Nêu lý do ở mức hữu ích: thiếu nguồn còn hiệu lực, câu hỏi cần dữ liệu cá nhân, hoặc cần cán bộ quyết định.
3. Không đưa “câu trả lời phỏng đoán” sau lời từ chối.
4. Đưa tối đa ba lựa chọn: bổ sung thông tin, xem nguồn gần nhất có nhãn, tạo ticket/handover.

Copy mẫu:

> Mình chưa tìm thấy nguồn đang còn hiệu lực đủ để xác nhận nội dung này. Mình sẽ không đoán. Bạn có thể уточнить câu hỏi hoặc chuyển yêu cầu cho cán bộ.

Implementation MUST sửa từ ngoại ngữ `уточнить` trước release thành copy đã duyệt: `nói rõ hơn câu hỏi`; test copy MUST ngăn ký tự/ngôn ngữ ngoài glossary. Câu có lỗi này được giữ có chủ ý như một test fixture cho review, không được dùng production.

### UX-TRUST-008 — Conflicting or stale source

- Hiển thị warning `Các nguồn hiện có chưa thống nhất` hoặc `Nguồn có thể đã hết hiệu lực`.
- Nêu từng source/version/date; MUST không tự chọn source chiến thắng nếu governance rule không xác định.
- CTA ưu tiên `Chuyển cán bộ` và `Báo vấn đề nguồn`.

## 5. Tool/action provenance

### UX-TRUST-009 — System fact vs AI explanation

Ticket ID, schedule item, room availability, auth identity và action result MUST được render từ structured tool/system response. AI MAY giải thích nhưng MUST không sửa giá trị.

UI MUST label timestamp/source, ví dụ:

```text
Theo hệ thống lịch mô phỏng · cập nhật lúc 14:05, 21/09/2026
```

Nếu tool result stale/unknown, use corresponding state; AI response MUST không override.

## 6. Feedback and challenge

### UX-TRUST-010 — Answer feedback

- Options tối thiểu: `Hữu ích`, `Chưa hữu ích`, `Nguồn không đúng`, `Câu trả lời có thể gây hại`.
- Feedback MUST không đổi answer history/citation; tạo record riêng có response/source/model versions.
- Free text optional; privacy notice ngắn và data minimization.
- `Câu trả lời có thể gây hại` MUST route quality/safety review theo policy, không phải emergency contact mặc định.

### UX-TRUST-011 — Challenge and human review

Mọi answer/decision-like output ảnh hưởng quyền lợi MUST có đường `Yêu cầu cán bộ xem xét`. UI MUST không mô tả AI suggestion là “quyết định của nhà trường”.

## 7. Citation failure behavior

- Citation metadata fetch fail: marker giữ visible, detail shows recoverable error, report action.
- Canonical source unavailable: không xóa citation; show unavailable timestamp and cached metadata if valid.
- Claim lacks citation after validation: do not render completed answer; return abstention or regenerate within bounded attempt policy.
- Source revoked/superseded after answer: history shows status and warning; MUST not silently rewrite old answer.

## 8. Acceptance evidence

- Golden screenshots cho sufficient, abstained, conflict, stale, unavailable citation và synthetic source.
- Automated mapping test: every policy claim segment has citation reference resolving to metadata.
- Keyboard/screen-reader test open/close/source navigation.
- Test structured system facts cannot be overwritten by model text.
- Copy lint/test catches foreign accidental token in production strings, including test fixture above.
- User research evidence trước pilot: người dùng phân biệt được AI answer, official source và staff message.

