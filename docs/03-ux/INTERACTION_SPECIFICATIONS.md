---
document_id: "DOC-UX-004"
version: "0.1.0"
status: "reviewed"
owner: "Product Design Lead"
approvers: ["Accessibility Lead", "Service Design Lead", "Frontend Lead"]
last_updated: "2026-09-21"
---

# Interaction specifications

## 1. Global interaction rules

### UX-INT-001 — Input ownership

- User-entered data MUST remain editable until confirmation.
- Validation MUST occur on submit and MAY occur after blur; MUST NOT show error while user is still typing unless security-critical.
- Error summary MUST link/focus tới field lỗi, và inline error MUST mô tả cách sửa.
- Normalized value khác đáng kể input (timezone, room, date, identifier) MUST hiện trong preview.

### UX-INT-002 — Buttons và links

- Button thực hiện action; link điều hướng. Agent MUST NOT dùng clickable `div`.
- Primary CTA chỉ một cho mỗi decision region; destructive/risky CTA không dùng label mơ hồ như `OK`.
- Disabled control MUST có reason discoverable; khi có thể, giữ enabled và trả validation dễ hiểu tốt hơn disabled im lặng.
- Double-click/Enter repeat MUST không tạo side effect trùng.

### UX-INT-003 — Feedback timing

- Trong 100 ms: visual pressed/focus state.
- Tác vụ kéo dài > 1 giây: status text/spinner có accessible status.
- Tác vụ > 10 giây: giải thích đang làm gì, cho phép rời trang nếu safe và cung cấp cách xem kết quả.
- Không dùng progress percentage nếu backend không cung cấp tiến độ thật.

### UX-INT-004 — Toast/notification

- Toast chỉ cho kết quả không cần giữ lâu; ticket ID, result unknown, permission denial và safety message MUST có persistent inline/page content.
- Toast MUST không là nơi duy nhất hiển thị lỗi.
- Auto-dismiss chỉ cho success/info không critical; error/warning/action toast phải persistent hoặc có history.

## 2. Chat interaction

### UX-INT-010 — Composer

- `Enter` gửi trên desktop chỉ khi setting mặc định được nêu; `Shift+Enter` xuống dòng. Mobile Enter SHOULD xuống dòng và có nút gửi rõ.
- Nút gửi disabled khi input rỗng/whitespace; accessible reason không cần vì obvious.
- Character/file limits hiển thị trước vi phạm. Attachment chưa thuộc requirement MUST không xuất hiện.
- Message draft SHOULD survive route refresh trong cùng secure session; MUST bị xóa khi logout/account switch.

### UX-INT-011 — Response lifecycle

```text
submitted -> queued -> generating -> validating -> completed
                              |-> abstained
submitted|queued|generating|validating -> failed
generating -> stopped
```

- `generating` MAY stream text nhưng action/citation CTA chỉ active sau `validating` pass.
- Stopped partial answer MUST có label `Đã dừng — nội dung có thể chưa hoàn chỉnh` và MUST không cung cấp write CTA dựa trên partial text.
- Retry tạo response attempt mới, giữ attempt cũ và reason; không sửa lịch sử im lặng.
- `abstained` dùng content/action khác error: nêu thiếu căn cứ và offer clarification/ticket.

### UX-INT-012 — Conversation history

- Tên conversation MAY được model gợi ý nhưng phải sanitize; không hiển thị sensitive text ở sidebar mặc định.
- Switching conversation cancels local stream subscription nhưng không giả backend cancellation.
- Delete conversation không thuộc V1 nếu chưa có retention/backend contract; UI MUST không hiện nút giả.

## 3. Forms và multi-step flows

### UX-INT-020 — Stepper

- Step labels phản ánh user goal: `Thông tin`, `Kiểm tra`, `Xác nhận`, `Kết quả`.
- Back trước confirm không mất dữ liệu hợp lệ.
- Deep-link vào confirmation/result không có state hợp lệ -> chuyển về first incomplete step kèm explanation; không auto-submit.
- Stepper semantic list; current step announced.

### UX-INT-021 — Date/time

