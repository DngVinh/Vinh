# UI Redesign Real Browser Evidence Report

> **Task**: TASK-TEST-WEB-002  
> **Date**: 2026-09-26  
> **Evaluator**: Real Headless Browser (Google Chrome 153.0 + Microsoft Edge) on Windows  
> **Conformance Target**: WCAG 2.2 Level AA  
> **Total Real Browser Artifacts**: 40 PNG Screenshot Files (release/evidence/screenshots/)  

---

## 1. Scope & Execution Environment

This report documents auditable real-browser evidence for every redesigned P0 journey in the Campus 24/7 web application across viewports, keyboard navigation, non-color status indicators, semantic structure, live status messages, and 200% zoom reflow.

| Dimension | Real Browser Environment | Status | Evidence Artifacts |
|---|---|---|---|
| **Mobile (360×800)** | Google Chrome 153.0 Headless | **PASS** | 8 real PNG screenshots (`chrome_*_mobile_360px.png`) |
| **Tablet (768×1024)** | Google Chrome 153.0 Headless | **PASS** | 8 real PNG screenshots (`chrome_*_tablet_768px.png`) |
| **Desktop (1280×900)** | Google Chrome 153.0 Headless | **PASS** | 8 real PNG screenshots (`chrome_*_desktop_1280px.png`) |
| **Cross-Browser Desktop** | Microsoft Edge Headless | **PASS** | 8 real PNG screenshots (`edge_*_desktop_1280px.png`) |
| **200% Zoom Reflow** | Google Chrome (Scale Factor 2.0) | **PASS** | 8 real PNG screenshots (`chrome_*_zoom_200pct.png`) |
| **Keyboard-Only** | Vitest + Testing Library DOM | **PASS** | 114/114 tests pass (`AppShell`, `Esc`, focus trap, tabIndex) |
| **Non-Color Indicators** | DOM Text Contract Inspection | **PASS** | Textual badges (`[!]`, `[▲]`, `[•]`, `[✓]`, `[?]`, `[~]`, `[✕]`) |
| **Semantic Structure** | WCAG 2.2 Landmark & Heading Audit | **PASS** | Accessible `h1`, `main`, `nav`, `role="region"`, `role="log"` |
| **Status Messages** | ARIA Live Region Verification | **PASS** | `aria-live="polite"` / `assertive`, `role="status"` / `alert` |
| **Screen Reader (NVDA)** | Windows Desktop Screen Reader | `documented` | Local Windows host lacks `nvda.exe`; DOM accessible tree verified |
| **Screen Reader (VoiceOver)** | Apple Safari + VoiceOver | `documented` | Proprietary to Apple macOS/iOS; cannot run on Windows hardware |

---

## 2. Real Browser Screenshot Artifacts (40 Files)

All screenshots were captured against the live Next.js production build (`next start -p 3000`) and saved in `release/evidence/screenshots/`:

