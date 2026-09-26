---
document_id: "DOC-PROD-002"
version: "1.1.0"
status: "reviewed"
owner: "Product Lead"
approvers: ["University Sponsor", "Finance Owner", "Product Owner"]
last_updated: "2026-09-22"
---

# Commercial business case

## 1. Executive summary

Campus 24/7 được xây như sản phẩm thương mại dành cho một trường trong V1, nhưng giai đoạn hiện tại chỉ dùng dữ liệu và integration mô phỏng. Đầu tư V1 nhằm chứng minh ba giả thuyết: người dùng tin và sử dụng câu trả lời có citation; cán bộ giảm việc lặp lại mà không mất quyền kiểm soát; chi phí trên mỗi phiên giải quyết được đủ thấp để vận hành bền vững.

Tài liệu này không tuyên bố HUCE là khách hàng hoặc đối tác. `HUCE Demo` chỉ là bối cảnh tham chiếu được chọn theo `DEC-002`.

## 2. Customer và buyer hypothesis

| Vai trò thương mại | Giả thuyết | Bằng chứng cần thu trong pilot |
|---|---|---|
| Economic buyer | Ban giám hiệu/đơn vị chuyển đổi số tài trợ ngân sách | Willingness-to-pay interview và budget range được ký nhận |
| Business owner | Đơn vị công tác sinh viên hoặc đầu mối dịch vụ sinh viên | Owner chấp nhận KPI, SLA và operating model |
| Technical buyer | Trung tâm CNTT/đơn vị hạ tầng | Architecture, identity, security và integration review đạt |
| Data owner | Đơn vị sở hữu SIS/LMS/ticket/document | Data-use approval và contract tích hợp |
| End user | Sinh viên và cán bộ hỗ trợ | Task success, CSAT và adoption telemetry |

Tên người và ngân sách thật chưa được xác định (`OQ-001`, `OQ-002`, `OQ-008`). Do đó mọi dự báo tài chính dưới đây là mô hình, MUST NOT được dùng làm cam kết thương mại.

## 3. Value proposition

### 3.1 Cho sinh viên

- Một cửa cho thông tin và tác vụ phổ biến.
- Citation, ngày hiệu lực và trạng thái nguồn giúp tự kiểm chứng.
- Theo dõi ticket/hồ sơ thay vì hỏi lại qua nhiều kênh.
- Có lối thoát rõ ràng tới cán bộ khi AI không đủ thẩm quyền.

### 3.2 Cho nhà trường

- Giảm yêu cầu lặp lại và thời gian phân tuyến.
- Chuẩn hóa câu trả lời theo nguồn được duyệt.
- Quan sát được khoảng trống tri thức, SLA, chất lượng và chi phí.
- Giữ quyền kiểm soát action, policy, publishing và handover.

### 3.3 Cho đơn vị vận hành sản phẩm

- Tách provider LLM và integration qua boundary để giảm lock-in.
- Có eval, audit và release gate trước khi thay model/prompt/source.
- Có đường mở rộng capability trong cùng trường mà không cần xây SaaS sớm.

## 4. Business model hypothesis

V1 giả định mô hình `annual institution license + implementation + support`, không triển khai billing trong sản phẩm.

| Thành phần | Cách định giá giả thuyết | V1 có implement? |
|---|---|---|
| License | Theo năm, theo dải active student/staff | Không; xử lý bằng hợp đồng ngoài hệ thống |
| Implementation | Phí cấu hình, ingestion, identity và integration | Không; theo statement of work |
| Support/SLA | Gói hỗ trợ theo giờ và mức SLO | Không; theo hợp đồng |
| Consumption overage | Ngưỡng request/model cost đã thỏa thuận | Chỉ đo và cảnh báo; chưa thu phí |
| Professional services | Tùy biến workflow/report/integration | Future commercial service |

V1 MUST NOT có checkout, payment, invoice, subscription engine, tenant billing hoặc license enforcement.

## 5. Cost model

Product team MUST duy trì mô hình chi phí tháng với ít nhất các biến sau:

