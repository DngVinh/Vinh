---
document_id: "DOC-RUNBOOK-001"
version: "1.0.0"
status: "reviewed"
owner: "Operations Lead"
approvers: ["Architecture Lead", "Security Lead", "Reliability Architect"]
last_updated: "2026-09-22"
---

# Runbook: Degraded-Mode Operations & Capability Switches

## 1. Overview and Objectives
Runbook hướng dẫn quy trình vận hành, phát hiện sự cố, kích hoạt chế độ suy giảm an toàn (Safe-mode Degradation) và ngắt mạch khẩn cấp (Capability Kill-switch) cho hệ thống Campus 24/7 theo chuẩn `ARCH-007` và `SEC-IR-010`.

## 2. Capability Degradation Matrix
| State | Trigger | Allowed Actions | Forbidden Actions | Exit Condition |
|---|---|---|---|---|
| `NORMAL` | All services healthy | All approved capabilities | None outside security policy | Continuous health |
| `DEGRADED_NO_LLM` | LLM timeout / circuit open / 5xx | Document search, FAQ, Ticket read, Handover | Generative LLM answers, tool planning | LLM circuit closed & healthy probes |
| `DEGRADED_NO_INTEGRATION` | SIS / booking dependency down | FAQ, Ticket read, Handover | Booking create, External sync writes | Integration dependency restored |
| `DEGRADED_ASYNC_BACKLOG` | SQS queue age > 300s | Synchronous read/write | Bulk ingestion jobs | Queue backlog cleared |
| `READ_ONLY` | DB replication lag / audit alert | Read queries, FAQ, ticket view | All write actions (ticket/booking create) | Operator investigation complete |
| `SEARCH_ONLY` | AI safety incident / red-team trip | Lexical/vector doc search + citations | Generative completions, tool actions | Product/Security dual sign-off |
| `MAINTENANCE` | Planned schema migration | Health check endpoints only | All user traffic | Post-migration smoke passed |

## 3. Operational Execution Procedures

### 3.1 Inspecting Active State
```bash
# Query active capability state from API
curl -s http://localhost:8000/v1/capabilities | jq .
```
Expected output: JSON containing `system_state`, `capabilities`, `degradation_reason`, and `banner_message`.

### 3.2 Activating LLM Kill-Switch (DEGRADED_NO_LLM)
Khi phát hiện lỗi suy luận AI (DeepSeek timeout, hallucination hàng loạt hoặc circuit open):
1. Gọi API quản trị hoặc cập nhật Feature Flag qua `FeatureFlagService.set_kill_switch(FeatureFlag.LLM_GENERATION, kill=True, reason="LLM timeout")`.
2. Kiểm tra lại `/v1/capabilities`: cờ `chat_generation` chuyển sang `false`.
3. Kiểm tra giao diện người dùng hiển thị banner cảnh báo: "Hệ thống đang hoạt động ở chế độ dự phòng (tạm ngừng sinh câu trả lời AI tự động)."

### 3.3 Activating Read-Only Mode (READ_ONLY)
Khi phát hiện sự cố ghi dữ liệu hoặc lỗi cơ sở dữ liệu:
1. Kích hoạt cờ: `FeatureFlagService.set_safe_mode(SystemState.READ_ONLY, reason="Database incident")`.
2. Toàn bộ endpoint ghi (`POST /v1/tickets`, `POST /v1/rooms/reserve`) từ chối với mã lỗi `423 Locked` hoặc thông báo chuyển hướng an toàn.

## 4. Rollback and Recovery
1. Khôi phục dependency gốc và xác nhận chỉ số đo lường (SLI/SLO) trở lại ngưỡng an toàn trong 10 phút.
2. Huỷ bỏ kill-switch: `FeatureFlagService.set_safe_mode(SystemState.NORMAL)`.
3. Xác nhận `/v1/capabilities` trả về `system_state: NORMAL` và banner thông báo được dọn sạch.
