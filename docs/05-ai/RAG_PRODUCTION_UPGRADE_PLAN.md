---
document_id: "DOC-RAG-UPGRADE-001"
version: "1.0.0"
status: "draft"
owner: "AI and Retrieval Lead"
approvers: ["AI Architecture Lead", "Knowledge Governance Lead", "Security Architect", "AI Quality Lead"]
last_updated: "2026-09-29"
supersedes: null
---

# Production RAG Upgrade Plan

## 1. Mục đích và phạm vi

Tài liệu này chuyển báo cáo audit RAG thành backlog micro-task có thể thực thi và kiểm chứng. Mục tiêu là đưa RAG hiện tại từ prototype/demo lên production-grade theo yêu cầu của `REQ-F-RAG-001` đến `REQ-F-RAG-005`, `DOC-RAG-001` và `ADR-005`.

Tài liệu bao phủ chín nhóm nâng cấp:

1. embedding thật và tái lập chỉ mục;
2. typed `RetrievalContext`;
3. filter hiệu lực, audience, faculty và authorization trong SQL;
4. một canonical retriever;
5. reranker thực;
6. claim-level evidence gate;
7. citation metadata và resolver;
8. evaluation bằng PostgreSQL/pgvector thật;
9. cache, HNSW, connection pool và quyết định hạ tầng dựa trên benchmark.

Không nằm trong phạm vi mặc định:

- thay PostgreSQL bằng vector database khác trước khi có benchmark chứng minh cần thiết;
- đổi product requirement, security policy hoặc quality threshold để làm test pass;
- chạy provider trả phí hoặc dùng credential thật khi chưa có phê duyệt;
- migration phá hủy, reset hoặc xóa index/dữ liệu đang active.

## 2. Baseline đã được xác định

Audit hiện trạng ghi nhận các điểm sau:

| Khu vực | Hiện trạng | Hệ quả |
|---|---|---|
| Embedding | `services/worker/src/campus247_worker/ingestion/embed_fake.py` dùng hash/random-style vector; API vector path còn phụ thuộc đường fake | Không đo được semantic quality; ingestion và query không đại diện production |
| Filter | Runtime chủ yếu lọc `PUBLISHED`; chưa áp đầy đủ effective date, audience, faculty, tenant và authorization trong SQL | Có nguy cơ retrieve sai nguồn hoặc lộ candidate trước khi lọc |
| Retrieval | Có lexical/vector nhưng còn nhiều entry point và hard-coded `top_k`/`fusion_k` | Behavior không nhất quán, khó version và rollback |
| Rerank | Node hiện tại chủ yếu sort lại candidate score | Không phải reranker thực; không chứng minh được quality gain |
| Evidence | Có implementation mạnh trong `agent/grounding/evidence_gate.py` nhưng graph còn import gate đơn giản hơn | Có nguy cơ gate production không đủ claim-level |
| Chunking | Character window khoảng 1200/150, chưa theo tokenizer/semantic boundaries | Có thể cắt sai điều, bảng, locator và làm giảm citation support |
| Eval | Runner có `stub_memory`/fake provider; report pass không đại diện retrieval database thật | Không dùng được làm release evidence |
| Indexing | Ingestion/indexer chưa bảo đảm cùng embedding manifest giữa build và query | Có nguy cơ mismatch model, dimension hoặc corpus version |

Các nhận định trên là baseline; mọi micro-task phải kiểm chứng lại bằng test/evidence thay vì coi mô tả này là bằng chứng hoàn thành.

## 3. Nguyên tắc không được lấp liếm

Các điều kiện sau là release-blocking:

1. Không được instantiate fake embedding trong profile `dev`, `staging` hoặc `production`. Fake adapter chỉ được phép trong test.
2. Authorization, effective-date, publication state, audience và faculty filter phải nằm trong SQL trước ranking và `LIMIT`. Lọc sau retrieval ở Python không đạt.
3. Reranker phải gọi `RerankerPort` và approved adapter. Sort lại theo RRF hoặc điểm cũ không được gọi là rerank.
4. Eval production phải chạy canonical retriever trên PostgreSQL + pgvector và active-like index. `stub_memory`, `MockCandidate` hoặc candidate nhét sẵn đều bị reject.
5. Model không được tự sinh title, URL, page, document number hoặc citation metadata. Server phải resolve từ trusted source.
6. Mọi material claim phải map tới source version và locator trước khi stream/commit final answer.
7. Claim repair chỉ được xóa/giảm mức khẳng định/abstain; không được thêm source mới vào evidence bundle.
8. Cache hit vẫn phải kiểm tra authorization và effective state hiện tại.
9. Tuning chỉ được áp dụng sau khi có benchmark cùng dataset/index/profile và có report recall, latency, error rate, memory/connection impact.
10. `missing`, `not_verified`, `stub`, `fake`, `model mismatch` hoặc `index mismatch` không được quy đổi thành pass/zero.

