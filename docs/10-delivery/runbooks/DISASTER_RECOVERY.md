---
document_id: "DOC-RUNBOOK-002"
version: "1.0.0"
status: "reviewed"
owner: "Reliability Architect"
approvers: ["Architecture Lead", "Operations Lead", "Security Lead"]
last_updated: "2026-09-22"
---

# Runbook: Disaster Recovery & Backup Restoration

## 1. Overview & Service Level Objectives (SLO)
Tài liệu hướng dẫn quy trình ứng phó thảm họa, khôi phục cơ sở dữ liệu và phục hồi hệ thống Campus 24/7 theo quyết định kiến trúc `ADR-012` và biện pháp kiểm soát `SEC-CTRL-020`.

| Mục tiêu khôi phục | Chỉ số cam kết | Cơ chế kỹ thuật |
|---|---|---|
| **RPO (Recovery Point Objective)** | $\le$ 15 phút | RDS Aurora Continuous Automated Backup & WAL Archiving |
| **RTO (Recovery Time Objective)** | $\le$ 60 phút | Automated snapshot provision + CDK IaC redeployment |
| **Tính khả dụng (Target Availability)** | 99.9% / tháng | Multi-AZ (2 Availability Zones) failover tự động |

## 2. Recovery Scenarios & Playbooks

### 2.1 Kịch bản 1: Availability Zone (AZ) Failover Tự động
- **Hiện tượng**: Một AZ thuộc Region gặp sự cố điện hoặc mạng vật lý.
- **Hành vi hệ thống**:
  - AWS ALB tự động cô lập target tasks trong AZ lỗi, chuyển hướng sang AZ còn lại.
  - RDS Aurora tự động kích hoạt Read Replica thành Primary Writer trong vòng < 120s.
  - ElastiCache Redis failover sang replica node.
- **Thao tác vận hành**:
  1. Theo dõi CloudWatch Alarms: `RDSFailoverEvent`, `ECSHealthyHostCount`.
  2. Xác nhận connection pool tự động kết nối lại (`campus247-api`).

### 2.2 Kịch bản 2: Dữ liệu hỏng hoặc Thảm họa cấp Database (Point-in-Time Restore)
- **Quy tắc an toàn bất biến**: Tuyệt đối **không ghi đè trực tiếp** lên cluster database đang chạy. Mọi thao tác restore phải thực hiện trên cụm cô lập (isolated target).
- **Quy trình thực thi**:
  1. Xác định thời điểm cần phục hồi $T_{\text{target}}$ (không quá 15 phút so với thời điểm xảy ra sự cố).
  2. Kích hoạt script phục hồi kiểm định snapshot cô lập:
     ```powershell
     powershell -ExecutionPolicy Bypass -File scripts/dr/verify-postgres-restore.ps1 -SnapshotId "campus247-latest-snapshot" -TargetEnvironment "dr-isolated"
     ```
  3. Kiểm tra tính toàn vẹn (schema validation, row count, checksum outbox/audit).
  4. Cập nhật secret chuỗi kết nối database trong AWS Secrets Manager trỏ sang cụm đã phục hồi.
  5. Khởi động lại ECS Fargate tasks để nhận database connection mới.

### 2.3 Kịch bản 3: Phục hồi Toàn cụm Khu vực (Regional Disaster Recovery)
1. Xác định toàn bộ hạ tầng IaC từ kho lưu trữ Git (`infra/cdk`).
2. Triển khai lại hạ tầng tại Region dự phòng (khi có phê duyệt hợp thức hóa từ Security/Legal):
   ```bash
   pnpm --filter cdk deploy NetworkStack DatabaseStack ComputeStack EdgeStack
   ```
3. Phục hồi dữ liệu RDS từ cross-region replica snapshot.
4. Chạy smoke verification suite (`tests/operations/test_restore_script.py`).
5. Chuyển đổi bản ghi DNS Route 53 sang ALB mới.

## 3. Post-Recovery Verification Checklist
- [ ] Database readiness probe: `GET /health/ready` trả về HTTP 200 `status: ok`.
- [ ] Bảng `audit_event` và `outbox_event` bảo toàn tính liên tục, không mất mát giao dịch trước mốc RPO.
- [ ] Chạy kiểm thử smoke test toàn hệ thống `python -m pytest -q tests/operations/test_restore_script.py`.
- [ ] Lập biên bản sự cố (Post-Incident Review - PIR) trong vòng 24 giờ.
