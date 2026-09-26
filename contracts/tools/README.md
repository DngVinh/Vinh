---
document_id: "DOC-TOOL-002"
version: "1.0.0"
status: "reviewed"
owner: "Backend Architecture Lead"
approvers: ["AI Architecture Lead", "Security Architect", "QA Lead"]
last_updated: "2026-09-21"
---

# Tool contracts

## 1. Cách sử dụng

Các file `*.schema.yaml` là JSON Schema Draft 2020-12 biểu diễn bằng YAML. Các khóa control header ở top-level là annotation mở rộng; validator MUST dùng `$schema` và `$ref`/fragment được registry chỉ định.

Implementation order bắt buộc:

1. đọc `docs/05-ai/TOOL_USE_POLICY.md`;
2. load `tool-registry.yaml`;
3. validate broker invocation bằng `tool-invocation.schema.yaml`;
4. validate `arguments` bằng `input_schema_ref` của đúng tool;
5. authorize bằng trusted context ngoài model payload;
6. với write, tạo/validate preview và confirmation bằng schema tương ứng;
7. execute adapter và validate result bằng `output_schema_ref`;
8. emit audit event.

## 2. Contract rules

- Registry version là immutable release unit; mọi trace ghi exact version/hash.
- Tool ID/name/schema ref MUST match registry byte-for-byte.
- Schema object dùng `additionalProperties: false`.
- Format `uuid`, `date`, `date-time` MUST được validator cấu hình assert, không chỉ annotate.
- Tool arguments từ model MUST không chứa trusted context.
- Unknown tool, version hoặc schema MUST fail closed.
- Một tool contract không được tự tạo network/database access; adapter implementation thuộc task riêng.

## 3. Files

| File | Vai trò |
|---|---|
| `tool-registry.yaml` | Source of truth cho tool metadata/policy |
| `common.schema.yaml` | Shared scalar/error definitions |
| `tool-invocation.schema.yaml` | Internal broker invocation envelope |
| `tool-result.schema.yaml` | Normalized result envelope |
| `action-preview.schema.yaml` | Preview trước write |
| `confirmation.schema.yaml` | Confirmation resume payload/claims |
| `audit-event.schema.yaml` | Append-only audit event |
| `<tool>.schema.yaml` | Atomic input/output definitions |

## 4. Schema change

Compatible optional field vẫn cần version bump và tests. Required field, enum removal, semantic change, auth/confirmation change là breaking/security change theo governance. Agent MUST không sửa schema để phù hợp output hiện tại; implementation phải phù hợp contract hoặc tạo change request.

## 5. Acceptance evidence

- mọi schema compile với Draft 2020-12 validator;
- positive/negative fixture cho từng `$defs/input` và `$defs/output`;
- registry refs resolve;
- unknown/additional fields bị reject;
- registry hash/version xuất hiện trong trace;
- no cyclic unresolved `$ref`;
- generated bindings (nếu có) reproducible và không chỉnh tay.

## 6. Nguồn

Dialect chính thức: [JSON Schema Draft 2020-12](https://json-schema.org/draft/2020-12). DeepSeek tool parameters cũng được mô tả bằng JSON Schema nhưng application vẫn phải validate arguments: [DeepSeek Responses API](https://api-docs.deepseek.com/api/create-response/).

