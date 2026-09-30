---
document_id: "DOC-ADR-005"
version: "1.1.0"
status: "approved"
owner: "AI and Retrieval Lead"
approvers: ["Architecture Lead", "AI Quality Lead", "Knowledge Owner"]
last_updated: "2026-09-29"
decision_status: "accepted"
---

# ADR-005 — Hybrid lexical/vector retrieval và reranking

## Context

Campus queries chứa cả natural-language similarity lẫn exact identifiers như mã môn, số quyết định, tên biểu mẫu. Vector-only làm giảm exact-match reliability; lexical-only bỏ ngữ nghĩa/paraphrase.

## Decision

Retrieval pipeline **MUST**:

1. áp metadata/effective-date/audience filters;
2. lấy bounded lexical candidates bằng PostgreSQL FTS;
3. lấy bounded semantic candidates bằng pgvector;
4. fuse bằng deterministic rank-fusion algorithm đã version hóa;
5. rerank bằng approved deterministic/model component;
6. evidence gate trước generation;
7. trả citation tới immutable document version/section/page.

Algorithm, candidate count, score threshold và reranker version là config có eval, không magic constant rải rác.

## Accepted production profile

`rag-prod-v1.0.0` là production retrieval profile đầu tiên. Runtime MUST fail closed khi profile, embedding manifest, reranker revision hoặc index version không khớp.

| Setting | Accepted value |
|---|---|
| Embedding | `BAAI/bge-m3@5617a9f61b028005a4858fdac845db406aefb181`, dense output, 1024 dimensions, L2-normalized, cosine distance |
| Reranker | `BAAI/bge-reranker-v2-m3@953dc6f6f85a1b2dbfca4c34a2796e7dde08d41e`, cross-encoder score, multilingual |
| Candidate/fusion | `lexical_k=30`, `semantic_k=30`, RRF constant `60`, `fusion_k=20` |
| Rerank/context | tối đa 20 rerank inputs, tối đa 8 selected chunks, tối đa 6,000 context tokens |
| Deadlines | lexical 400 ms, semantic 700 ms, reranker 700 ms, retrieval+rereank hard deadline 1,800 ms; tối đa một retry chỉ cho lỗi transient còn đủ deadline |
| Fallback | một branch có thể degrade sang branch còn lại nếu SQL authorization/effective filters vẫn được bảo đảm và evidence gate pass; reranker failure dùng RRF order với degraded reason; hai branch fail hoặc filter assurance mất thì abstain |
| Evidence | calibrated support threshold `0.78`; mọi material claim phải có trusted citation trước stream commit; một repair tối đa và không được thêm evidence |
| Performance gate | p95 retrieval+rereank <= 1,800 ms, p99 <= 3,000 ms ở load profile `TP-RAG`; error rate < 1%; connection/memory budgets theo approved benchmark artifact |

Model artifacts MUST được lấy theo exact revision và checksum ghi trong embedding/index manifest. Inference chạy qua nội bộ/private endpoint; production runtime không tải mutable `main` revision. BGE-M3 có output dimension 1024 và hỗ trợ multilingual; model card upstream dùng giấy phép MIT. BGE reranker V2-M3 là multilingual và dùng Apache-2.0. Dependency/runtime packaging vẫn phải qua `TASK-RAGUP-DEPS-001` trước khi adapter được bật.

Approval evidence: direct human approval trong phiên triển khai `TASK-RAGUP-GOV-001` ngày 2026-09-29, bao phủ architecture, contract, model/dependency, security và quality decisions của profile trên. Approval không thay thế verification hoặc production credential/deployment controls.

## Alternatives

- Vector-only: rejected theo `DEC-012`.
- Lexical-only: không đủ paraphrase/multilingual/noisy query.
- Managed external search ngay: chưa cần; tăng data boundary và cost.

## Consequences

Recall và explainability tốt hơn nhưng query phức tạp, cần eval và index tuning. Reranker tăng latency/cost nên phải có fallback và budget.

## Constraints

- Corpus version **MUST** là phần của result/cache key.
- Expired/draft/quarantined document **MUST NOT** xuất hiện.
- No evidence => abstain/clarify/handover; **MUST NOT** generate unsupported answer.
- Search logs phải redact personal query theo policy.
- Tuning **MUST** report recall@k, citation precision, grounded correctness và latency/cost.

## Acceptance and failure

Gold dataset phải chứng minh lexical, vector và hybrid; hybrid phải đạt approved release thresholds, không chỉ average score. Khi reranker down, use fused result only if eval-approved fallback; nếu không, abstain. Index mismatch/corpus version mismatch block answer.

Sources: `SRC-POSTGRES-001`, `SRC-PGVECTOR-001`, `SRC-AWS-002`. Traceability: `DEC-012`, `DEC-013`, `ARCH-006`, `ARCH-007`.