## 4. DAG và thứ tự triển khai

```text
RAGUP-GOV-001
       │
       ├── RAGUP-DEPS-001
       │
       ├── RAGUP-EMBED-001..007 ───────────┐
       │                                    │
       └── RAGUP-CONTEXT-001..003           │
                    │                       │
             RAGUP-FILTER-001..005 ◄────────┘
                    │
             RAGUP-RETRIEVE-001..006
                    │
             RAGUP-RERANK-001..004
                    │
             RAGUP-EVID-001..004
                    │
             RAGUP-CITE-001..004
                    │
             RAGUP-EVAL-001..007
                    │
             RAGUP-OPS/CACHE/PERF
                    │
             RAGUP-RELEASE-001
```

### Wave execution

| Wave | Nội dung | Quy tắc song song |
|---|---|---|
| 0 | Governance, dependency/model approval | Tuần tự |
| 1 | Shared contracts, embedding manifest, context types | Có thể tách file; migration vẫn tuần tự |
| 2 | Embedding adapter/reindex và lexical/vector filters | Hai branch filter có thể song song nếu không trùng file |
| 3 | Canonical retriever và reranker | Graph/bootstrap wiring tuần tự |
| 4 | Evidence gate và citation resolver | UI citation có thể song song sau API contract |
| 5 | Gold dataset, real eval runner, metrics và gate | Data shard tối đa 4 task song song |
| 6 | Cache, benchmark, HNSW và pool tuning | Chỉ sau real eval |
| 7 | Production promotion gate | Tuần tự, không song song |

Không một task nào được bỏ qua chỉ vì metric trung bình tốt; subgroup, authorization, temporal và abstention vẫn phải pass.

## 5. Contract chung cho mọi micro-task

Mỗi task dưới đây khi materialize thành `tasks/items/*.yaml` phải giữ các trường:

- `task_id`: đúng ID được nêu;
- `objective`: chỉ một mục tiêu;
- `depends_on`: chỉ dependency đã hoàn tất;
- `inputs`: tài liệu/contract/code được đọc trước;
- `write_scope`: tối đa ba path/file scope cụ thể;
- `preconditions`: profile, migration, approval và fixture cần có;
- `steps`: thao tác nhỏ, có thể review;
- `acceptance_criteria`: kết quả observable, không dùng câu “improve” chung chung;
- `verification`: command và expected evidence;
- `stop_conditions`: mismatch, missing approval, dirty overlap, security failure;
- `recovery`: feature flag, pointer rollback hoặc revert patch, không destructive cleanup;
- `human_approval_required`: `true` cho provider/dependency/architecture/live test.

Default cho mọi task:

- estimate: 15–45 phút;
- tối đa 3 file/path trong write scope;
- không commit/push/deploy;
- deterministic fake cho unit test;
- network/live provider chỉ khi task ghi rõ approval;
- evidence phải có command, exit code, test output, diff và AC mapping.

---

## 6. Micro-task nhóm 0 — Governance và dependency

### `TASK-RAGUP-GOV-001` — Chốt production retrieval specification

- Phụ thuộc: không.
- Human approval: bắt buộc; đây là architecture/contract change.
- Write scope: `docs/04-architecture/adr/ADR-005_HYBRID_RETRIEVAL.md`, `docs/05-ai/RAG_PIPELINE.md`, `docs/04-architecture/contracts/DATA_DICTIONARY.md`.
- Thực hiện: chốt model/version/dimension, lexical/vector candidate counts, RRF constant, rerank counts, timeouts, fallback, filter semantics, citation/evidence contract và release thresholds.
- Acceptance:
  - ba tài liệu không còn mâu thuẫn;
  - mọi magic constant production được thay bằng versioned profile;
  - ADR có decision status `accepted` và approval evidence;
  - không còn placeholder production cho các trường bắt buộc.
- Verification: document control, link/traceability checker và review sign-off.
- Stop: requirement/architecture conflict chưa được giải quyết.

### `TASK-RAGUP-DEPS-001` — Phê duyệt dependency và model allowlist

- Phụ thuộc: `GOV-001`, `TASK-REPO-DEP-002`.
- Human approval: bắt buộc nếu thêm package, SDK, provider hoặc model.
- Write scope: `pyproject.toml`, `uv.lock`, dependency verification artifact.
- Acceptance:
  - package/version được pin;
  - có license, provenance, security review;
  - lockfile tái tạo được;
  - không có dependency ngoài allowlist;
  - model/provider ID được xác định rõ.
- Verification: dependency checker, lockfile check và import smoke test.
- Stop: phải dùng paid/live provider nhưng chưa có approval.