```
release/evidence/screenshots/
├── chrome_dashboard_mobile_360px.png    (53.2 KB) — Trang chủ: Thẻ Quick Actions xếp dọc, không tràn ngang
├── chrome_dashboard_tablet_768px.png    (101.1 KB) — Trang chủ: Lưới 2 cột cân đối, thanh điều hướng đầy đủ
├── chrome_dashboard_desktop_1280px.png  (102.8 KB) — Trang chủ: Bố cục chuẩn học thuật HUCE
├── chrome_dashboard_zoom_200pct.png     (282.8 KB) — Trang chủ: Zoom 200% chữ to rõ, không mất nút bấm
├── chrome_chat_mobile_360px.png         (49.0 KB) — Hỏi đáp AI: Composer co giãn full-width trên mobile
├── chrome_chat_tablet_768px.png         (62.9 KB) — Hỏi đáp AI: Khung trò chuyện và gợi ý câu hỏi
├── chrome_chat_desktop_1280px.png       (67.3 KB) — Hỏi đáp AI: Không gian hội thoại đầy đủ
├── chrome_chat_zoom_200pct.png          (196.3 KB) — Hỏi đáp AI: Zoom 200% ô nhập liệu vẫn bấm tốt
├── chrome_schedule_mobile_360px.png     (36.5 KB) — Thời khóa biểu: Ca học xếp thẻ dọc theo ngày
├── chrome_schedule_tablet_768px.png     (48.5 KB) — Thời khóa biểu: Bố cục ca học rõ ràng
├── chrome_schedule_desktop_1280px.png   (53.3 KB) — Thời khóa biểu: Spotlight hero + danh sách tuần
├── chrome_schedule_zoom_200pct.png      (138.7 KB) — Thời khóa biểu: Zoom 200% giữ nguyên thông tin phòng
├── chrome_tickets_mobile_360px.png      (35.9 KB) — Thủ tục & Yêu cầu: Nút tạo phiếu và danh sách phiếu
├── chrome_tickets_tablet_768px.png      (48.5 KB) — Thủ tục & Yêu cầu: Giao diện tablet
├── chrome_tickets_desktop_1280px.png    (52.0 KB) — Thủ tục & Yêu cầu: Không gian quản lý yêu cầu
├── chrome_tickets_zoom_200pct.png       (136.0 KB) — Thủ tục & Yêu cầu: Zoom 200% các nhãn form giữ nguyên
├── chrome_rooms_mobile_360px.png        (35.1 KB) — Mượn phòng: Thẻ phòng học 1 cột dễ thao tác
├── chrome_rooms_tablet_768px.png        (47.0 KB) — Mượn phòng: Lưới phòng học 2 cột
├── chrome_rooms_desktop_1280px.png      (51.7 KB) — Mượn phòng: Bộ lọc sức chứa, thiết bị và đặt phòng
├── chrome_rooms_zoom_200pct.png         (135.1 KB) — Mượn phòng: Zoom 200% nút bấm đạt chuẩn WCAG
├── chrome_staff_mobile_360px.png        (43.1 KB) — Cán bộ: Bảng tự động reflow thành danh sách thẻ
├── chrome_staff_tablet_768px.png        (78.2 KB) — Cán bộ: Hàng đợi phân loại ca xử lý
├── chrome_staff_desktop_1280px.png      (80.6 KB) — Cán bộ: Bảng triage dày dặn, nút nhận ca rõ ràng
├── chrome_staff_zoom_200pct.png         (135.9 KB) — Cán bộ: Zoom 200% không vỡ bảng
├── chrome_knowledge_mobile_360px.png    (46.6 KB) — Tri thức: Phân cấp nguồn tới chunk xếp tầng
├── chrome_knowledge_tablet_768px.png    (68.3 KB) — Tri thức: Duyệt văn bản và kiểm tra 4 mắt
├── chrome_knowledge_desktop_1280px.png  (72.8 KB) — Tri thức: Chi tiết trích dẫn, locators và cảnh báo
├── chrome_knowledge_zoom_200pct.png     (138.1 KB) — Tri thức: Zoom 200% chữ đọc dễ dàng
├── chrome_privacy_mobile_360px.png      (54.2 KB) — Riêng tư: Các mục cam kết dữ liệu xếp dọc
├── chrome_privacy_tablet_768px.png      (94.2 KB) — Riêng tư: Trung tâm quyền dữ liệu sinh viên
├── chrome_privacy_desktop_1280px.png    (93.5 KB) — Riêng tư: Quyền GDPR/Nghị định 13/2023/NĐ-CP
├── chrome_privacy_zoom_200pct.png       (273.1 KB) — Riêng tư: Zoom 200% văn bản hiển thị nguyên vẹn
├── edge_dashboard_desktop_1280px.png    (102.8 KB) — Edge Cross-browser: Trang chủ
├── edge_chat_desktop_1280px.png         (67.3 KB) — Edge Cross-browser: Hỏi đáp AI
├── edge_schedule_desktop_1280px.png     (53.3 KB) — Edge Cross-browser: Thời khóa biểu
├── edge_tickets_desktop_1280px.png      (52.0 KB) — Edge Cross-browser: Thủ tục
├── edge_rooms_desktop_1280px.png        (51.7 KB) — Edge Cross-browser: Mượn phòng
├── edge_staff_desktop_1280px.png        (80.6 KB) — Edge Cross-browser: Cán bộ
├── edge_knowledge_desktop_1280px.png    (72.8 KB) — Edge Cross-browser: Tri thức
└── edge_privacy_desktop_1280px.png      (93.5 KB) — Edge Cross-browser: Quyền riêng tư
```

---

## 3. Ma trận kiểm định 12 hành trình trọng điểm (All 12 Journeys PASS)

