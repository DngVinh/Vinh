---
document_id: "DOC-UX-008"
version: "0.1.0"
status: "reviewed"
owner: "Accessibility Lead"
approvers: ["Product Design Lead", "Frontend Lead", "QA Lead"]
last_updated: "2026-09-21"
---

# Accessibility specification

## 1. Conformance target

Campus 24/7 MUST đáp ứng WCAG 2.2 Level AA cho toàn bộ V1, gồm student, staff, knowledge và operations surfaces. WCAG 2.2 là W3C Recommendation và tổ chức theo bốn nguyên tắc perceivable, operable, understandable, robust: <https://www.w3.org/TR/WCAG22/>.

Automated scan không đủ để tuyên bố conformance. Release evidence MUST gồm automated checks, keyboard-only, screen reader, zoom/reflow, color/contrast và critical-journey manual review.

## 2. Semantic structure

### UX-A11Y-001 — Landmarks/headings

- Mỗi page MUST có `main`, một `h1`, thứ tự heading logic và skip link tới nội dung chính.
- Navigation, search, complementary và form regions MUST có accessible name khi có nhiều vùng cùng loại.
- Visual size MUST không được dùng thay heading semantic.

### UX-A11Y-002 — Native controls first

- MUST ưu tiên native HTML: `button`, `a`, `input`, `select`, `textarea`, `table`, `dialog` khi phù hợp.
- Custom widget chỉ được dùng khi có keyboard/ARIA/state tests theo WAI-ARIA APG: <https://www.w3.org/WAI/ARIA/apg/patterns/>.
- `div`/`span` click handler không role/keyboard bị cấm.

## 3. Keyboard và focus

### UX-A11Y-003 — Keyboard complete

Mọi chức năng MUST dùng được không cần chuột, không keyboard trap, không yêu cầu gesture phức tạp duy nhất. Tab order theo visual/logical order; positive `tabindex` bị cấm.

### UX-A11Y-004 — Focus visibility

- Focus indicator MUST visible, có contrast/area phù hợp WCAG 2.2.
- Sticky header/banner/modal MUST không che focused element.
- Route change: focus tới `h1`/main intro theo pattern nhất quán; validation error focus error summary; background refresh không được cướp focus.
- Sau đóng modal/drawer, trả focus về invoker hoặc next logical target.

### UX-A11Y-005 — Modal/dialog

Modal MUST giữ focus, background inert, có accessible name, close control và `Escape` nếu safe. Risky confirmation đặt initial focus vào action an toàn. Thực hiện theo WAI APG Dialog Modal Pattern: <https://www.w3.org/WAI/ARIA/apg/patterns/dialog-modal/>.

## 4. Visual và responsive

### UX-A11Y-006 — Contrast/non-color

- Text/interactive/non-text contrast MUST đạt WCAG 2.2 AA applicable criteria.
- Status, priority, error, source quality và chart MUST không chỉ dựa màu; dùng text/icon/pattern semantic.
- Disabled state vẫn phải đọc được; nếu contrast exception áp dụng, help text/reason vẫn accessible.

### UX-A11Y-007 — Zoom/reflow/text spacing

- Content MUST hoạt động ở 200% zoom và reflow tại equivalent 320 CSS px không mất chức năng hoặc phải scroll hai chiều, trừ dữ liệu hai chiều thực sự như bảng.
- Text spacing override MUST không làm mất/che nội dung.
- Bảng rộng có accessible alternative hoặc horizontal region có label; actions không bị khuất.

### UX-A11Y-008 — Target size

Interactive targets SHOULD tối thiểu 44x44 CSS px; MUST ít nhất đáp ứng WCAG 2.2 AA Target Size (Minimum) và spacing/exception hợp lệ. Inline citation markers phải có hit area đủ mà không phá dòng.

### UX-A11Y-009 — Motion

- Respect `prefers-reduced-motion`.
- Không auto-scroll theo streaming nếu người dùng đã cuộn khỏi cuối; có button `Đến câu trả lời mới`.
- Animation không là cách duy nhất truyền trạng thái; no flashing content vượt ngưỡng WCAG.

## 5. Forms và authentication

### UX-A11Y-010 — Labels/instructions

- Mọi input có persistent programmatic label; placeholder không thay label.
- Required, format, units, limits và sensitive-data rationale được nêu trước input khi cần.
- Group dùng `fieldset/legend` hoặc equivalent.