---

## 7. Micro-task nhóm 1 — Embedding và reindex

### `TASK-RAGUP-EMBED-001` — Canonical embedding contract

- Phụ thuộc: `GOV-001`.
- Write scope: shared embedding contract, contract tests và package path configuration.
- Thực hiện: định nghĩa `EmbeddingPort`, `embed_documents`, `embed_query`, model/version, dimension, normalization, batch limit, timeout và typed errors.
- Acceptance:
  - ingestion và query dùng cùng contract;
  - dimension/model mismatch bị reject;
  - `NaN`, `Infinity`, empty input và batch quá giới hạn có test;
  - contract không phụ thuộc vendor cụ thể.
- Verification: unit tests và import test từ API/worker boundary.

### `TASK-RAGUP-EMBED-002` — Production embedding adapter

- Phụ thuộc: `EMBED-001`, `DEPS-001`.
- Human approval: bắt buộc nếu adapter gọi external/paid service.
- Write scope: approved embedding adapter, settings/profile và adapter tests.
- Acceptance:
  - adapter trả vector đúng dimension/model version;
  - batch, timeout và bounded retry hoạt động;
  - log không chứa raw document/query hoặc credential;
  - telemetry có model/version/latency.
- Verification: deterministic adapter contract tests; live test chỉ trong approved environment.

### `TASK-RAGUP-EMBED-003` — Cô lập fake embedding vào test

- Phụ thuộc: `EMBED-001`.
- Write scope: fake adapter, environment guard và negative tests.
- Acceptance:
  - fake adapter chỉ import được dưới test profile;
  - startup `dev/staging/production` fail closed nếu chọn fake;
  - không còn production import từ `embed_fake.py`;
  - test không nhầm fake output là quality evidence.
- Verification: profile startup tests và import graph check.

### `TASK-RAGUP-EMBED-004` — Embedding/index manifest

- Phụ thuộc: `GOV-001`.
- Write scope: additive migration, manifest contract và migration tests.
- Trường bắt buộc: model, model version, dimension, index version, embedded timestamp, active pointer/manifest.
- Acceptance:
  - query không thể dùng vector khác model/dimension;
  - document version trace được tới index và profile;
  - migration không drop/truncate/overwrite active data.
- Verification: migration apply test, mismatch test và schema inspection.

### `TASK-RAGUP-EMBED-005` — Ingestion dùng embedding port

- Phụ thuộc: `EMBED-002`, `EMBED-004`.
- Write scope: ingestion/indexing adapter và ingestion tests.
- Acceptance:
  - chunk, tsvector, embedding và manifest lưu nhất quán;
  - partial failure không đánh dấu version ready;
  - retry idempotent, không duplicate chunk;
  - deterministic fake chỉ dùng test.
- Verification: integration test với test adapter và transaction failure test.

### `TASK-RAGUP-EMBED-006` — Query embedding cùng active manifest

- Phụ thuộc: `EMBED-002`, `EMBED-004`.
- Write scope: query embedding adapter, bootstrap/profile wiring và mismatch tests.
- Acceptance:
  - model/version/dimension query khớp active index;
  - mismatch fail closed;
  - trace ghi `embedding_model_version` và `index_version`.
- Verification: runtime startup/query tests và telemetry assertion.

### `TASK-RAGUP-EMBED-007` — Reindex song song và atomic activation

- Phụ thuộc: `EMBED-005`, `EMBED-006`.
- Write scope: reindex job, active-pointer service và reindex tests.
- Acceptance:
  - reindex có checkpoint/resume;
  - validate document/chunk count, dimension và checksum trước activation;
  - activation atomic;
  - rollback chỉ đổi active pointer;
  - index cũ không bị xóa.
- Verification: interrupted job test, activation race test và rollback test.

---

## 8. Micro-task nhóm 2 — Typed `RetrievalContext`

### `TASK-RAGUP-CONTEXT-001` — Domain retrieval types

- Phụ thuộc: `GOV-001`.
- Write scope: context/candidate/result contracts và contract tests.
- Phải có: `RetrievalQuery`, `RetrievalContext`, `AuthorizedScope`, `RetrievalCandidate`, `RetrievalResult`, `RetrievalDiagnostics`.
- Acceptance: context chứa tenant/campus, trusted actor, roles, faculty/program, audience, locale, effective time, simulation policy và trace ID.
- Verification: schema/type tests và serialization round-trip.

### `TASK-RAGUP-CONTEXT-002` — Trusted context factory

- Phụ thuộc: `CONTEXT-001`.
- Write scope: context factory, identity mapping và spoofing tests.
- Acceptance:
  - client không tự khai role, audience, faculty hoặc tenant;
  - thiếu/invalid identity fail closed;
  - request-controlled fields không trở thành authorized scope;
  - context có audit-safe trace ID.
