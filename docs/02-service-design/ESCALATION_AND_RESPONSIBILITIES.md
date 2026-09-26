---
document_id: "DOC-SVC-008"
version: "0.1.0"
status: "draft"
owner: "Operations Lead"
approvers: ["Product Owner", "Security/Privacy Lead", "Student Support Lead"]
last_updated: "2026-09-21"
---

# Escalation matrix và staff responsibilities

## 1. Vai trò vận hành

### SVC-ROLE-001 — Support Officer

MUST triage/claim/reply/transfer/resolve trong queue được cấp; xác minh citation trước câu trả lời ảnh hưởng quyền lợi; giữ internal note tách khỏi student-visible reply; dùng reason code. MUST NOT truy cập queue restricted nếu không allowlist/training, sửa priority không lý do, hoặc dùng AI output như quyết định cuối.

### SVC-ROLE-002 — Queue Lead

MUST theo dõi unassigned/breach risk/capacity; điều phối transfer; review P0/P1 và sampling quality; bảo đảm shift handoff. MUST NOT xóa hoặc hạ priority để cải thiện metric.

### SVC-ROLE-003 — Student Support Lead

Accountable cho catalog hỗ trợ, queue ownership, staffing, macro/template và human SLA proposal. MUST phối hợp Product/Privacy khi yêu cầu thêm dữ liệu.

### SVC-ROLE-004 — Knowledge Administrator/Lead

MUST quản lý provenance/version/effective date, quarantine và publish workflow; xử lý citation defect. MUST NOT publish nguồn thiếu owner/approval hoặc thay nội dung gốc để khớp answer.

### SVC-ROLE-005 — Operations Administrator/Incident Commander

MUST giám sát health/backlog, điều phối incident, safe mode, communication và recovery evidence. MUST NOT phục hồi feature khi security/quality gate chưa pass.

### SVC-ROLE-006 — Security/Privacy Lead

MUST sở hữu unauthorized access/data incident, restricted access review, data-minimization, transfer/retention approval. Có quyền yêu cầu suspend capability trong phạm vi rủi ro.

### SVC-ROLE-007 — AI Quality Lead

MUST sở hữu eval set, threshold, prompt/model/retrieval regression và failure taxonomy. MUST NOT thay đổi outcome dữ liệu để đạt metric; model/prompt release phải traceable.

### SVC-ROLE-008 — Product Owner

Accountable cho scope/outcome/priority và go/no-go. Product Owner MUST NOT đơn phương hạ security/privacy control hoặc đóng risk thuộc owner khác.

## 2. Escalation levels

| ID | Level | Trigger ví dụ | Notify | Quyền hành động | Target |
|---|---|---|---|---|---|
| `SVC-ESC-001` | `SEV0` | data exposure đang diễn ra, auth bypass, unauthorized side effect diện rộng, safety flow gây nguy hiểm có hệ thống | Incident Commander, Security/Privacy, Product, Platform | suspend/safe mode theo runbook, bảo toàn evidence | Immediate; không phụ thuộc human SLA catalog |
| `SVC-ESC-002` | `SEV1` | P0 case không route, restricted queue unavailable, model/source poisoning nghiêm trọng, system-wide write result unknown | Ops, Security/AI Quality, queue lead, Product | disable capability, search-ticket-only, rollback | Acknowledge nội bộ theo on-call plan chưa được chốt |
| `SVC-ESC-003` | `SEV2` | queue backlog lớn, integration trọng yếu lỗi, citation defect ảnh hưởng nhiều answer | Ops, affected owner, Product | degraded mode, reroute, incident ticket | Theo approved operations target |
| `SVC-ESC-004` | `SEV3` | lỗi giới hạn/cosmetic, isolated low-impact defect | owning team | scheduled fix | Backlog priority |

Các human incident response target đang `UNCONFIGURED`; UI/customer communication MUST NOT tự công bố con số.

## 3. Escalation decision matrix

