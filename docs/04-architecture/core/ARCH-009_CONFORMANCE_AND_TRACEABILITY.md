---
document_id: "DOC-ARCH-009"
version: "1.0.0"
status: "approved"
owner: "Architecture Governance Lead"
approvers: ["Architecture Lead", "Product Owner", "Security Lead", "QA Lead"]
last_updated: "2026-09-28"
---

# ARCH-009 — Architecture conformance và traceability

## 1. Mục đích

Tài liệu này biến kiến trúc thành quy tắc có thể kiểm tra cho coding agent. Nó không cấp quyền triển khai. Task chỉ được chạy khi tất cả nguồn tham chiếu đã `approved`, task ở trạng thái `ready` và dependencies `accepted`.

## 2. ARCH registry

| ID | Invariant | Evidence tối thiểu |
|---|---|---|
| `ARCH-001` | Bốn actor, một trường, simulation disclosure | E2E role tests + UI/API evidence |
| `ARCH-002` | Ba runtime: web/api/worker; PostgreSQL truth | Image/smoke/dependency tests |
| `ARCH-003` | Layer direction và bounded context ownership | Import graph + architecture tests |
| `ARCH-004` | Trust crossing có authz/validation/minimization | Data-flow + negative security tests |
| `ARCH-005` | ECS/Fargate private app, Multi-AZ data production | IaC assertions + failover/restore evidence |
| `ARCH-006` | Preview/confirm/idempotency/outbox | Integration/duplicate/crash tests |
| `ARCH-007` | Explicit degradation, bounded retry, scoped cache | Chaos/load/cache-isolation evidence |
| `ARCH-008` | Ports/adapters và provider-neutral gateway | Contract/provider/tool-boundary tests |
| `ARCH-009` | Task traceability và stop behavior | Task evidence schema + review log |

## 3. Required trace chain

Mọi implementation task **MUST** có chuỗi:

```text
OBJ/KPI
-> REQ or approved architecture enabler
-> ARCH/ADR
-> API/EVT/DATA/TOOL contract
-> TEST/EVAL case
-> TASK
-> verification evidence
```

Thiếu một mắt xích bắt buộc thì task status là `blocked`, không phải `completed_with_assumption`.

## 4. Architecture decision ownership

| Change | Classification | Required action |
|---|---|---|
| Rename nội bộ không đổi boundary/contract | Editorial/compatible | Owner review + tests |
| New library trong existing adapter | Compatible hoặc behavioral | Dependency/security review; task riêng |
| New datastore/queue/provider | Architectural | New/updated ADR; architecture + security approval |
| Move domain ownership | Breaking/behavioral | ADR + migration + trace update |
| New public endpoint/event/tool | Contract/behavioral | Approved contract + authz + tests |
| Auth, encryption, retention, outbound data | Security/privacy | Security/privacy approval |
| Kubernetes/microservice split/multi-tenancy | Major architectural | Business case, ADR, threat/cost/ops review |

Coding agent **MUST NOT** tự cập nhật ADR status hoặc đổi accepted decision để hợp thức hóa code.

## 5. Prohibited implementation patterns

Static/manual review **MUST** chặn:

- route gọi ORM/database trực tiếp;
- domain import FastAPI, LangGraph, AWS SDK hoặc provider SDK;
- DeepSeek/base URL/model hard-coded ngoài provider config/adapter test fixture;
- public S3 bucket, public ECS IP, public DB/cache;
- `tenant_id`/billing/tenant middleware trong V1 không có ADR;
- user-specific response có shared/public cache header;
- retry write không idempotency key;
- SQS handler không processed-event/idempotency strategy;
- model-generated SQL/URL/tool name được chạy trực tiếp;
- wildcard IAM action/resource khi có thể scope;
- log raw token, secret, full prompt/transcript hoặc direct identifier;
- migration phá hủy, `DROP`, broad delete hoặc force reset không có protocol/phê duyệt;
- TODO/placeholder trên production path mà behavior không fail closed.

## 6. Conformance checks

Tên command cuối do build specification định nghĩa, nhưng pipeline **MUST** có capability tương đương:

