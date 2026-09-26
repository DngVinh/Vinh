---
document_id: "DOC-AI-000"
version: "1.1.0"
status: "approved"
owner: "AI Architecture Lead"
approvers: ["Solution Architect", "AI Quality Lead", "Security Architect", "Product Owner"]
last_updated: "2026-09-22"
---

# Gói đặc tả AI, RAG, agent, tool và evaluation

## 1. Mục đích

Thư mục này là nguồn sự thật chuẩn tắc cho mọi hành vi có sử dụng mô hình ngôn ngữ trong Campus 24/7. Toàn bộ gói đặc tả AI, RAG pipeline, LangGraph state machine, typed tools policy và evaluation gates đã được phê duyệt chính thức (`status: approved`) cho phạm vi triển khai mô phỏng dữ liệu tổng hợp (synthetic implementation) ngày 2026-09-22 theo `TASK-DOC-AI-001`. Tài liệu được viết để một coding agent năng lực hạn chế có thể triển khai từng phần mà không phải tự chọn kiến trúc, tự nới quyền hoặc suy đoán tiêu chí nghiệm thu.

Các từ `MUST`, `MUST NOT`, `SHOULD`, `MAY` có nghĩa chuẩn tắc như quy định tại `docs/README.md`. Nếu tài liệu trong gói này mâu thuẫn với luật, quyết định đã accepted, product requirement, security/privacy policy hoặc contract đã approved, implementation agent MUST dừng và tạo blocker; agent MUST NOT tự hòa giải mâu thuẫn.

## 2. Phạm vi và ranh giới

Gói này bao phủ:

- hệ thống AI và phân chia trách nhiệm deterministic/LLM;
- controlled LangGraph state machine;
- provider-neutral LLM gateway với DeepSeek là adapter đầu tiên;
- prompt, structured output và model-routing governance;
- RAG ingestion, retrieval, reranking, citation và evidence gate;
- bộ nhớ hội thoại;
- policy và contract của tool;
- guardrail, prompt injection và phân loại tình huống nhạy cảm;
- dữ liệu tổng hợp, gold dataset, rubric, metric, regression gate và red team.

Gói này không định nghĩa database vật lý, endpoint HTTP công khai, AWS topology, UI hoặc chính sách bảo mật tổng thể. Những phần đó thuộc các domain khác. Tài liệu này chỉ định nghĩa interface và invariants mà các domain đó MUST đáp ứng.

## 3. Thứ tự đọc bắt buộc

| Thứ tự | Tài liệu | Nội dung |
|---:|---|---|
| 1 | `AI_SYSTEM_SPEC.md` | Ranh giới, trách nhiệm và invariant toàn hệ thống |
| 2 | `AGENT_STATE_MACHINE.md` | State, node, transition, retry, interrupt và terminal behavior |
| 3 | `LLM_GATEWAY.md` | Gateway, DeepSeek adapter và deterministic fake provider |
| 4 | `PROMPT_AND_OUTPUT_GOVERNANCE.md` | Prompt registry và structured output |
| 5 | `RAG_PIPELINE.md` | Ingestion đến evidence/citation |
| 6 | `MEMORY_POLICY.md` | Short-term và durable memory |
| 7 | `TOOL_USE_POLICY.md` | Authorization, confirmation, idempotency, timeout và audit |
| 8 | `GUARDRAILS_AND_SENSITIVE_CASES.md` | Safety pipeline và sensitive-case classifier |
| 9 | `ROUTING_COST_LATENCY.md` | Routing, budget, timeout và degradation |
| 10 | `SYNTHETIC_DATA_STRATEGY.md` | Corpus và dữ liệu mô phỏng |
| 11 | `EVALUATION_PLAN.md` | Dataset, rubric, metric và release gate |
| 12 | `RED_TEAM_CATALOG.md` | Danh mục tấn công và expected behavior |
| 13 | `TRACEABILITY.md` | Ma trận ID sang contract, eval và evidence |

Sau đó đọc `contracts/tools/README.md`, `contracts/tools/tool-registry.yaml`, các schema được tham chiếu và toàn bộ `evals/README.md`.

## 4. Quy tắc triển khai cho coding agent

1. Agent MUST chỉ triển khai một task ở trạng thái `ready` và đọc đầy đủ mọi `design_refs`, `contract_refs`, `eval_refs` của task.
2. Agent MUST NOT thay đổi ID, schema, threshold, transition, prompt contract hoặc tool policy để làm test pass.
3. Agent MUST dùng deterministic fake provider cho unit, integration và CI; test mặc định MUST NOT gọi DeepSeek hoặc dịch vụ trả phí.
4. Agent MUST validate input/output tại mọi trust boundary. Output của LLM luôn là dữ liệu không tin cậy, kể cả khi structured output được provider hỗ trợ.
5. Agent MUST NOT đưa quyền, `actor_id`, role, owner scope, confirmation status hoặc idempotency status vào phần dữ liệu do LLM quyết định. Những giá trị này chỉ đến từ trusted application context.
6. Agent MUST không thực thi side effect nếu authorization, schema validation, preview, confirmation hoặc idempotency check chưa thành công.
7. Agent MUST lưu evidence được yêu cầu trong task output; log “test passed” không thay thế cho exit code, case ID và artifact cụ thể.

## 5. Chia micro-task

Mỗi task implementation SHOULD thay đổi tối đa 1–3 product files, một layer và khoảng 150 dòng thêm mới. Các phần sau MUST là task riêng:

- schema/contract;
- provider interface;
- fake provider;
- DeepSeek adapter;
- một node của graph;
- một tool adapter;
- một guardrail;
- một metric hoặc grader;
- một corpus generator concern;
- một integration/eval suite.

Một task MUST dừng nếu cần sửa ngoài allowlist, cần dependency chưa phê duyệt, không tìm thấy contract hoặc cần thay đổi behavior chuẩn tắc.

## 6. Tình trạng phê duyệt

Các tài liệu đang ở trạng thái `reviewed`: đã được kiểm tra nội bộ về tính nhất quán nhưng chưa phải `approved`. Theo `DOC-...` control policy, orchestrator MUST NOT chuyển implementation task sang `ready` cho đến khi các approver trong header phê duyệt hoặc ban hành một accepted decision cho phép sử dụng bản reviewed trong môi trường mô phỏng.