| Condition | Case priority | Incident severity | First owner | Mandatory action |
|---|---|---|---|---|
| Safety signal một người dùng, routing hoạt động | P0/P1 theo policy | Không mặc định là incident | Restricted queue lead | `HITL-005` playbook |
| Safety routing/config không hoạt động | P0 | SEV1 | Operations | chặn public flow, alert, fallback safe message |
| Unauthorized data shown cho một user | P0 | SEV0/SEV1 theo scope | Security/Privacy | contain, preserve evidence, suspend affected path |
| Duplicate booking/ticket do retry | P1 | SEV2; SEV1 nếu diện rộng | Operations + service owner | stop write path, reconcile, notify affected users theo approval |
| Citation sai ảnh hưởng quyền lợi | P1 | SEV2; nâng nếu systematic | Knowledge + AI Quality | unpublish/disable answer path, assess cases |
| LLM provider unavailable, deterministic flows tốt | P2 system | SEV2 | Operations | `search_ticket_only` |
| Human backlog breach | theo case | SEV2 nếu systemic | Queue Lead | capacity escalation, transparent communication |
| Dashboard data missing | P2/P3 | SEV2 nếu che risk | Operations | show `unknown`, repair telemetry |

Case priority và incident severity MUST được lưu riêng; không suy ra trực tiếp một từ một.

## 4. RACI theo hoạt động

| Activity | Product | Support Lead | Queue Lead/Officer | Knowledge | AI Quality | Ops | Security/Privacy |
|---|---|---|---|---|---|---|---|
| Approve service scope | A/R | C | I | C | C | C | C |
| Publish human SLA | A | R | C | I | I | C | C |
| Triage/resolve case | I | A | R | C | I | C | C for restricted |
| Publish knowledge | I | C | I | A/R | C | C | C for sensitive |
| Release prompt/model/retrieval | C | I | I | C | A/R | R | C |
| Change queue/routing policy | A | R | C | C | C | R | C |
| Activate safe mode | I/C | I | I | I | C | A/R | A/R for security trigger |
| Privacy/security incident | I/C | I | I | I | C | R | A/R |
| Production go/no-go | A | C | I | C | C | C | approval required |

`A` = Accountable, `R` = Responsible, `C` = Consulted, `I` = Informed. Nếu hai vai trò cùng `A/R` trong emergency control, bất kỳ owner nào được phép contain; phục hồi cần đồng thuận theo runbook.

## 5. Staff action controls

- Claim, transfer, priority change, resolve, reopen, restricted view và export MUST có audit event.
- Sensitive action SHOULD yêu cầu step-up authentication khi identity integration được bật; hiện là launch requirement cho Entra phase.
- Staff MUST nhập reason bằng code + note ngắn cho transfer/override; free text không thay reason code.
- Internal note MUST có banner “Không hiển thị cho sinh viên” và không được dùng để chứa secret hoặc nội dung xúc phạm.
- AI-generated draft MUST có nhãn, không auto-send; staff là actor gửi và chịu trách nhiệm xác minh.
- Audit history MUST không có UI delete/edit; correction tạo event mới.

## 6. Shift handover

### SVC-ESC-005 — Shift handover record

Mỗi case P0/P1 chưa đóng khi kết thúc ca MUST có:

```yaml
shift_handover:
  case_id: "uuid"
  current_owner: "role-or-staff-id"
  receiving_owner: "role-or-staff-id"
  status: "string"
  last_verified_fact: "string"
  next_action: "string"
  due_at: "RFC3339|null"
  risks: []
  acknowledged_at: "RFC3339|null"
```

Nếu `receiving_owner` hoặc `acknowledged_at` thiếu, source owner vẫn chịu trách nhiệm và queue lead nhận alert. MUST NOT coi email gửi đi là acknowledgement.

## 7. Acceptance evidence và failure behavior

- Role/permission matrix test cho từng staff action, gồm negative test.
- Incident drill cho SEV0, SEV1 và provider outage; evidence gồm timeline, decisions, recovery probe.
- Sample audit chứng minh override/transfer/resolve có actor/reason.
- Shift handover concurrency/failure test không tạo case vô chủ.
- Nếu owner/on-call/runbook chưa cấu hình, production gate MUST fail; demo MUST hiển thị owner role `UNASSIGNED` và không gửi notification giả.
- Nếu severity mâu thuẫn, chọn mức cao hơn tạm thời, preserve evidence và yêu cầu Incident Commander quyết định; MUST NOT tự hạ mức bằng AI.

