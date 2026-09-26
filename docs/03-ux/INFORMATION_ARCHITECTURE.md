---
document_id: "DOC-UX-002"
version: "0.1.0"
status: "reviewed"
owner: "Information Architect"
approvers: ["Product Design Lead", "Product Owner", "Security/Privacy Lead"]
last_updated: "2026-09-21"
---

# Information architecture

## 1. Nguyên tắc tổ chức

- Navigation MUST theo mục tiêu người dùng, không theo tên microservice/phòng ban nội bộ.
- Mỗi vai trò chỉ thấy capability được phép; ẩn navigation không thay thế authorization server-side.
- Mỗi trang MUST có heading cấp 1 duy nhất, title có nghĩa và breadcrumb cho staff/admin hierarchy sâu.
- Critical action/status MUST không chỉ tồn tại trong chat transcript; phải có destination bền vững như ticket detail hoặc booking result.
- URL MUST deep-link được cho non-sensitive state. Sensitive data/filter MUST NOT đưa vào URL.
- Browser Back MUST không tự lặp write action hoặc bỏ qua confirmation.

## 2. Logical route map

Các route dưới đây là UX contract, không phải quyết định file-system router. Architecture MAY map kỹ thuật khác nhưng URL public MUST giữ tương thích hoặc có redirect được duyệt.

### UX-IA-001 — Public/auth

```text
/
/login
/auth/callback
/auth/error
/help
/accessibility
/privacy
/service-status
```

- `/` MUST nêu đây là `HUCE Demo` không chính thức và cung cấp login/help.
- Auth simulation MUST có nhãn rõ; production auth UI tương lai MUST giữ destination và không lộ raw provider error.

### UX-IA-002 — Student workspace

```text
/app
/app/assistant
/app/schedule
/app/tickets
/app/tickets/new
/app/tickets/:ticketId
/app/document-requests/new
/app/rooms
/app/rooms/request
/app/profile/privacy
```

Primary navigation labels: `Tổng quan`, `Trợ lý`, `Lịch học`, `Yêu cầu`, `Đặt phòng`. Privacy/help nằm trong account/support menu nhưng MUST vẫn keyboard reachable.

### UX-IA-003 — Staff workspace

```text
/staff
/staff/queues
/staff/queues/:queueId
/staff/cases/:caseId
/staff/reports/service
```

Primary labels: `Hàng chờ`, `Việc của tôi`, `Sắp vi phạm SLA`, `Báo cáo`. Restricted queue visibility phụ thuộc permission; direct URL không quyền -> `UX-STATE-010`.

### UX-IA-004 — Knowledge workspace

```text
/knowledge
/knowledge/sources
/knowledge/sources/new
/knowledge/sources/:sourceId
/knowledge/sources/:sourceId/versions/:versionId
/knowledge/reviews
/knowledge/quality
```

Primary labels: `Nguồn tri thức`, `Cần duyệt`, `Chất lượng`, `Lịch sử`. Upload không được đặt tên CTA là `Xuất bản`.

### UX-IA-005 — Operations workspace

```text
/operations
/operations/health
/operations/queues
/operations/incidents
/operations/controls
/operations/audit
/operations/configuration
```

Control pages MUST tách khỏi monitoring pages để giảm thao tác nhầm. Direct control URL cần authorization/step-up policy; dashboard MUST không chứa plaintext secret.

## 3. Role-access map

| Destination | Student | Support officer | Knowledge admin | Operations admin |
|---|---:|---:|---:|---:|
| Public/help/privacy | View | View | View | View |
| Student workspace | Own data only | No by default | No | No by default |
| Staff queues/cases | No | Assigned scopes | No | Operational metadata only unless separately granted |
| Knowledge workspace | No | Report defect only | Full lifecycle by policy | Health metadata only |
| Operations workspace | No | Limited report | Limited quality view | Authorized operations controls |
| Restricted case content | No broad access | Allowlist only | No | Incident role/allowlist only |

Agent MUST NOT infer access from table as backend policy implementation; security contracts remain authoritative. UI MUST render forbidden destination as absent from nav and direct-access denial as `UX-STATE-010`, not `404`, trừ khi security spec later requires resource hiding.

## 4. Navigation behavior

### UX-IA-006 — Student responsive navigation

- Desktop MAY dùng sidebar/top navigation; mobile MAY dùng bottom navigation hoặc menu.
- Five primary destinations MUST giữ label text hoặc accessible name rõ; icon-only primary nav bị cấm.
- Badge count MUST có accessible label và MUST không lộ restricted counts.
- Current page MUST có visual + semantic state (`aria-current="page"`).

### UX-IA-007 — Staff/admin navigation

- Sidebar MUST có collapse nhưng label vẫn available cho assistive technology.
- Queue switcher MUST hiển thị scope và unread/at-risk count; `unknown` không hiển thị `0`.
- Context switch giữa student/staff/admin MUST không tồn tại nếu một tài khoản không có role tương ứng.
- Khi role/context đổi, data cache của context trước MUST không xuất hiện thoáng qua.

### UX-IA-008 — Cross-service links

- Answer -> citation/source.
- Answer/abstention -> new ticket/handover với context preview, không auto-submit.
- Schedule item -> source detail/read-only, không thêm edit nếu V1 không hỗ trợ.
- Ticket timeline -> related booking/document request reference.
- Citation report -> knowledge-quality case không kèm personal transcript mặc định.

## 5. Search và findability

- Student global search trong V1 chỉ tìm public/authorized knowledge, không tìm hồ sơ người khác.
- Staff queue search MUST scope theo queue permission và audit nếu tìm bằng identifier cá nhân.
- Search results MUST nêu loại kết quả, source/status và snippet; MUST không trộn knowledge document với user ticket mà không phân nhóm.
- Zero results -> `UX-STATE-005`; search error -> `UX-STATE-007`.

## 6. Deep link và session behavior

- Protected deep link khi chưa auth -> lưu internal relative destination, login, rồi return; external open redirect bị cấm.
- Session hết hạn giữa form -> lưu draft cục bộ theo privacy policy, re-auth và revalidate; confirmation token cũ invalid.
- Opening case link without permission -> không fetch/render case detail trước authorization.
- Expired/deleted reference -> hiển thị trạng thái rõ và đường quay về list; không redirect im lặng về dashboard.

## 7. Acceptance evidence và failure behavior

- Route-to-screen and role table tests.
- Keyboard navigation recording cho student mobile/desktop và staff desktop.
- Direct URL negative tests cho từng role.
- Back/forward/reload tests chứng minh không lặp side effect.
- Auth expiry/deep-link/open-redirect tests.
- Nếu screen không có parent navigation hoặc access rule rõ, task MUST dừng và raise UX IA blocker.

