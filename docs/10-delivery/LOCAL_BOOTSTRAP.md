---
document_id: "DOC-DELIVERY-BOOTSTRAP-001"
version: "1.0.0"
status: "approved"
owner: "Developer Experience Lead"
approvers: ["Platform Lead", "Architecture Lead", "Security Lead"]
last_updated: "2026-09-22"
---

# Hướng dẫn Khởi chạy Cục bộ (Local Bootstrap Guide)

Tài liệu này hướng dẫn các bước khởi tạo, xác thực và dừng môi trường phát triển cục bộ cho Campus 24/7 (V1 — HUCE Demo) theo quyết định `TASK-DOC-DEV-001`. Toàn bộ quy trình chỉ sử dụng dữ liệu tổng hợp (synthetic-only) và giá trị cấu hình giữ chỗ (placeholder configuration); tuyệt đối không yêu cầu hoặc lưu trữ credential thật.

## 1. Yêu cầu công cụ tiền đề

- **Python**: `>= 3.12, < 3.14` kèm trình quản lý `uv`.
- **Node.js**: `>= 20.x LTS` kèm trình quản lý `pnpm`.
- **Docker Engine & Docker Compose**: Để chạy Postgres pgvector và Redis cục bộ.

## 2. Các bước khởi tạo môi trường

### Bước 1: Chuẩn bị cấu hình môi trường
Sao chép cấu hình mẫu an toàn, không chứa secret thật:
```powershell
Copy-Item .env.example .env
```

### Bước 2: Khởi động dịch vụ phụ trợ cục bộ
Khởi chạy cơ sở dữ liệu PostgreSQL (pgvector) và Redis bằng Docker Compose:
```powershell
docker compose up -d postgres redis
```

### Bước 3: Cài đặt dependencies theo lockfiles
Cài đặt thư viện đã được phê duyệt trong `docs/09-agent-execution/DEPENDENCY_ALLOWLIST.md`:
```powershell
uv sync
pnpm install
```

## 3. Lệnh kiểm tra xác thực cục bộ (Offline Preflight Checks)

Chạy bộ kiểm tra cấu trúc toàn vẹn không gọi mạng ngoài:
```powershell
$env:PYTHONDONTWRITEBYTECODE = "1"
powershell -ExecutionPolicy Bypass -File scripts/validate-tasks.ps1
python -m pytest -q
python contracts/tools/validate_openapi.py
python evals/validate_contracts.py
```

## 4. Khởi chạy ứng dụng

- **FastAPI API**:
  ```powershell
  uv run uvicorn campus247.bootstrap.app:create_app --factory --host 127.0.0.1 --port 8000 --reload
  ```
- **Next.js Web**:
  ```powershell
  pnpm --filter web dev
  ```

## 5. Dừng môi trường an toàn

Khi kết thúc phiên làm việc, dừng các container và dọn dẹp tài nguyên:
```powershell
docker compose down -v
```
