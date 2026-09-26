# Campus 24/7 evaluation fixtures

Thư mục này chứa hợp đồng đánh giá máy đọc và một bộ fixture tổng hợp nhỏ để phát triển grader, pipeline và regression gate mà không gọi provider trả phí. Đây **không** phải bộ release đầy đủ. Quota release chuẩn vẫn là các mức tối thiểu trong `docs/05-ai/EVALUATION_PLAN.md` (500 RAG, 150 tool, 100 safety, 100 injection, 100 abstention, 50 multi-turn và 300 routing).

## Nguyên tắc bất biến

- Tất cả dữ liệu là hư cấu, locale `vi-VN`, không chứa hồ sơ sinh viên thật.
- Mỗi case có `synthetic=true`, seed, generator version, provenance và license marker.
- `sealed_test` chỉ là nhãn cấu trúc trong sample; nội dung release sealed thực tế không được commit vào coding context.
- Deterministic assertions quyết định schema, authorization, confirmation, idempotency, citation existence và forbidden behavior. LLM-as-judge không được là gate duy nhất cho safety/security.
- Test mặc định dùng fake provider, fake tool adapter và virtual clock; không cần network, credential hay paid API.
- Case S1 có ít nhất hai reviewer IDs. Các ID reviewer ở đây là vai trò mô phỏng, không phải tên người thật.

## Cấu trúc

- `schemas/eval-case.schema.yaml`: hợp đồng case nguồn.
- `schemas/eval-result.schema.yaml`: kết quả một case/attempt đã redaction.
- `gates/regression-gates.yaml`: threshold và hard-zero release gate.
- `rubrics/*.yaml`: rubric semantic/deterministic.
- `datasets/*.jsonl`: fixture đại diện, mỗi dòng là một JSON object độc lập.
- `red-team/catalog.yaml`: taxonomy scenario và invariant bắt buộc.

## Quy ước chạy

1. Parse YAML và từng dòng JSONL với duplicate-key rejection.
2. Validate case bằng Draft 2020-12 với format assertion bật.
3. Materialize fixture theo `provider_fixture_ref`; thiếu fixture là `not_verified`, không phải pass.
4. Chạy deterministic assertions trước rubric semantic.
5. Ghi output theo `eval-result.schema.yaml`, không lưu raw secret, raw prompt nhạy cảm hoặc chain-of-thought.
6. Tổng hợp theo suite/subgroup, so baseline và áp dụng `regression-gates.yaml`.

## Dataset sample

Các file JSONL cố ý nhỏ, có case tích cực và tiêu cực cho grounded QA/citation, abstention, routing, tool safety, handover, prompt injection và privacy. Khi mở rộng, giữ nguyên ID đã phát hành, thêm case mới và chạy kiểm tra near-duplicate/split leakage; không nhân bản paraphrase chỉ để đạt quota.

## Validation tối thiểu

Một thay đổi chỉ đủ điều kiện review khi:

- toàn bộ YAML/JSONL parse được;
- mọi `$ref` nội bộ resolve;
- mọi JSON Schema compile theo Draft 2020-12;
- mọi case validate schema;
- case ID duy nhất trên toàn bộ dataset;
- hard-zero gate và baseline delta giữ nguyên theo tài liệu chuẩn;
- không có email/domain thật, student code thật, token hoặc contact khẩn cấp tưởng tượng.
