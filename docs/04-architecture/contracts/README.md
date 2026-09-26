---
document_id: "DOC-API-001"
version: "1.2.0"
status: "approved"
owner: "Solution Architect"
approvers: ["Product Owner", "Architecture Lead", "Security Lead", "Data Lead"]
last_updated: "2026-09-22"
---

# Gói hợp đồng dữ liệu, API, sự kiện và tích hợp

## 1. Mục đích và phạm vi

Thư mục này là nguồn sự thật cho các hợp đồng V1 nằm giữa miền nghiệp vụ và phần triển khai. Toàn bộ khế ước máy (OpenAPI v1, AsyncAPI v1, JSON Schema và Tool Schemas) đã được Solution Architect và các bên phê duyệt chính thức (`status: approved`) cho phạm vi triển khai mô phỏng dữ liệu tổng hợp (synthetic implementation) ngày 2026-09-22 theo `TASK-DOC-CONTRACT-001`. Gói này định nghĩa dữ liệu logic, vòng đời thực thể, HTTP API, lỗi, phân trang, idempotency, sự kiện tích hợp và biên hệ thống ngoài. Gói này **không** định nghĩa prompt, LLM tool schema, agent graph hoặc hành vi nội bộ của model.

Các thuật ngữ MUST, MUST NOT, SHOULD và MAY mang nghĩa chuẩn RFC. Khi tài liệu Markdown và artifact máy đọc khác nhau, agent MUST dừng với blocker `CONTRACT_MISMATCH`; không được tự chọn một phía.

## 2. Quyết định nền tảng

| ID | Quy tắc bắt buộc |
|---|---|
| API-BASE-001 | Mọi HTTP endpoint nghiệp vụ V1 MUST nằm dưới `/v1`; health endpoint MAY nằm ngoài version prefix. |
| API-BASE-002 | `contracts/openapi/v1/openapi.yaml` là hợp đồng HTTP máy đọc chuẩn. |
| DATA-BASE-001 | `contracts/json-schema/**` dùng JSON Schema Draft 2020-12 và `additionalProperties: false` tại mọi object biên, trừ khi schema ghi rõ ngoại lệ. |
| EVT-BASE-001 | Chỉ phát sự kiện sau khi transaction nghiệp vụ commit; producer MUST dùng transactional outbox hoặc cơ chế có đảm bảo tương đương. |
| INT-BASE-001 | V1 phục vụ một trường; implementation MUST NOT thêm `tenant_id`, billing SaaS hoặc tenant routing. |
| API-BASE-003 | Mọi write action do sinh viên khởi tạo MUST đi qua preview và explicit confirmation theo DEC-015. |
| DATA-BASE-002 | Development/demo MUST chỉ dùng synthetic data theo DEC-004. |
| API-BASE-004 | LLM MUST NOT được cấp trực tiếp bất kỳ contract nào trong gói này như một tool callable; tool contracts thuộc `docs/05-ai` và chỉ tham chiếu các domain API đã duyệt. |

## 3. Bản đồ artifact

| Artifact | Nội dung | IDs chính |
|---|---|---|
| [DATA_MODEL.md](DATA_MODEL.md) | Aggregate, quan hệ, ownership và invariant | `DATA-MOD-*` |
| [DATA_DICTIONARY.md](DATA_DICTIONARY.md) | Bảng, trường, kiểu, constraint và phân loại | `DATA-DIC-*` |
| [ENTITY_LIFECYCLES.md](ENTITY_LIFECYCLES.md) | State machine và transition guards | `DATA-LIFE-*` |
| [INTEGRATION_CATALOG.md](INTEGRATION_CATALOG.md) | Biên mock/Entra/DeepSeek/SIS/notification | `INT-*` |
| [API_CONVENTIONS.md](API_CONVENTIONS.md) | Quy ước REST, versioning, auth, concurrency | `API-CONV-*` |
| [ERROR_MODEL.md](ERROR_MODEL.md) | RFC 9457, problem registry và failure behavior | `API-ERR-*` |
| [PAGINATION_AND_IDEMPOTENCY.md](PAGINATION_AND_IDEMPOTENCY.md) | Cursor, replay và duplicate prevention | `API-PAGE-*`, `API-IDEM-*` |
| [EVENT_CONTRACTS.md](EVENT_CONTRACTS.md) | Event envelope, catalog và delivery semantics | `EVT-*` |
| `contracts/openapi/v1/openapi.yaml` | V1 HTTP API skeleton | `API-*` |
| `contracts/asyncapi/v1/asyncapi.yaml` | Internal event API | `EVT-*` |
| `contracts/json-schema/**` | Shared wire schemas | `DATA-*`, `API-*` |
| `contracts/json-schema/config/disclaimer.schema.json` | Public synthetic-demo disclosure | `REQ-F-PRIV-001`, `REQ-F-AUTH-004` |
| `contracts/json-schema/privacy/privacy-request.schema.json` | Privacy request, receipt, owner-visible status | `REQ-F-PRIV-003`, `REQ-F-PRIV-004` |
| `contracts/tools/validate_openapi.py` | Offline OpenAPI contract validator | `API-BASE-002` |

