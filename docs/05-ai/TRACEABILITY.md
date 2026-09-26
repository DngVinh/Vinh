---
document_id: "DOC-AI-008"
version: "1.1.0"
status: "approved"
owner: "AI Architecture Lead"
approvers: ["AI Quality Lead", "QA Lead", "Solution Architect"]
last_updated: "2026-09-22"
---

# Traceability matrix

## 1. Quy tắc

Ma trận truy vết AI behaviors, tools và evaluation gates đã được phê duyệt chính thức (`status: approved`) cho phạm vi triển khai synthetic implementation ngày 2026-09-22 theo `TASK-DOC-AI-001`. Mỗi implementation task thuộc gói AI MUST tham chiếu ít nhất một behavior ID dưới đây, contract/schema liên quan, eval case/suite và evidence command. Nếu row thiếu artifact downstream, task MUST ở `draft|blocked`, không `ready`.

## 2. Hệ thống và graph

| Behavior IDs | Design | Contracts | Eval/Gate | Evidence |
|---|---|---|---|---|
| AI-SYS-001, AI-NODE-006..009 | `AI_SYSTEM_SPEC.md`, `RAG_PIPELINE.md` | eval case/result schemas | EVAL-DATA-RAG-001, EVAL-METRIC-002..006 | retrieval/citation report |
| AI-SYS-002..004, AI-NODE-010..016 | `AGENT_STATE_MACHINE.md`, `TOOL_USE_POLICY.md` | tool registry, invocation, preview, confirmation | EVAL-DATA-TOOL-001, EVAL-METRIC-008..012 | auth/confirmation/idempotency tests |
| AI-SYS-005, AI-NODE-002..004,018..019 | `GUARDRAILS_AND_SENSITIVE_CASES.md` | handover schema | EVAL-DATA-SAFE-001, EVAL-METRIC-009 | safety confusion matrix + queue audit |
| AI-SYS-006..008 | `LLM_GATEWAY.md`, `PROMPT_AND_OUTPUT_GOVERNANCE.md` | JSON schemas + eval result | EVAL-METRIC-015 | contract/fake-provider/trace tests |
| AI-SYS-009 | `ROUTING_COST_LATENCY.md` | run/result schemas | regression gates | chaos/degraded-mode report |
| AI-SYS-010 | prompt, RAG, guardrails | strict schemas | EVAL-DATA-INJECT-001, EVAL-RED-* | red-team report |
| AI-SYS-011 | gateway, memory | audit schema | EVAL-RED-022/023 | log/trace inspection |
| AI-SYS-012 | system + synthetic strategy | dataset manifests | EVAL-RED-036 | UI/API content snapshots |

## 3. RAG

| IDs | Machine artifacts | Gate |
|---|---|---|
| RAG-ING-001..011 | dataset manifest schema, synthetic/gold manifests | source lifecycle/integrity report |
| RAG retrieval/fusion/rerank | eval case schema + RAG suite | Recall@10, exact-ID Recall@5, P95 |
| Citation/evidence gate | grounded rubric + eval result schema | citation precision/recall, zero invented IDs |

## 4. Tools

| Tool ID | Contract | Primary eval |
|---|---|---|
| TOOL-SCHEDULE-001 | `student-schedule-get.schema.yaml` | ownership, date range, redaction |
| TOOL-TICKET-001 | `ticket-create.schema.yaml` | preview/confirm/idempotency |
| TOOL-TICKET-002 | `ticket-get.schema.yaml` | owner/staff authorization |
| TOOL-DOCUMENT-001 | `document-request-create.schema.yaml` | allowed request types + confirmation |
| TOOL-ROOM-001 | `room-availability-search.schema.yaml` | bounded search/conflict |
| TOOL-ROOM-002 | `room-booking-create.schema.yaml` | availability recheck + confirmation |
| TOOL-HITL-001 | `handover-create.schema.yaml` | sensitive payload minimization/idempotency |

## 5. Eval artifact chain

```text
evals/schemas/eval-case.schema.yaml
  -> evals/datasets/gold-v1.manifest.yaml
  -> evals/datasets/samples/gold-v1.sample.yaml
  -> evals/rubrics/*.yaml
  -> evals/schemas/eval-run.schema.yaml
  -> evals/schemas/eval-result.schema.yaml
  -> evals/gates/regression-gates.yaml
```

## 6. Change impact

| Thay đổi | Suite tối thiểu phải chạy |
|---|---|
| Prompt/model/provider | routing + affected semantic suite + full safety/injection |
| Embedding/chunker/parser/retrieval | full RAG + abstention + injection-in-document |
| Tool schema/adapter | tool suite + auth/confirmation/idempotency + affected graph transitions |
| Memory/context builder | multi-turn + privacy/leakage + safety |
| Safety rule/classifier | full safety + benign control + injection |
| Cost/latency route | quality non-inferiority + load/cost + degradation |
| Source publication policy | RAG + poison/expired/unauthorized source suite |

## 7. Unresolved external traceability

Các product/security/platform requirement IDs chưa tồn tại trong write scope hiện tại. Khi những tài liệu đó được tạo, owner MUST cập nhật matrix để nối AI IDs với `REQ-*`, `SEC-*`, `PRIV-*`, `API-*`, `SLO-*` và `TEST-*`. Implementation agent MUST không tự phát minh các ID đó.