- Hiển thị ngày dạng `21/09/2026`, có textual alternative khi dễ nhầm; giờ 24h như `14:30` và timezone khi liên quan.
- Store/transport theo contract; UI MUST không tự chuyển timezone mà không hiển thị.
- Date picker MUST có keyboard path và manual input; không phụ thuộc chỉ vào calendar grid.

### UX-INT-022 — Attachment

- Chỉ implement khi requirement/contract quy định MIME/size/retention/scan.
- Upload state: selecting -> uploading -> scanning -> accepted/quarantined/failed.
- File quarantined MUST không preview/download và phải giải thích bước tiếp theo.

## 4. Data tables và queues

### UX-INT-030 — Table/list

- Mobile MAY đổi row thành cards nhưng phải giữ field/status/action.
- Sort state có label và programmatic announcement.
- Pagination/infinite load MUST giữ vị trí/focus khi quay lại detail.
- Bulk selection mặc định bị cấm cho resolve/transfer/restricted access.

### UX-INT-031 — Claim và concurrent edit

- Claim button chuyển `processing`; success chỉ khi server trả owner/version.
- Conflict hiển thị người/role đã claim nếu được phép và CTA refresh/back.
- Khi version stale, disable submit, hiển thị diff/refresh; MUST không overwrite tự động.

### UX-INT-032 — Reply vs internal note

- Hai mode có label, visual treatment và help text khác nhau.
- Switching mode với draft không rỗng cần confirmation để tránh gửi nhầm.
- Internal note composer MUST không có student notification controls.
- AI draft phải có label và cần staff review; không auto-send.

## 5. Dialog, drawer và focus

### UX-INT-040 — Modal criteria

Chỉ dùng modal cho một quyết định ngắn phải hoàn tất trước khi quay lại context: confirmation, permission explanation, critical control. Nội dung dài/có deep link dùng page hoặc non-modal drawer.

- Focus vào title/static intro khi nội dung cần đọc; với risky action, initial focus vào hành động ít rủi ro.
- `Tab`/`Shift+Tab` bị giữ trong modal; `Escape` đóng nếu đóng an toàn.
- Đóng trả focus về invoker hoặc destination hợp lý.
- Background phải inert thực sự khi `aria-modal="true"`.

Quy tắc dựa trên WAI-ARIA APG Dialog Pattern: <https://www.w3.org/WAI/ARIA/apg/patterns/dialog-modal/>.

### UX-INT-041 — Citation drawer

- MAY non-modal trên desktop để so sánh answer/source; mobile SHOULD full-screen dialog/page.
- Mở citation giữ vị trí answer; đóng trả focus tới citation trigger.
- Mỗi citation trigger có accessible name gồm số và source label.

## 6. Session, offline và navigation safety

### UX-INT-050 — Offline

- Read cache MAY hiển thị nếu policy cho phép, luôn có stale label/timestamp.
- Write CTA disabled hoặc chuyển draft local; MUST không queue side effect ngầm trừ requirement offline-sync riêng.
- Khi reconnect, UI MUST revalidate data và action preview; không auto-submit draft.

### UX-INT-051 — Auth expiry

- Giữ safe draft; mở re-auth; sau auth, re-fetch permissions/data và tạo preview mới.
- Nếu account khác đăng nhập, xóa/không expose draft cũ và quay về safe destination.

### UX-INT-052 — Unsaved changes

- Internal navigation/browser close MAY cảnh báo khi mất dữ liệu có ý nghĩa.
- Sau confirmation submit, không cảnh báo “unsaved”; chuyển sang processing/result reconciliation.

## 7. Acceptance evidence và failure behavior

- Interaction test cho pointer, keyboard, touch và repeated activation.
- State transition tests không cho impossible transition như `preview -> success` không qua confirm/processing.
- Concurrency/stale version tests cho staff case và room availability.
- Screen-reader status announcements không lặp toàn bộ streamed text.
- Nếu implementation cần state không có trong matrix, agent MUST dừng và tạo change request; không reuse state gần giống nhưng sai nghĩa.