- Verification: role spoofing, tenant crossing và missing identity tests.

### `TASK-RAGUP-CONTEXT-003` — Propagate context xuyên pipeline

- Phụ thuộc: `CONTEXT-002`.
- Write scope: graph/bootstrap/retrieval call chain và propagation tests.
- Acceptance:
  - lexical, vector, reranker, citation nhận cùng context;
  - không có production `dict` context tùy ý;
  - legacy wrapper chỉ delegate;
  - context không bị mất khi retry/degraded mode.
- Verification: end-to-end context identity assertion.

---

## 9. Micro-task nhóm 3 — SQL filters

### `TASK-RAGUP-FILTER-001` — Storage fields và indexes

- Phụ thuộc: `GOV-001`.
- Write scope: additive migration, schema contract và migration tests.
- Fields: publication/approval state, effective range, audience, faculty/program, tenant/campus, simulation marker và indexes.
- Acceptance: metadata uncertainty loại source khỏi production retrieval; withdrawn/superseded vẫn giữ audit nhưng excluded.
- Verification: migration apply/rollback-pointer test và index inspection.

### `TASK-RAGUP-FILTER-002` — Authorized filter compiler

- Phụ thuộc: `CONTEXT-002`, `FILTER-001`.
- Write scope: filter compiler và predicate tests.
- Acceptance:
  - parameterized SQL, không nối chuỗi;
  - lexical/vector semantics giống nhau;
  - empty scope không thành allow-all;
  - date boundary, role, audience, faculty, tenant có negative tests.
- Verification: property/unit tests trên mọi tổ hợp scope được phép.

### `TASK-RAGUP-FILTER-003` — Lexical filter trước rank/limit

- Phụ thuộc: `FILTER-002`.
- Write scope: lexical query và SQL integration tests.
- Acceptance:
  - predicate nằm trong SQL trước rank và `LIMIT`;
  - query plan dùng index phù hợp;
  - unauthorized/expired rows không xuất hiện candidate/diagnostic.
- Verification: PostgreSQL integration fixture, `EXPLAIN` evidence và leakage test.

### `TASK-RAGUP-FILTER-004` — Vector filter trước ANN limit

- Phụ thuộc: `FILTER-002`, `EMBED-006`.
- Write scope: vector query và pgvector integration tests.
- Acceptance:
  - predicate áp dụng trước ANN candidate limit;
  - không retrieve rộng rồi lọc Python;
  - model/index mismatch fail closed;
  - filtered recall được đo.
- Verification: pgvector fixture, `EXPLAIN` và unauthorized candidate test.

### `TASK-RAGUP-FILTER-005` — Cross-branch leakage suite

- Phụ thuộc: `FILTER-003`, `FILTER-004`.
- Write scope: shared security fixtures và cross-branch tests.
- Cases: draft, future, expired, withdrawn, faculty khác, audience khác, tenant khác, synthetic bị cấm và conflicting version.
- Acceptance: lexical và vector đều zero leakage; response không tiết lộ sự tồn tại của unauthorized source.
- Verification: full integration suite và redacted trace inspection.

---

## 10. Micro-task nhóm 4 — Canonical retriever

### `TASK-RAGUP-RETRIEVE-001` — Versioned retrieval profile

- Phụ thuộc: `GOV-001`.
- Write scope: profile schema, runtime loader và profile tests.
- Profile phải chứa lexical/vector k, RRF constant, rerank k, context budget, timeout, fallback, evidence threshold, embedding/index/reranker versions.
- Acceptance: thiếu field hoặc version mismatch làm startup/query fail closed; không còn hard-coded production constants.
- Verification: profile validation và compatibility tests.

### `TASK-RAGUP-RETRIEVE-002` — Canonical `HybridRetriever`

- Phụ thuộc: `FILTER-003`, `FILTER-004`, `RETRIEVE-001`.
- Write scope: canonical retriever, diagnostics contract và service tests.
- Acceptance:
  - lexical/vector chạy bounded/concurrent;
  - timeout từng branch;
  - RRF deterministic;
  - dedupe bằng stable chunk ID;
  - branch failure được ghi explicit;
  - hai branch fail không tạo grounded answer.
- Verification: unit, integration và branch-degradation tests.

### `TASK-RAGUP-RETRIEVE-003` — Exact identifier handling

- Phụ thuộc: `RETRIEVE-002`.
- Write scope: query preparation/exact boost và tests.
- Hỗ trợ mã môn, số văn bản, section/page, form ID và ngày.
- Acceptance: exact boost versioned, giữ phủ định/time/audience constraint và không vượt filter authorization.
- Verification: exact match, no-diacritic, typo và false-positive tests.