| Check ID | Check | Failure behavior |
|---|---|---|
| `ARCH-CHECK-001` | YAML header/ID uniqueness/link validation | Fail documentation gate |
| `ARCH-CHECK-002` | Mermaid parse/render | Fail documentation gate |
| `ARCH-CHECK-003` | Python import/layer boundary | Fail build |
| `ARCH-CHECK-004` | OpenAPI/event/schema backward compatibility | Fail build/release |
| `ARCH-CHECK-005` | IaC policy assertions | Fail deploy |
| `ARCH-CHECK-006` | Secret/dependency/container scan | Fail theo severity policy |
| `ARCH-CHECK-007` | Authorization and object-scope negative tests | Fail release |
| `ARCH-CHECK-008` | AI eval/regression | Fail model/prompt/corpus promotion |
| `ARCH-CHECK-009` | Load/failure test against capacity/SLO | Mark unverified; block production |
| `ARCH-CHECK-010` | Backup restore/rollback drill | Block production readiness |

Agent **MUST NOT** suppress rule, exclude file, lower threshold hoặc rewrite test để làm check pass nếu task không cho phép chính xác thay đổi đó.

## 7. Atomic task architecture input

Mỗi task ảnh hưởng kiến trúc **MUST** chứa tối thiểu:

```yaml
architecture:
  arch_ids: ["ARCH-003"]
  adr_ids: ["ADR-001"]
  bounded_context: "ticket"
  layer: "application"
  allowed_dependencies: ["domain.ticket", "ports.audit"]
  forbidden_dependencies: ["infrastructure.postgres", "provider.deepseek"]
  data_classification: "CONFIDENTIAL"
  side_effects: []
  network_calls: []
```

Nếu task có side effect hoặc network call nhưng khai báo rỗng, verification **MUST** fail.

## 8. Completion evidence schema

Coding agent phải trả machine-readable object:

```json
{
  "task_id": "TASK-API-TICKET-001",
  "result": "completed",
  "architecture_conformance": [
    {
      "id": "ARCH-003",
      "status": "passed",
      "evidence": ["command: architecture-test; exit_code: 0"]
    }
  ],
  "changed_files": [],
  "contracts_changed": [],
  "commands": [],
  "deviations": [],
  "residual_risks": []
}
```

`status` chỉ có `passed`, `failed`, `not_verified`. `not_verified` **MUST NOT** được đổi thành `passed` bằng narrative. `deviations` khác rỗng tạo change request; agent không tự accept.

## 9. Architecture review evidence

Reviewer **MUST** kiểm tra:

1. Diff chỉ nằm trong task scope và pre-existing changes được giữ nguyên.
2. Requirement/contract không bị implementation sửa ngược.
3. Dependency direction và ownership đúng.
4. Data path, log, cache và provider payload đúng classification.
5. Failure/timeout/retry/idempotency đã test.
6. Telemetry không làm lộ dữ liệu và đủ correlation.
7. Rollback/degradation behavior có thể vận hành.
8. Output evidence reproducible từ clean approved revision.

Review result:

```yaml
review:
  task_id: "TASK-..."
  reviewer_role: "Architecture Reviewer"
  source_revision: "git-sha"
  result: "accepted|changes_required|blocked"
  findings: []
  accepted_at: null
```

## 10. Failure/blocker schema

```json
{
  "result": "blocked",
  "blocker_code": "ARCHITECTURE_CONFLICT",
  "summary": "Task requires direct database access from a route handler.",
  "evidence": ["path:line", "ARCH-003#dependency-direction"],
  "impacted_ids": ["ARCH-003", "TASK-..."],
  "safe_options": ["Add an application use case through a reviewed task"],
  "files_changed_after_blocker": []
}
```

Agent **MUST** dừng trước mutation ngoài scope, không “tiện thể” refactor để gỡ blocker.

## 11. Architecture fitness and release gates

- Mỗi PR/task phải chạy relevant conformance checks.
- Nightly/staging chạy integration, eval, load subset và dependency drift.
- Trước production: full regression, security review, restore drill, cost review và open-question closure.
- Architecture drift được ghi issue/change request với owner/deadline; critical drift block release.
- Tách microservice, thêm cache hoặc tăng concurrency không được coi là “optimization” nếu chưa có measurement evidence.

## 12. Traceability và unresolved gates

Upstream: toàn bộ `docs/00-governance/**`, đặc biệt `DEC-017`–`DEC-021` và `DOCUMENT_CONTROL.md`.

Production vẫn bị chặn bởi `OQ-001`–`OQ-008`. Các open question này không chặn documentation hoặc synthetic implementation, nhưng coding agent **MUST NOT** thay chúng bằng fabricated values.

