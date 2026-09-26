---
document_id: "DOC-UX-001"
version: "0.1.0"
status: "reviewed"
owner: "Product Design Lead"
approvers: ["Product Owner", "Accessibility Lead", "Security/Privacy Lead"]
last_updated: "2026-09-21"
---

# UX specification index

## 1. Mục đích

Thư mục này định nghĩa hành vi giao diện chuẩn của Campus 24/7. Nó không định nghĩa framework component hoặc CSS implementation. Agent MUST giữ nguyên outcome, states, copy semantics, accessibility và trust boundaries; visual implementation MAY thay đổi nếu không phá contract.

Ngôn ngữ hiển thị V1 là tiếng Việt theo `ASM-004`. Web responsive/PWA là kênh chính theo `ASM-005`. WCAG 2.2 AA là target theo `ASM-010`.

## 2. Thứ tự đọc

1. Toàn bộ `docs/00-governance/**` và `docs/02-service-design/**`.
2. `INFORMATION_ARCHITECTURE.md`.
3. `SCREEN_INVENTORY.md`.
4. `INTERACTION_SPECIFICATIONS.md`.
5. `TRUST_AND_CITATION_UX.md`.
6. `ACTION_PREVIEW_AND_CONFIRMATION_UX.md`.
7. `SYSTEM_STATES_AND_RECOVERY.md`.
8. `ACCESSIBILITY.md`.
9. `CONTENT_STYLE_VI.md`.
10. `UI_STATE_MATRIX.yaml` trước khi implement state/rendering logic.

## 3. Normative rules

- `UI_STATE_MATRIX.yaml` là machine-readable state contract. Nếu prose và YAML mâu thuẫn, agent MUST dừng và raise blocker; không tự chọn.
- Mỗi screen/task MUST reference ít nhất một `UX-SCR-*`, state IDs liên quan và upstream `SVC-*`/`HITL-*`.
- Success MUST chỉ xuất hiện sau authoritative result; optimistic success bị cấm cho mọi write action.
- `unknown`, `empty`, `zero`, `not_authorized`, `offline` và `error` là các trạng thái khác nhau, MUST NOT dùng chung copy hoặc visual semantics.
- AI-generated content, deterministic system facts và staff-authored content MUST phân biệt bằng label/provenance.
- Agent MUST NOT thêm số liên hệ khẩn cấp hoặc human-response promise ngoài approved configuration.
- Responsive design MUST không làm mất hành động, citation, trạng thái hoặc evidence ở viewport nhỏ.

## 4. ID map

| Range | Ý nghĩa |
|---|---|
| `UX-IA-*` | Information architecture/navigation |
| `UX-SCR-*` | Screen/surface inventory |
| `UX-INT-*` | Interaction behavior |
| `UX-TRUST-*` | AI disclosure, citation, evidence và feedback |
| `UX-ACT-*` | Action preview, confirmation và result |
| `UX-STATE-*` | Loading/empty/error/offline/degraded states |
| `UX-A11Y-*` | Accessibility rules |
| `UX-CONTENT-*` | Vietnamese content rules |
| `UX-HITL-*` | Handover/emergency presentation |

## 5. Launch blockers

- `OQ-001`: chưa có Product Owner/người ký nghiệm thu UX.
- `OQ-003`: contact/message/staffed hours cho emergency chưa cấu hình; public safety UI không được launch.
- `OQ-004`: login/claim mapping thật chưa có; auth UI chỉ là simulation.
- `OQ-005`, `OQ-006`: privacy/retention copy production chưa được legal review.
- Chưa có user research với sinh viên/cán bộ thật, bao gồm người dùng có nhu cầu tiếp cận; mọi journey assumption phải được validate trước pilot thật.

## 6. Acceptance evidence

Mỗi UI micro-task MUST trả:

```yaml
ux_evidence:
  screen_ids: []
  state_ids_tested: []
  service_ids: []
  screenshots:
    - viewport: "360x800|768x1024|1440x900"
      path: "artifact path"
  keyboard_test: "passed|failed|not_applicable"
  screen_reader_test: "passed|failed|not_applicable"
  automated_accessibility_result: "summary"
  functional_test_ids: []
  copy_review: "passed|failed"
  deviations: []
```

Thiếu state/error/accessibility evidence -> task không được `accepted`.

## 7. Nguồn chuẩn

- WCAG 2.2 Recommendation: <https://www.w3.org/TR/WCAG22/>.
- WAI-ARIA Authoring Practices Guide: <https://www.w3.org/WAI/ARIA/apg/patterns/>.
- GOV.UK guidance về dịch vụ đơn giản, nhất quán và được test với người dùng: <https://www.gov.uk/service-manual/service-standard/point-4-make-the-service-simple-to-use>.