### `TASK-RAGUP-RETRIEVE-004` — Context assembler

- Phụ thuộc: `RETRIEVE-002`.
- Write scope: context assembler và snapshot tests.
- Acceptance:
  - top evidence theo token budget;
  - dedupe/diversity;
  - stable IDs và locator giữ nguyên;
  - table/header/section metadata không bị cắt;
  - không vượt route budget.
- Verification: tokenizer budget, duplicate và locator-preservation tests.

### `TASK-RAGUP-RETRIEVE-005` — Wire graph/bootstrap về canonical service

- Phụ thuộc: `RETRIEVE-003`, `RETRIEVE-004`.
- Write scope: graph, bootstrap và wiring/integration tests.
- Acceptance:
  - mọi chat path gọi một retriever;
  - legacy path chỉ delegate;
  - không còn duplicate RRF/filter implementation;
  - profile quyết định k và timeout.
- Verification: call graph inspection và end-to-end retrieval test.

### `TASK-RAGUP-RETRIEVE-006` — Failure/degradation policy

- Phụ thuộc: `RETRIEVE-005`.
- Write scope: degradation policy, typed errors và failure tests.
- Cases: lexical timeout, vector timeout, invalid branch output, database unavailable, both branches fail.
- Acceptance: fallback chỉ khi profile cho phép; mỗi degraded answer có reason code; unsafe fallback abstain.
- Verification: fault-injection integration suite.

---

## 11. Micro-task nhóm 5 — Reranker thực

### `TASK-RAGUP-RERANK-001` — Reranker port và validator

- Phụ thuộc: `CONTEXT-001`.
- Write scope: reranker contract, ordered-ID validator và tests.
- Acceptance: input tối đa profile limit; output chỉ gồm input IDs, không duplicate, score hữu hạn, có model/version/latency; invalid output bị reject.
- Verification: malformed/foreign-ID/duplicate/NaN tests.

### `TASK-RAGUP-RERANK-002` — Approved reranker adapter

- Phụ thuộc: `RERANK-001`, `DEPS-001`.
- Human approval: bắt buộc nếu dùng external/paid model.
- Write scope: adapter, settings và adapter tests.
- Acceptance: adapter thật sự gọi approved model; timeout/retry bounded; không thay chunk text; fake chỉ ở test; log privacy-safe.
- Verification: contract tests; live test chỉ ở approved environment.

### `TASK-RAGUP-RERANK-003` — Rerank top-20 thành top-8

- Phụ thuộc: `RETRIEVE-002`, `RERANK-002`.
- Write scope: retriever/reranker integration và tests.
- Acceptance:
  - rerank sau RRF;
  - tối đa 20 input và 8 context output theo profile;
  - fallback RRF có degraded flag;
  - không rerank candidate chưa qua authorization/effective filters.
- Verification: call-count, limit, fallback và security tests.

### `TASK-RAGUP-RERANK-004` — Reranker ablation/quality suite

- Phụ thuộc: `RERANK-003`.
- Write scope: eval cases và reranker comparison tests.
- Cases: Vietnamese có dấu/không dấu, paraphrase, exact IDs, hard negatives, stale near-match.
- Acceptance: chỉ enable mặc định nếu quality tăng và không subgroup nào dưới threshold.
- Verification: same-index ablation report.

---

## 12. Micro-task nhóm 6 — Claim-level evidence gate

### `TASK-RAGUP-EVID-001` — Structured grounded-answer parser

- Phụ thuộc: `RETRIEVE-004`, `TASK-AGENT-EVIDENCE-002`.
- Write scope: grounded answer schema/parser và parser tests.
- Acceptance: tách answer, material claims, citation IDs, claim type và abstention reason; reject malformed/ambiguous/missing citation mapping.
- Verification: malformed JSON, unknown ID, duplicate claim và unsupported claim tests.

### `TASK-RAGUP-EVID-002` — Wire graph vào canonical evidence gate

- Phụ thuộc: `EVID-001`, `TASK-AGENT-EVIDENCE-002`.
- Write scope: graph wiring, compatibility wrapper và integration tests.
- Acceptance:
  - graph dùng `agent/grounding/evidence_gate.py`;
  - không còn hai gate độc lập;
  - gate chạy trước final stream commit;
  - pass/repair/abstain là deterministic decision.
- Verification: graph transition và stream boundary tests.

### `TASK-RAGUP-EVID-003` — Bounded evidence repair

- Phụ thuộc: `EVID-002`.
- Write scope: repair policy và tests.
- Acceptance:
  - tối đa một repair;
  - chỉ remove/qualify/clarify/abstain;
  - không thêm source/citation mới;
  - lần hai fail thì abstain.
