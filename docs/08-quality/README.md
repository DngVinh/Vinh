---
document_id: "DOC-QUAL-000"
version: "1.0.0"
status: "reviewed"
owner: "Quality Engineering Lead"
approvers: ["Product Owner", "Architecture Lead", "AI Quality Lead", "Security Lead", "Release Owner"]
last_updated: "2026-09-22"
---

# Quality engineering package

## 1. Mục đích và thẩm quyền

Gói này là đặc tả kiểm thử và release-quality cho **Campus 24/7 — HUCE Demo**. Nó chuyển requirement, contract, AI policy, security control và operational target thành test oracle, evidence và gate có thể thi hành. Đây là kế hoạch trước triển khai; trạng thái `reviewed` không có nghĩa hệ thống đã được code, test hoặc phê duyệt production.

Khi có xung đột, coding agent MUST dừng và áp dụng thứ tự thẩm quyền trong `docs/README.md`; agent MUST NOT hạ threshold, sửa oracle, bỏ test hoặc đổi trạng thái evidence để làm pipeline xanh.

## 2. Bất biến chất lượng

1. Chỉ dữ liệu tổng hợp có provenance, seed và checksum được dùng trong development, CI, staging, demo và evaluation.
2. Kết quả `missing`, `not_run`, `not_verified`, `inconclusive` hoặc test-infrastructure failure không bao giờ được tính là `passed`.
3. Mọi gate P0, Critical, S1, hard-zero và privacy launch blocker đều **fail-closed**.
4. Test assertion phải quan sát được ở API, state store, audit/event hoặc UI; narrative của agent không phải evidence.
5. LLM-as-judge không được là oracle duy nhất cho security, authorization, confirmation, idempotency, schema, leakage hoặc safety-critical behavior.
6. Release candidate là immutable tuple: source revision, image digest, config hash, contract hash, dataset hash, prompt/model/index/tool-policy version.
7. Không có tài liệu nào trong gói này cấp quyền deploy production hoặc sử dụng dữ liệu thật.

## 3. Danh mục tài liệu

| File | Nội dung chuẩn |
|---|---|
| `TEST_STRATEGY.md` | Mô hình rủi ro, môi trường, lane và chiến lược regression |
| `TEST_PYRAMID_AND_OWNERSHIP.md` | Tầng kiểm thử, ownership, cadence và flaky-test policy |
| `ACCEPTANCE_TEST_CATALOG.md` | Scenario Given/When/Then cho capability và failure path |
| `CONTRACT_TEST_PLAN.md` | OpenAPI, JSON Schema, tool, event, adapter và compatibility tests |
| `AI_EVALUATION_GATES.md` | AI/RAG/tool/safety metrics, hard-zero và promotion gate |
| `SECURITY_TEST_PLAN.md` | Authn/authz, privacy, abuse, supply-chain và infrastructure tests |
| `PERFORMANCE_RESILIENCE_TEST_PLAN.md` | Load model, latency, capacity, fault injection, RPO/RTO |
| `TEST_DATA_MANAGEMENT.md` | Synthetic fixtures, provenance, isolation, retention và canary scans |
| `TRACEABILITY_AND_EVIDENCE.md` | Evidence schema, lineage, retention và orphan detection |
| `RELEASE_QUALITY_GATES.md` | Gate sequence, thresholds, waiver và decision protocol |

## 4. ID và trạng thái

ID trong gói này là immutable:

- `TEST-UNIT-*`, `TEST-INT-*`, `TEST-CON-*`, `TEST-ACC-*`, `TEST-AI-*`, `TEST-SEC-*`, `TEST-PERF-*`, `TEST-RES-*`, `TEST-A11Y-*`, `TEST-DATA-*`, `TEST-OPS-*`;
- release gates dùng `GATE-REL-*`;
- defect dùng `DEF-<severity>-<sequence>`; waiver dùng `WVR-<year>-<sequence>`.

Một ID bị thay thế chuyển sang `superseded`; MUST NOT tái sử dụng. Trạng thái test run chỉ gồm `passed`, `failed`, `blocked`, `not_run`, `not_verified`, `inconclusive`. Chỉ `passed` từ đúng release tuple mới thỏa gate.

## 5. Contract cho micro-task kiểm thử

Gemini Flash MUST nhận một task có đúng một objective và tối đa một test family. Task tối thiểu phải chỉ rõ:

```yaml
test_task:
  task_id: TASK-TEST-<DOMAIN>-<NNN>
  test_ids: [TEST-...]
  traces_to: [REQ-F-..., REQ-NF-..., AI-..., SEC-..., OPS-...]
  dependencies: [TASK-...]
  allowed_write_paths: []
  fixtures: []
  preconditions: []
  action: "one observable action"
  oracle: "one deterministic expected result"
  negative_oracle: "forbidden effect"
  commands: []
  required_evidence: []
  exit_criteria: []
```

Agent MUST dừng nếu contract/fixture/dependency chưa tồn tại hoặc không approved; không tự sáng tác endpoint, schema, secret, production credential hay official HUCE contact.

## 6. Truy vết bắt buộc

Mỗi test phải có upstream `REQ-F`/`REQ-NF` hoặc architecture enabler, và khi liên quan phải thêm `AI/RAG/TOOL/EVAL`, `SEC/PRIV/THR`, `OPS/SLO`, `API/EVT/DATA`. Mỗi test phải chỉ tới một `GATE-REL-*` hoặc giải thích vì sao chỉ là informational. Quy tắc đầy đủ ở `TRACEABILITY_AND_EVIDENCE.md`.

## 7. Trạng thái hiện tại

Tài liệu quy định test và gate tương lai. Chưa có run ID, evidence bundle hay gate decision nào được tuyên bố là đã tạo. Production vẫn bị chặn bởi `OQ-001`–`OQ-008` và các điều kiện launch trong security/service package.
