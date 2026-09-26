---
document_id: "DOC-PROD-KPI-001"
version: "1.1.0"
status: "reviewed"
owner: "Product Analytics"
approvers: ["Product Owner", "AI Quality Owner", "Service Owner"]
last_updated: "2026-09-22"
---

# KPI catalog

Mọi KPI phải được phân tách theo intent, nguồn, phiên bản model/prompt/retrieval và nhóm người dùng; số liệu thiếu phải hiển thị `unknown`, không mặc định bằng 0.

| ID | Tên và công thức | Mục tiêu V1 | Loại |
|---|---|---:|---|
| KPI-001 | `eligible_substantive_answers / eligible_questions` | >=70% | Online/offline |
| KPI-002 | `grounded_correct_answers / reviewed_answers` | >=90% | Eval + sample review |
| KPI-003 | `supporting_citations / evaluated_citations` | >=95% | Eval |
| KPI-004 | `queries_with_gold_source_in_top_10 / retrieval_queries` | >=90% | Offline eval |
| KPI-005 | Macro-F1 của định tuyến ticket | >=90% | Offline/online review |
| KPI-006 | Recall phát hiện critical cases | >=98%, 100% critical gold set trước release | Safety eval |
| KPI-007 | `confirmed_write_actions / executed_write_actions` | 100% | Security invariant |
| KPI-008 | Thao tác vượt quyền | 0 | Security invariant |
| KPI-009 | Duplicate side effects cùng idempotency key | 0 | Reliability invariant |
| KPI-010 | `monthly_active_students / eligible_pilot_students` | >=50% sau pilot thật | Adoption |
| KPI-011 | Điểm hài lòng sau phiên | >=4/5 | Experience |
| KPI-012 | `repeated_first_line_tickets_after / baseline` | giảm >=30% | Business outcome |
| KPI-013 | P95 thời gian trả lời FAQ hoàn chỉnh | <=6 giây | SLO |
| KPI-014 | P95 thời gian handover xuất hiện trong queue | <=5 giây | SLO |
| KPI-015 | `sessions_with_valid_cost / sessions` | 100% | FinOps data quality |
| KPI-016 | `verified_successful_outcomes / eligible_completed_workflows` | >=70% trong pilot thật | Outcome quality |
| KPI-017 | `successful_eligible_requests / eligible_requests` trong cửa sổ SLO | >=99.9%/tháng cho AI và read-only services | Availability |
| KPI-018 | P95 latency của capability được đo (FAQ/read-only/write theo lớp đo) | FAQ <=6s; read-only <=4s; write <=10s | Performance SLO |
| KPI-019 | `P0_journeys_passing_WCAG_2_2_AA / P0_journeys_tested` | 100%, không Critical/Serious mở | Accessibility |
| KPI-020 | `privacy_and_consent_controls_passing / applicable_privacy_and_consent_controls` | 100% | Privacy/control invariant |
| KPI-021 | Số vi phạm critical-control đã xác minh (synthetic boundary, security, safety hoặc representation) | 0 | Safety/security invariant |

## Quy tắc đo

- `eligible_question` loại trừ spam, input rỗng, truy vấn ngoài phạm vi rõ ràng và case buộc handover; lý do loại trừ phải có mã.
- Câu trả lời abstain không tính đúng và không tính sai trong grounded correctness, nhưng làm giảm answer coverage.
- MAU là sinh viên có ít nhất một phiên có chủ đích trong 30 ngày; refresh/login nền không tính.
- Một phiên resolved khi người dùng xác nhận hữu ích, hành động/ticket hoàn tất hoặc rubric vận hành xác định đã xử lý; chỉ gửi response không đủ.
- Dashboard phải hiển thị mẫu số và khoảng thời gian cạnh tỷ lệ.
- `KPI-018` phải ghi rõ capability, tải tham chiếu, phạm vi đo và loại trừ hợp lệ; không được gộp các ngưỡng khác loại vào một percentile không có ngữ cảnh.
- `KPI-021` là hard-zero invariant: một vi phạm đã xác minh làm gate liên quan thất bại, không được bù bằng tỷ lệ tốt.

## Business metric ngoài KPI catalog

`BM-001 Cost per Verified Resolution = TotalVariableAndAllocatedCost / VerifiedResolvedSessions` là business metric của commercial model, không phải `KPI-014`. Nó dùng effective pricing configuration và phải gắn nhãn `estimated` khi thiếu giá hợp đồng hoặc usage thật.