### UX-A11Y-011 — Errors

- Error identified bằng text, linked tới field và có correction suggestion khi biết, trừ khi gây rủi ro bảo mật.
- Error summary ở đầu form focusable; input giữ giá trị hợp lệ.
- Quy tắc phù hợp WCAG Error Suggestion: <https://www.w3.org/WAI/WCAG22/Understanding/error-suggestion.html>.

### UX-A11Y-012 — Accessible authentication

- Không dùng cognitive-function test làm phương thức duy nhất.
- Cho phép password manager/paste khi mock auth có password; production OIDC không can thiệp provider flow.
- CAPTCHA nếu tương lai thêm cần alternative và approval; V1 MUST không tự thêm.

## 6. Dynamic content, chat và status

### UX-A11Y-013 — Status messages

- Loading/success/error/queue status phải programmatically available mà không bắt buộc focus.
- Dùng polite live region cho non-critical; assertive chỉ cho immediate critical alert.
- Streaming text MUST không announce từng token; announce phase/start và completed summary.
- Hướng dẫn W3C về status messages: <https://www.w3.org/WAI/WCAG22/Understanding/status-messages.html>.

### UX-A11Y-014 — Chat transcript

- Transcript là ordered semantic region; mỗi message có sender label và timestamp accessible.
- New message không cướp focus; cung cấp navigation tới latest/unread.
- AI/staff/system sender không chỉ phân biệt bằng avatar/màu.
- Citation marker có accessible name; opening source returns focus.

### UX-A11Y-015 — Data tables/charts

- Data table có caption/headers/scope; sortable header là button với sort state.
- Chart MUST có text summary và accessible data table/download only if authorized.
- `unknown`, missing, suppressed và zero có labels riêng.

## 7. Language và content

### UX-A11Y-016 — Language

- Page root `lang="vi"`; đoạn English/technical pronunciation quan trọng có `lang` phù hợp khi cần.
- Không trộn ngôn ngữ trong user-facing copy nếu có thuật ngữ Việt rõ; acronym được mở rộng lần đầu.
- Copy tuân theo `CONTENT_STYLE_VI.md`.

### UX-A11Y-017 — Time limits

- Session/confirmation expiry được thông báo trước nếu người dùng có thể gia hạn an toàn.
- Không dùng countdown gây áp lực. Extend/refresh MUST không auto-submit.
- Security timeout exception cần giải thích và preserve safe draft theo policy.

## 8. Safety và emergency accessibility

### UX-A11Y-018 — Critical message

- Safety message xuất hiện gần đầu current context, có heading rõ, concise text và action labels.
- Không dùng chỉ màu đỏ/animation/sound.
- Contact link phải nêu channel/value/purpose từ approved config; mobile tap target đủ lớn.
- Modal safety MUST không trap người dùng khỏi việc đóng hoặc dùng contact; no repeated interrupt loop.

## 9. Required test matrix

| Layer | Required evidence |
|---|---|
| Static/automated | semantic, name/role/value, contrast, common WCAG violations; no serious/critical issue |
| Keyboard | all critical journeys, visible focus, modal, menu, table, citation, error recovery |
| Screen reader Windows | latest supported NVDA + Chrome/Edge critical journeys |
| Screen reader Apple | VoiceOver + Safari for student responsive critical journeys |
| Zoom/reflow | 200%, 400% where applicable, 320 CSS px equivalent |
| Visual | high contrast/forced colors where supported, reduced motion, light/dark only if both shipped |
| Content | heading/link labels, error clarity, language attributes |

Browser/AT exact versions MUST được ghi trong test report; “latest” trong tài liệu không thay versioned evidence lúc release.

Critical journeys: login, ask/open citation, schedule, create ticket preview-confirm-result, room conflict, handover/safety, staff claim/reply/transfer, knowledge review/publish, operations safe-mode confirmation.

## 10. Acceptance và failure policy

- Bất kỳ WCAG A/AA failure trên critical path là release blocker.
- Serious/critical automated violation là blocker; automated pass không đủ nếu manual fail.
- Nếu third-party identity/widget không accessible, record vendor blocker và cung cấp approved alternative trước launch.
- Accessibility exception cần scope, criterion, user impact, workaround, owner, due date và approver; agent MUST NOT tự miễn trừ.
- Evidence MUST link mỗi `UX-A11Y-*` tới test ID/result/artifact.