- Verification: repair mutation guard và two-failure tests.

### `TASK-RAGUP-EVID-004` — Adversarial evidence integration

- Phụ thuộc: `EVID-003`, `TASK-AGENT-INJECT-001`, `TASK-AGENT-STREAM-001`.
- Write scope: adversarial fixtures và integration tests.
- Cases: stale, unauthorized, conflict, prompt injection trong document, synthetic confusion, sai locator, PII và stream-then-fail.
- Acceptance: unsupported material claim không được commit hoặc render như grounded answer.
- Verification: full evidence/security suite.

---

## 13. Micro-task nhóm 7 — Citation metadata và resolver

### `TASK-RAGUP-CITE-001` — Complete candidate provenance

- Phụ thuộc: `FILTER-005`, `EMBED-004`.
- Write scope: candidate/provenance contract, mapper và tests.
- Metadata bắt buộc: source ID, document version, chunk ID, title, issuer, number, dates, section/page, canonical URI, simulation marker, quote hash.
- Acceptance: missing required metadata làm candidate/citation invalid; immutable IDs giữ xuyên pipeline.
- Verification: metadata completeness and immutability tests.

### `TASK-RAGUP-CITE-002` — Server-side citation resolver

- Phụ thuộc: `CITE-001`.
- Write scope: resolver, citation bundle và resolver tests.
- Acceptance:
  - model chỉ tham chiếu candidate ID;
  - server resolve từ trusted storage;
  - missing metadata fail closed;
  - quote span hash khớp chunk;
  - source version/effective state được kiểm tra lại.
- Verification: missing metadata, wrong span, stale source và unauthorized resolver tests.

### `TASK-RAGUP-CITE-003` — Public API citation contract

- Phụ thuộc: `CITE-002`.
- Write scope: API schema, presentation mapper và contract tests.
- Acceptance: response chỉ chứa server-resolved citation; model-provided URL/title/page bị bỏ hoặc reject; claim-citation mapping machine-readable.
- Verification: API contract and forged-metadata tests.

### `TASK-RAGUP-CITE-004` — Verified citation UI states

- Phụ thuộc: `CITE-003`, citation UI task hiện có.
- Write scope: citation rendering component/tests.
- Acceptance: UI phân biệt verified, unavailable, stale/conflict và simulation; không render citation giả.
- Verification: component tests, accessibility test và screenshot states.

---

## 14. Micro-task nhóm 8 — Real evaluation

### `TASK-RAGUP-EVAL-001` — Gold dataset schema và validator

- Phụ thuộc: `GOV-001`.
- Write scope: gold schema, validator và leakage tests.
- Mỗi case phải có query, locale/domain, authorized context, relevant version/chunk, citation expectation, negative labels, split và provenance.
- Acceptance: validator bắt duplicate/paraphrase leakage, missing source/version, missing auth context và unresolved gold citation.
- Verification: invalid-fixture suite.

### `TASK-RAGUP-DATA-001` đến `TASK-RAGUP-DATA-020` — Gold data shards

- Phụ thuộc: `EVAL-001`.
- Mỗi task tạo hoặc review đúng 25 case trong một shard riêng; write scope không overlap.
- Phân bổ:
  - `DATA-001..012`: development, cases 0001–0300;
  - `DATA-013..016`: validation, cases 0301–0400;
  - `DATA-017..020`: sealed test, cases 0401–0500.
- Mỗi shard phải có quota cho: tiếng Việt có/không dấu, exact identifier, paraphrase, multi-document, temporal, audience/faculty authorization, unanswerable, conflict/stale, injection và hard negative.
- Acceptance: gold chunk tồn tại trong trusted index; answer/citation expectation review được; sealed cases không đi vào implementation fixture.
- Verification: schema validator, quota validator, duplicate/leakage detector và reviewer evidence.
- Parallelism: tối đa 4 shard task đồng thời.

### `TASK-RAGUP-EVAL-002` — PostgreSQL/pgvector evaluation runner

- Phụ thuộc: `RETRIEVE-005`, `EVAL-001`.
- Write scope: real runner, database fixture config và runner tests.
- Acceptance:
  - runner gọi canonical retriever;
  - dùng PostgreSQL/pgvector thật;
  - ghi git/index/profile/model/dataset hash;
  - tự fail với `stub_memory`, fake provider hoặc pre-supplied candidates.
- Verification: run against isolated fixture database và negative runner tests.

### `TASK-RAGUP-EVAL-003` — Retrieval/grounding metrics

- Phụ thuộc: `EVAL-002`.
- Write scope: metrics aggregator, report schema và metric tests.
- Metrics: Recall@5/@10, MRR, nDCG, exact-ID success, citation precision/recall, claim support, abstention precision/recall, latency p50/p95/p99, subgroup CIs.
- Acceptance: missing metric là failure; report giữ query-level failed IDs.
- Verification: hand-calculated fixture và aggregation tests.