## 4. Thứ tự đọc bắt buộc cho coding agent

1. Đọc `docs/README.md` và toàn bộ `docs/00-governance/**`.
2. Đọc file task được giao và mọi `traceability` reference.
3. Đọc `DATA_MODEL.md`, phần entity liên quan trong `DATA_DICTIONARY.md` và state machine tương ứng.
4. Đọc `API_CONVENTIONS.md`, `ERROR_MODEL.md`, `PAGINATION_AND_IDEMPOTENCY.md`.
5. Đọc operation trong OpenAPI hoặc event trong AsyncAPI.
6. Validate mọi JSON instance bằng schema được `$ref`.

Agent MUST NOT bắt đầu code nếu artifact tham chiếu bị thiếu, status không phải `approved` khi task ở trạng thái `ready`, hoặc contract có lỗi parse/validate.

## 5. Chính sách thay đổi

- Thêm optional response field là thay đổi `compatible` nhưng vẫn cần bump version artifact và kiểm thử backward compatibility.
- Thêm required request field, đổi meaning, đổi enum/state, xóa endpoint hoặc đổi status code là `breaking`.
- Breaking API MUST tạo `/v2` hoặc có migration window được phê duyệt; không được sửa lặng lẽ `/v1`.
- Event consumer MUST bỏ qua field chưa biết; producer MUST NOT xóa/đổi meaning field trong cùng `event_version`.
- Schema ID và operation ID là immutable; ID đã xóa không được tái sử dụng.

## 6. Nguồn kỹ thuật chính thức

- [OpenAPI Specification 3.1.2](https://spec.openapis.org/oas/v3.1.2.html) định nghĩa mô tả API độc lập ngôn ngữ và kế thừa cách xử lý JSON Schema Draft 2020-12.
- [JSON Schema Draft 2020-12](https://json-schema.org/draft/2020-12) là dialect cho schema dùng chung.
- [RFC 9457](https://www.rfc-editor.org/rfc/rfc9457.html) định nghĩa `application/problem+json`.
- [AsyncAPI 3.0.0](https://www.asyncapi.com/docs/reference/specification/v3.0.0) là baseline cho mô tả event API.

## 7. Acceptance evidence

Gói chỉ đủ điều kiện chuyển `approved` khi có đủ:

- `openapi.yaml` parse được bằng validator hỗ trợ OAS 3.1.
- `asyncapi.yaml` parse được bằng validator hỗ trợ AsyncAPI 3.0.
- Mọi JSON Schema compile được theo Draft 2020-12 và examples hợp lệ.
- Không có `$ref` hỏng hoặc vòng tham chiếu không chủ ý.
- Mỗi endpoint có `operationId`, security, success response, problem response và traceability extension.
- Mỗi write operation chỉ rõ idempotency và optimistic concurrency nếu có.
- Mỗi event có owner, producer, consumer, partition key, PII class và replay behavior.
- Review xác nhận không có LLM tool contract trong gói.

### Lệnh kiểm tra bắt buộc

Chạy từ repository root, không cần network hay provider credential:

```powershell
python contracts/tools/validate_openapi.py
```

Validator kiểm tra YAML parse không trùng key, OpenAPI `3.1.2`, unique
`operationId`/`x-contract-id`, success response + problem-response policy,
traceability extension cho mọi operation, `REQ-*` tham chiếu có trong
`docs/01-product/requirements.yaml`, test-task tham chiếu tồn tại và mọi local
`$ref`/JSON Pointer resolve được. Nó không thay thế legal review, identity
provider review hoặc production launch gate.

Các schema cross-reference chính của HTTP contract là:

- `contracts/json-schema/common/error.schema.json`
- `contracts/json-schema/config/disclaimer.schema.json#/$defs/syntheticServiceDisclaimer`
- `contracts/json-schema/privacy/privacy-request.schema.json#/$defs/createRequest`
- `contracts/json-schema/privacy/privacy-request.schema.json#/$defs/receipt`
- `contracts/json-schema/privacy/privacy-request.schema.json#/$defs/statusView`

Nếu một kiểm tra thất bại, reviewer MUST giữ status `reviewed`, ghi exact file/path và không tạo task triển khai dựa trên phần lỗi.
