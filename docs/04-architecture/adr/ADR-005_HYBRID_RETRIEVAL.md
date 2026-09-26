---
document_id: "DOC-ADR-005"
version: "1.0.0"
status: "draft"
owner: "AI and Retrieval Lead"
approvers: ["Architecture Lead", "AI Quality Lead", "Knowledge Owner"]
last_updated: "2026-09-21"
decision_status: "proposed"
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