### `TASK-RAGUP-EVAL-004` — Controlled ablation

- Phụ thuộc: `EVAL-003`, `RERANK-004`.
- Write scope: ablation profile/runner và report tests.
- So sánh lexical-only, vector-only, hybrid RRF, hybrid+rereanker trên cùng dataset/index.
- Acceptance: run metadata giống nhau ngoài biến đang thử; report tách quality, latency và cost.
- Verification: reproducibility check và ablation artifact hash.

### `TASK-RAGUP-EVAL-005` — Approved live-model evaluation

- Phụ thuộc: `EVAL-004`, toàn bộ data shards.
- Human approval: bắt buộc cho network, credential, paid provider/live model.
- Acceptance: ghi model IDs/versions, timestamp, repeats, token/cost, errors/timeouts; không thay live run bằng fake provider.
- Verification: approved environment run và immutable report.

### `TASK-RAGUP-EVAL-006` — Production quality gate

- Phụ thuộc: `EVAL-005`.
- Write scope: release gate, threshold config và gate tests.
- Gate fail khi stub/fake, thiếu shard/subgroup, mismatch index/model, metric dưới threshold hoặc evidence `not_verified`.
- Verification: negative gate fixtures cho từng failure reason.

### `TASK-RAGUP-EVAL-007` — CI/release integration

- Phụ thuộc: `EVAL-006`, `TASK-EVAL-GATE-001`, `TASK-OPS-RELEASE-002`.
- Write scope: CI invocation, artifact manifest và CI tests.
- Acceptance: immutable report được lưu; promotion đọc đúng report/hash; không bypass bằng sửa expected output.
- Verification: clean CI run và tampered-artifact test.

---

## 15. Micro-task nhóm 9 — Cache, index tuning và vận hành

### `TASK-RAGUP-OPS-001` — Retrieval observability schema

- Phụ thuộc: `RETRIEVE-001`.
- Write scope: additive retrieval-run/candidate schema và observability tests.
- Fields: branch result, candidate rank, RRF/rerank score, profile/index/model versions, degraded reason và latency.
- Acceptance: trace đủ debug nhưng không chứa raw private query/secret.
- Verification: schema and privacy tests.

### `TASK-RAGUP-OPS-002` — Privacy-safe trace writer

- Phụ thuộc: `OPS-001`, trace task hiện có.
- Write scope: trace writer, redaction policy và tests.
- Acceptance: hash/redact query, giới hạn candidate metadata, có correlation ID, không log token/hidden prompt/PII không cần thiết.
- Verification: redaction and forbidden-field tests.

### `TASK-RAGUP-CACHE-001` — Scope-safe cache key

- Phụ thuộc: `CONTEXT-002`, `RETRIEVE-005`.
- Write scope: cache key builder và tests.
- Key phải gồm query hash, tenant/campus, authorization scope hash, audience/faculty, locale, effective bucket, profile, index/model versions.
- Acceptance: cùng query khác scope không share; cache hit vẫn authorization-check.
- Verification: cross-scope cache leakage tests.

### `TASK-RAGUP-CACHE-002` — Invalidation

- Phụ thuộc: `CACHE-001`, `EMBED-007`.
- Write scope: invalidation hooks và race tests.
- Invalidate khi publish/withdraw/effective change/scope change/index/profile/model change.
- Acceptance: không trả answer/citation từ version cũ sau invalidation event.
- Verification: event ordering, race và stale-cache tests.

### `TASK-RAGUP-PERF-001` — Real retrieval benchmark

- Phụ thuộc: `EVAL-002`, `RERANK-003`.
- Write scope: benchmark runner, workload manifest và report schema.
- Workload: cold/warm cache, concurrency, lexical/vector/hybrid/rerank, authorized filters, realistic corpus size.
- Acceptance: report p50/p95/p99, throughput, timeout, DB CPU/IO, memory và pool usage; không dùng MockCandidate.
- Verification: repeatable benchmark artifact.

### `TASK-RAGUP-PERF-002` — HNSW tuning experiment

- Phụ thuộc: `PERF-001`.
- Write scope: experiment profile và report.
- Thử có kiểm soát `m`, `ef_construction`, `ef_search`, iterative scan/filter settings.
- Acceptance: recall không dưới threshold, p95/p99 cải thiện hoặc trade-off được approved, memory/build time trong budget.
- Verification: same-corpus comparison report.

### `TASK-RAGUP-PERF-003` — Pool saturation và degradation test