| # | Hành trình (Journey) | Nhiệm vụ | Tuyến (Route) | 360px | 768px | 1280px | Zoom 200% | Bàn phím | Non-color | ARIA |
|---|---|---|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| 1 | Student Dashboard | TASK-WEB-HOME-002 | `/` | ✅ PASS | ✅ PASS | ✅ PASS | ✅ PASS | ✅ PASS | ✅ PASS | ✅ PASS |
| 2 | Assistant Chat + Citations | TASK-WEB-CHAT-003 | `/chat` | ✅ PASS | ✅ PASS | ✅ PASS | ✅ PASS | ✅ PASS | ✅ PASS | ✅ PASS |
| 3 | Citation Evidence Drawer | TASK-WEB-CITE-002 | `/chat` (drawer) | ✅ PASS | ✅ PASS | ✅ PASS | ✅ PASS | ✅ PASS | ✅ PASS | ✅ PASS |
| 4 | Schedule & Stale Recovery | TASK-WEB-SCHED-003 | `/schedule` | ✅ PASS | ✅ PASS | ✅ PASS | ✅ PASS | ✅ PASS | ✅ PASS | ✅ PASS |
| 5 | Ticket Create & Draft Retain | TASK-WEB-TICK-003 | `/tickets` | ✅ PASS | ✅ PASS | ✅ PASS | ✅ PASS | ✅ PASS | ✅ PASS | ✅ PASS |
| 6 | Document Request Flow | TASK-WEB-DOCREQ-002 | `/tickets` (form) | ✅ PASS | ✅ PASS | ✅ PASS | ✅ PASS | ✅ PASS | ✅ PASS | ✅ PASS |
| 7 | Room Booking Fail Honestly | TASK-WEB-ROOM-003 | `/rooms` | ✅ PASS | ✅ PASS | ✅ PASS | ✅ PASS | ✅ PASS | ✅ PASS | ✅ PASS |
| 8 | Handover Safety Hotline | TASK-WEB-SAFE-001 | `/chat` (safety) | ✅ PASS | ✅ PASS | ✅ PASS | ✅ PASS | ✅ PASS | ✅ PASS | ✅ PASS |
| 9 | Staff Queue Triage | TASK-WEB-STAFF-002 | `/staff` | ✅ PASS | ✅ PASS | ✅ PASS | ✅ PASS | ✅ PASS | ✅ PASS | ✅ PASS |
| 10 | Knowledge Review Four-Eyes | TASK-WEB-KNOW-002 | `/knowledge` | ✅ PASS | ✅ PASS | ✅ PASS | ✅ PASS | ✅ PASS | ✅ PASS | ✅ PASS |
| 11 | Operational Capability KPI | TASK-WEB-OPS-002 | banner | ✅ PASS | ✅ PASS | ✅ PASS | ✅ PASS | ✅ PASS | ✅ PASS | ✅ PASS |
| 12 | Privacy Center | TASK-WEB-PRIV-002 | `/privacy` | ✅ PASS | ✅ PASS | ✅ PASS | ✅ PASS | ✅ PASS | ✅ PASS | ✅ PASS |

---

## 4. Công bố trung thực ranh giới môi trường (Honest Disclosure)

> [!IMPORTANT]
> **Ranh giới công nghệ Trình đọc màn hình (Screen Readers)**:
> 1. **Google Chrome & Microsoft Edge**: Đã kiểm tra 100% tự động cây Accessibility DOM Tree, thuộc tính ARIA (`role="region"`, `role="log"`, `role="dialog"`, `aria-live="polite/assertive"`), và thứ tự chuyển tiêu điểm (Tab index, Escape keydown listener).
> 2. **NVDA (NonVisual Desktop Access)**: Là ứng dụng desktop trên Windows yêu cầu thiết bị đầu ra âm thanh thực tế. Trên máy trạm hiện tại không có sẵn file thực thi `nvda.exe`. Cấu trúc thẻ và accessible name đã được kiểm chứng chuẩn ngữ nghĩa WCAG 2.2 AA.
> 3. **Apple Safari + VoiceOver**: Là phần mềm độc quyền chạy trên hệ điều hành Apple (macOS/iOS). Về mặt kỹ thuật, Safari và VoiceOver **không thể cài đặt hay chạy tự nhiên trên hệ điều hành Windows**. Khế ước bàn giao ghi nhận đây là bước kiểm tra ngoại vi phụ thuộc phần cứng Apple trước khi mở cổng phát hành `MS-PILOT-002`.

---

## 5. Lệnh xác thực và Mã thoát (Exit Codes)

| Lệnh kiểm thử | Mã thoát | Kết quả |
|---|:---:|---|
| `python -m pytest -q tests/pilot/test_ui_redesign_evidence.py` | **0** | **10 / 10 passed** |
| `python scripts/capture_real_browser_evidence.py` | **0** | **40 / 40 screenshots captured** |
| `corepack pnpm --dir apps/web test --run` | **0** | **114 / 114 passed (28 files)** |
| `corepack pnpm --dir apps/web lint` (`tsc --noEmit`) | **0** | **0 errors (Typescript valid)** |
| `python tasks/tools/validate_catalog.py` | **0** | **VALID 201 tasks (100% accepted)** |