```text
MonthlyCost = AwsFixedCost
            + DatabaseCost
            + StorageAndTransferCost
            + LlmInputTokenCost
            + LlmOutputTokenCost
            + EmbeddingAndRerankCost
            + NotificationCost
            + ObservabilityCost
            + SupportLaborCost
```

`BM-001 Cost per Verified Resolution = TotalVariableAndAllocatedCost / VerifiedResolvedSessions`.

Khi chưa có giá hợp đồng và usage thật, dashboard MUST gắn nhãn `estimated`. Agent MUST NOT hard-code bảng giá provider vào domain; pricing input phải là configuration có ngày hiệu lực.

## 6. Benefit model

```text
AvoidedHandlingHours = DeflectedEligibleRequests × BaselineAverageHandlingMinutes / 60
GrossOperationalBenefit = AvoidedHandlingHours × LoadedHourlyLaborCost
NetBenefit = GrossOperationalBenefit - MonthlyCost
```

Một request chỉ được coi là `deflected` khi outcome được xác minh và không phát sinh contact cùng intent trong cửa sổ 72 giờ. Product team MUST NOT tính lượt chat, click hoặc answer chưa grounded là lợi ích.

## 7. Investment stages

| Stage | Đầu tư | Exit evidence |
|---|---|---|
| Stage A — Simulated foundation | Tài liệu, synthetic corpus, mock integrations, eval và vertical slices | P0 requirements pass trên môi trường staging |
| Stage B — Controlled pilot readiness | Identity/integration thật trong sandbox, privacy/security review | OQ-001..008 được giải quyết; UAT và go-live review đạt |
| Stage C — Limited live pilot | Nhóm người dùng giới hạn, support và kill switch | KPI P0 đạt trong tối thiểu 4 tuần; không có Critical incident |
| Stage D — Commercial rollout | Hợp đồng, support model, capacity và DR | Buyer acceptance, signed SLA, production readiness |

Agent MUST NOT bỏ qua stage gate chỉ vì simulated demo chạy thành công.

## 8. Risks và mitigations

| Risk | Impact | Mitigation bắt buộc | Kill/hold condition |
|---|---|---|---|
| Câu trả lời sai nhưng tự tin | Mất quyền lợi/niềm tin | Citation, evidence threshold, abstention, eval | `KPI-002` hoặc `KPI-003` dưới gate |
| Truy cập hoặc ghi sai dữ liệu | Vi phạm an toàn/quyền riêng tư | AuthZ, preview, confirmation, idempotency | Bất kỳ event ở `KPI-006`/`KPI-007`/`KPI-008` |
| Không có người nhận handover | Kỳ vọng dịch vụ sai | Published hours, queue ownership, honest status | Không có owner cho queue P0 |
| Chi phí model không kiểm soát | Không bền vững | Routing, budget alert, cache phù hợp, BM-001 | Vượt hard budget được phê duyệt |
| Dùng tên HUCE gây hiểu nhầm | Rủi ro uy tín/pháp lý | Disclaimer bắt buộc, không dùng logo nếu chưa phép | Disclaimer thiếu trên entry surface |
| Synthetic data cho kết quả quá lạc quan | Quyết định sai | Adversarial eval và pilot thật trước thương mại | Chỉ có synthetic evidence nhưng đề xuất go-live |

## 9. Quyết định Go/No-Go thương mại

Go sang pilot thật chỉ khi toàn bộ điều kiện sau đúng:

- các owner tại OQ-001..008 đã được chỉ định và câu hỏi đã đóng;
- requirements, architecture, security/privacy, AI evaluation và operations pack ở trạng thái `approved`;
- KPI P0 đạt trên staging bằng test độc lập;
- hợp đồng/điều khoản provider và data transfer được duyệt;
- rollback, kill switch, incident response và support roster đã diễn tập.

Nếu bất kỳ điều kiện nào sai, quyết định MUST là `NO-GO` hoặc `CONDITIONAL-GO` có owner, deadline và giới hạn exposure; MUST NOT chuyển dữ liệu/người dùng thật vào hệ thống.