- Phụ thuộc: `PERF-001`.
- Write scope: load profile và pool/fault tests.
- Cases: pool exhaustion, long vector query, parallel branch cancellation, connection leak, OLTP contention, backpressure.
- Acceptance: không leak connection; timeout/cancel giải phóng resource; SLO OLTP không bị phá.
- Verification: load report và pool metrics.

### `TASK-RAGUP-PERF-004` — Infrastructure decision gate

- Phụ thuộc: `PERF-002`, `PERF-003`.
- Write scope: decision record, không tự động migration.
- Kết quả hợp lệ: giữ PostgreSQL, thêm read replica, tách retrieval database hoặc đánh giá vector DB khác.
- Acceptance: chỉ đề xuất thay DB nếu evidence cho thấy PostgreSQL không đạt SLO sau tuning; ghi rõ cost/data-boundary/rollback.
- Verification: architecture review.

### `TASK-RAGUP-RELEASE-001` — Final promotion gate

- Phụ thuộc: toàn bộ task bắt buộc ở nhóm 0–9.
- Human approval: bắt buộc.
- Write scope: release manifest, promotion gate và rollback runbook.
- Manifest phải khóa: Git revision, dataset hash, index version, embedding/reranker/model versions, profile, migration version, eval report, approvals và rollback pointer.
- Acceptance:
  - không promote khi có `blocked`, `failed`, `not_verified`, fake/stub hoặc missing evidence;
  - active pointer rollback được;
  - mọi artifact reproducible và traceable tới requirements.
- Verification: full release gate, tampered-manifest test và rollback rehearsal.

## 16. Acceptance gate cấp hệ thống

Chỉ coi toàn bộ nâng cấp hoàn tất khi đồng thời đạt:

| Gate | Điều kiện tối thiểu |
|---|---|
| Source validity | Chỉ published, approved, applicable và currently effective source là candidate production |
| Authorization | Expired, withdrawn, wrong audience/faculty/tenant và unauthorized candidate leakage bằng 0 |
| Retrieval | Lexical + semantic branch được trace; fusion deterministic; failure explicit |
| Rerank | Adapter thật được gọi; top-k và fallback versioned |
| Grounding | 100% material claim có citation ID hợp lệ; unsupported claim bị remove hoặc abstain |
| Citation | Metadata server-resolved, đúng version/locator/hash; không nhận forged model metadata |
| Eval | Real PostgreSQL/pgvector run, không stub/fake/pre-supplied candidate; đủ subgroup/sealed split |
| Quality | Theo threshold đã accepted trong `GOV-001`; không dùng average để che subgroup fail |
| Performance | p95/p99, pool, memory và throughput nằm trong approved SLO/budget |
| Release | Manifest/hash/approval/rollback đầy đủ và reproducible |

## 17. Recovery và stop conditions

Dừng task ngay khi:

- source requirement/architecture/contract mâu thuẫn;
- file đích có dirty change của công việc khác;
- cần thêm dependency/provider/credential nhưng chưa được phê duyệt;
- model/index/profile mismatch;
- SQL filter không chứng minh được chạy trước `LIMIT`;
- eval runner phát hiện stub/fake/mock candidate;
- citation metadata thiếu hoặc evidence gate không chạy trước stream commit;
- chỉ có metric trung bình mà thiếu subgroup/negative/security evidence.

Recovery hợp lệ:

- giữ active index/profile/version cũ;
- tắt feature bằng approved profile/flag;
- rollback active pointer;
- revert patch nhỏ, không reset hoặc clean working tree;
- ghi incident/degraded reason và giữ audit history.

Không được dùng cleanup, reset, drop, truncate hoặc xóa artifact để làm cho task pass.

## 18. Traceability

Backlog này trace tới:

- `REQ-F-RAG-001` — published, applicable, currently effective retrieval;
- `REQ-F-RAG-002` — lexical + semantic retrieval trước reranking;
- `REQ-F-RAG-003` — material claim tới source version/locator/provenance;
- `REQ-F-RAG-004` — citation metadata đầy đủ;
- `REQ-F-RAG-005` — insufficient/expired/conflicting evidence phải abstain;
- `DOC-RAG-001` — ingestion, retrieval, rerank, citation và evidence contract;
- `ADR-005` — hybrid PostgreSQL FTS + pgvector + deterministic fusion + approved rerank + evidence gate;
- `TASK-AGENT-EVIDENCE-002`, `TASK-AGENT-INJECT-001`, `TASK-AGENT-STREAM-001`, `TASK-EVAL-GATE-001`, `TASK-OPS-RELEASE-002` — các dependency đã có trong repository.

Mỗi task khi đưa vào catalog phải bổ sung binding cụ thể tới acceptance criteria tương ứng trong `tasks/requirement-acceptance-bindings.yaml`; không được coi tài liệu này là thay thế cho requirement hoặc architecture approval.
