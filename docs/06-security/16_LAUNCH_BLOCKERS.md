---
document_id: "DOC-SEC-010"
version: "0.1.0"
status: "draft"
owner: "Release Governance Lead"
approvers: ["Product Owner", "Security Architect", "Privacy/Legal Owner", "Operations Owner", "University Sponsor"]
last_updated: "2026-09-22"
---

# Launch blocker catalog

## 1. Mục đích và quyết định hiện tại

Catalog này xác định điều kiện fail-closed cho ba mức phát hành khác nhau. Việc có code, tài liệu hoặc test riêng lẻ không tự đóng blocker. Một blocker chỉ `closed` khi owner chỉ định đã chấp nhận evidence có thể tái lập cho đúng release, environment, capability và data mode.

**Trạng thái tại thời điểm viết:** tài liệu là `draft`; mọi blocker có `initial_status: open`. Không được suy diễn production-ready hoặc legal compliance từ catalog này.

```yaml
launch_decision_current:
  simulated_demo: "not_yet_approved"
  pilot: "blocked"
  production: "blocked"
  real_personal_data: "prohibited_pending_approval"
  production_deployment_by_agent: "prohibited"
```

## 2. Định nghĩa stage

### `simulated_demo`

- Audience nội bộ/được kiểm soát, không phải dịch vụ chính thức.
- Chỉ synthetic identities/content; không real student/staff directory, PII, credential hoặc production copy.
- Banner `HUCE Demo` và giới hạn mô phỏng luôn hiển thị.
- Mock auth được phép chỉ trong environment đánh dấu synthetic demo.
- Fake LLM/provider là mặc định. Gọi DeepSeek thật cần paid-service approval riêng, synthetic-only egress và vendor gate tương ứng.
- Không hứa human response, emergency outcome, SLA hoặc quyết định nghiệp vụ thật.

### `pilot`

- Bất kỳ thử nghiệm nào có người dùng thật, university identity thật, institutional integration thật, dữ liệu thật, hoặc được dùng để hỗ trợ quy trình thật.
- Dù business content là synthetic, identity, access log, device/network metadata và feedback của người dùng thật có thể là dữ liệu cá nhân; privacy/security gates áp dụng.
- Pilot phải có phạm vi, thời hạn, cohort, rollback, support và exit criteria được phê duyệt.

### `production`

- Dịch vụ chính thức hoặc được người dùng/nhà trường dựa vào cho hoạt động thực tế.
- Tất cả blockers applicable phải `closed`; exception chỉ hợp lệ theo phần 5.
- Chỉ release owner/human-approved pipeline được deploy. Agent không có quyền tự deploy.

## 3. Trạng thái, applicability và evidence

Allowed blocker status:

```text
open -> evidence_pending -> closed
  \-> exception_requested -> waived_time_bound
  \-> not_applicable_for_release
closed/waived/not_applicable -> reopened (change, expiry, incident or failed verification)
```

Applicability:

- `BLOCK`: blocker MUST `closed` hoặc có waiver hợp lệ trước launch.
- `CONDITIONAL`: capability/flow phải bị disable bằng configuration + test nếu blocker chưa đóng; enablement làm item thành `BLOCK`.
- `NOT_APPLICABLE`: stage không có capability/flow; cần evidence chứng minh absence, không phải lời khai.

Evidence MUST có release ID/source revision, environment, data mode, command/review result, owner, independent verifier khi high risk, timestamp, expiry và immutable artifact reference. `planned`, `documented`, `implemented` hoặc screenshot đơn lẻ không đồng nghĩa `verified`.

## 4. Security and operational launch blockers

| ID | Blocker / exit condition | Demo | Pilot | Production | Owner | Minimum closure evidence | Fail-closed behavior | Waiver rule | Initial status |
|---|---|---:|---:|---:|---|---|---|---|---|
| `SEC-LAUNCH-001` | Release scope, accountable Product Owner, release owner, capability list, data mode và success/abort criteria MUST được ký. | BLOCK | BLOCK | BLOCK | Product Owner | Signed release charter; source/config digest; scope diff; `OQ-001` closed for pilot/production. | Không phát hành; environment giữ private. | Demo có thể dùng named internal demo owner; pilot/production không được bỏ accountable owner. | open |
| `SEC-LAUNCH-002` | Environment/data-mode guard MUST chứng minh synthetic-only ở demo và không cho mock auth/synthetic toggle sai stage. | BLOCK | BLOCK | BLOCK | Security + Platform Owner | Startup/config negative tests; dataset manifests; no-prod-copy/DLP scan; production mock-auth hard fail. | Process không start hoặc data ingress bị deny. | NOT_WAIVABLE cho real-data boundary và production mock auth. | open |
| `SEC-LAUNCH-003` | Authentication MUST phù hợp stage: isolated mock demo; Entra production contract, MFA/Conditional Access, revocation và break-glass drill cho pilot/production. | BLOCK | BLOCK | BLOCK | Identity Owner | Auth threat tests; issuer/audience/nonce/PKCE evidence; claim mapping; revocation ≤ target; `OQ-004` closure. | Deny login/privileged action; maintenance mode, không fallback production sang mock. | NOT_WAIVABLE cho production; pilot alternative IdP cần architecture/security approval, không phải silent waiver. | open |
| `SEC-LAUNCH-004` | Deny-default RBAC+ABAC+object/field/queue authorization MUST pass positive và negative BOLA/BFLA tests. | BLOCK | BLOCK | BLOCK | Security/API Owner | Route/tool matrix; cross-user/cross-unit canary; hidden-field and permission-loss tests. | Return normalized 401/403; không fetch/render protected data. | NOT_WAIVABLE cho unauthorized access. | open |
| `SEC-LAUNCH-005` | Network và provider egress MUST chỉ tới exact approved destinations; C2/C3/secret egress bị chặn. | CONDITIONAL | BLOCK | BLOCK | Security/Platform Owner | IaC/network policy tests; DNS/redirect deny; DLP/provider-spy corpus; transfer/vendor record binding. | Deny outbound call; use deterministic path/abstain/safe mode. | NOT_WAIVABLE cho secret/PII leakage; demo fake provider makes vendor egress path NOT_APPLICABLE. | open |
| `SEC-LAUNCH-006` | Mọi write MUST có authorization, authoritative preview, actor/payload-bound confirmation, expiry/revalidation, idempotency, reconciliation và audit. | BLOCK | BLOCK | BLOCK | API/Product Owner | Tamper, replay, duplicate, disconnect-after-confirm, stale-preview and audit tests. | Disable write; never render optimistic success; unknown result reconciles/HITL. | NOT_WAIVABLE cho unconfirmed or unauthorized write. | open |
| `SEC-LAUNCH-007` | AI/RAG/tool path MUST pass grounding, citation, abstention, prompt-injection, corpus authorization, schema và no-side-effect tests. | BLOCK | BLOCK | BLOCK | AI Quality + Security Owner | Affected eval suites; red-team results; source/version manifest; tool policy spy; regression gate output. | Disable affected model/tool; deterministic search/form or HITL remains. | High/Critical failures NOT_WAIVABLE; bounded Medium may use `SEC-CTRL-026`. | open |
| `SEC-LAUNCH-008` | Sensitive/emergency/HITL experience MUST use approved wording, routing, contact, staffed hours, privacy minimization và drill. | BLOCK | BLOCK | BLOCK | Student Support Lead | Demo placeholder test; pilot/prod contact config approval; safety eval; handover and after-hours drill; `OQ-003`. | Demo shows no-official-contact placeholder; pilot/production safety surface disabled and launch blocked. | NOT_WAIVABLE where surface implies real emergency support. | open |
| `SEC-LAUNCH-009` | Structured audit, privacy-safe telemetry, detection and alert routing MUST be complete; unknown telemetry MUST not be success. | BLOCK | BLOCK | BLOCK | SecOps/Operations Owner | Event schema/DLP tests; correlation; append-only/IAM test; alarm delivery/acknowledgement; dashboard unknown-state tests. | High-risk capability disabled; missing security audit blocks launch. | Audit integrity/secret redaction NOT_WAIVABLE; noncritical dashboard gap may be time-bound with alternate monitoring. | open |
| `SEC-LAUNCH-010` | Incident response MUST have named roles, severity model, contacts, containment/communications/forensics/notification assessment and tested runbooks. | BLOCK | BLOCK | BLOCK | Incident Commander | Tabletop for auth breach, PII/provider leak and AI unsafe action; contact test; evidence vault; post-exercise actions. | Keep environment private or disable affected capability; invoke incident process if exposure occurred. | Pilot/production cannot waive accountable incident owner; minor drill action may be time-bound. | open |
| `SEC-LAUNCH-011` | Backup, restore, deletion replay, degraded mode and rollback MUST be tested to stage-appropriate targets. | CONDITIONAL | BLOCK | BLOCK | Operations/Data Owner | Restore drill with checksums; RPO/RTO measurement labeled verified/not verified; rollback and deletion reconciliation. | Read-only/safe mode; no unverified recovery claim. | Demo ephemeral environment may be NOT_APPLICABLE with rebuild proof; production critical stores NOT_WAIVABLE. | open |
| `SEC-LAUNCH-012` | Supply chain and application security gates MUST pass: pinning, secret/SAST/SCA/IaC/container scans, SBOM, provenance and independent review. | BLOCK | BLOCK | BLOCK | Engineering Security Lead | CI evidence bundle, artifact digest, SBOM, review, vulnerability triage; independent penetration review for production. | Build/promotion stops; vulnerable release not deployed. | Critical/High follows `SEC-CTRL-027`; Medium/Low only time-bound under `SEC-CTRL-026`. | open |
| `SEC-LAUNCH-013` | Operational owners, staffed schedule/on-call, runbooks, escalation, support channel and service-status ownership MUST be assigned and exercised. | BLOCK | BLOCK | BLOCK | Operations Owner | RACI/on-call record; runbook drill; escalation test; approved public copy. | Unowned capability disabled; demo labels `UNASSIGNED`; no fake notification. | Pilot/production critical queue and incident roles NOT_WAIVABLE. | open |
| `SEC-LAUNCH-014` | Server-side rate/token/tool/time/cost budgets, quota alert, circuit breaker và finance kill switch MUST be approved. | CONDITIONAL | BLOCK | BLOCK | Product/Finance + Platform Owner | Load/limit tests; budget record; alarm/kill-switch drill; `OQ-008`. | Paid/provider-heavy capability disabled at hard limit; no unbounded retry. | Live paid demo requires explicit approval; pilot/prod hard cap NOT_WAIVABLE. | open |
| `SEC-LAUNCH-015` | Mỗi enabled SIS/LMS/ticket/room integration MUST có owner, sandbox/contract, schema, auth, timeout/idempotency và degraded behavior. | CONDITIONAL | CONDITIONAL | BLOCK | Integration Owner | `OQ-007` closure per integration; contract tests; sandbox limit; credential/IAM and failure drill. | Disable unapproved integration; synthetic adapter only; never fabricate authoritative data. | NOT_APPLICABLE only when capability is visibly disabled; no fake production result. | open |
| `SEC-LAUNCH-016` | Release evidence, approvals, config/model/source versions, migration, smoke checks, rollback and post-release verification MUST be bound to immutable release ID. | BLOCK | BLOCK | BLOCK | Release Owner | Signed evidence manifest; artifact/config digest; gate outputs; rollback decision; post-release checklist. | Promotion/deploy stops; drift triggers rollback/safe mode. | Missing critical evidence NOT_WAIVABLE; production deployment remains human-only. | open |

Primary security-control mapping:

| Launch blocker | Required controls |
|---|---|
| `SEC-LAUNCH-001` | `SEC-CTRL-001`, `SEC-CTRL-024`, `SEC-SDLC-001` |
| `SEC-LAUNCH-002` | `SEC-CTRL-002`, `SEC-CTRL-006`, `SEC-SDLC-006`, `PRIV-DATA-001` |
| `SEC-LAUNCH-003` | `SEC-CTRL-002`, `SEC-CTRL-004`, `SEC-AUTHN-001` đến `SEC-AUTHN-012` |
| `SEC-LAUNCH-004` | `SEC-CTRL-003`, `SEC-CTRL-023` |
| `SEC-LAUNCH-005` | `SEC-CTRL-005`, `SEC-CTRL-016`, `PRIV-FLOW-016`, `PRIV-FLOW-017` |
| `SEC-LAUNCH-006` | `SEC-CTRL-008`, `SEC-CTRL-018` |
| `SEC-LAUNCH-007` | `SEC-CTRL-006`, `SEC-CTRL-007`, `SEC-CTRL-012`, `SEC-CTRL-013`, `SEC-CTRL-014`, `SEC-CTRL-023`, `SEC-SDLC-005` |
| `SEC-LAUNCH-008` | `SEC-CTRL-025`, `PRIV-DPIA-007`, `PRIV-DPIA-016` |
| `SEC-LAUNCH-009` | `SEC-CTRL-018`, `SEC-CTRL-021`, `PRIV-FLOW-008`, `PRIV-FLOW-014` |
| `SEC-LAUNCH-010` | `SEC-CTRL-021`, `SEC-IR-*`, `PRIV-IR-*` |
| `SEC-LAUNCH-011` | `SEC-CTRL-015`, `SEC-CTRL-020`, `PRIV-DPIA-005` |
| `SEC-LAUNCH-012` | `SEC-CTRL-019`, `SEC-CTRL-023`, `SEC-CTRL-024`, `SEC-SDLC-002` đến `SEC-SDLC-007` |
| `SEC-LAUNCH-013` | `SEC-CTRL-021`, `SEC-CTRL-025` |
| `SEC-LAUNCH-014` | `SEC-CTRL-017`, `SEC-CTRL-018` |
| `SEC-LAUNCH-015` | `SEC-CTRL-001`, `SEC-CTRL-003`, `SEC-CTRL-005`, `SEC-CTRL-006`, `SEC-CTRL-008` |
| `SEC-LAUNCH-016` | `SEC-CTRL-024`, `SEC-CTRL-026` đến `SEC-CTRL-030`, `SEC-SDLC-007`, `SEC-SDLC-008` |

## 5. Privacy, legal and data launch blockers

| ID | Blocker / exit condition | Demo | Pilot | Production | Owner | Minimum closure evidence | Fail-closed behavior | Waiver rule | Initial status |
|---|---|---:|---:|---:|---|---|---|---|---|
| `PRIV-LAUNCH-001` | Data ownership, controller/processor roles, processing inventory, purpose và approved recipients MUST be named. | BLOCK | BLOCK | BLOCK | Data Owner + Privacy/Legal Owner | Synthetic data steward for demo; signed `PRIV-FLOW-*` inventory and `OQ-002` closure for real use. | Unknown fields treated C3; real-data collection/transfer disabled. | Legal/data accountability cannot be waived by engineering. | open |
| `PRIV-LAUNCH-002` | Demo synthetic data MUST have generator seed/version, provenance, no-real-person assertion, classification, allowed environments và manual sample review. | BLOCK | BLOCK | CONDITIONAL | Data Owner | Dataset manifests; deterministic regeneration; PII/secret scan; no production-copy proof. | Dataset rejected; environment receives no seed data. | NOT_WAIVABLE for any stage claiming synthetic-only. | open |
| `PRIV-LAUNCH-003` | Real-user processing MUST have approved purpose, lawful condition, privacy notice/consent or other basis, rights information and versioned evidence. | NOT_APPLICABLE | BLOCK | BLOCK | Privacy/Legal Owner | Legal memorandum; notice version; consent/exception design and negative tests; processing record. | Do not onboard real users or collect their telemetry/content. | LEGAL_DETERMINATION_REQUIRED; no technical waiver. | open |
| `PRIV-LAUNCH-004` | DPIA and risk treatment MUST cover actual people, fields, purposes, vendors, locations, retention, automated behavior and vulnerable groups. | BLOCK | BLOCK | BLOCK | Privacy Owner + University Sponsor | Simulation control review for demo; completed DPIA, residual-risk approval and review date for pilot/prod. | Affected processing disabled; High/Critical residual risk not silently accepted. | `PRIV-DPIA-019`; legal permissibility required. | open |
| `PRIV-LAUNCH-005` | Vendor due diligence, DPA, security assurance, subprocessor register, incident/rights/deletion terms and exit plan MUST be approved. | CONDITIONAL | BLOCK | BLOCK | Vendor + Privacy Owner | `PRIV-VEND-001..012` evidence per DeepSeek/AWS/Entra scope. | No credential/route or real-data enablement; fake/local adapter used. | No real-data waiver for unknown contract/subprocessor/data-use terms. | open |
| `PRIV-LAUNCH-006` | Every cross-border or external transfer MUST have current scope-bound legal, contractual and technical approval. | CONDITIONAL | BLOCK | BLOCK | Privacy/Legal + Security Owner | `PRIV-XFER-001..010` records; filing/assessment evidence where applicable; runtime deny tests; `OQ-005`. | Egress deny; deterministic/local fallback. | LEGAL_DETERMINATION_REQUIRED; C2/C3/secret-to-LLM prohibition NOT_WAIVABLE. | open |
| `PRIV-LAUNCH-007` | Retention, deletion, legal hold, backup/vendor reconciliation and data-subject rights workflows MUST be approved and tested. | BLOCK | BLOCK | BLOCK | Records/Privacy Owner | `OQ-006` closure; retention config; expiry/deletion/right-request E2E; backup/vendor evidence. | Minimize collection; disable unsupported rights claim; never claim deletion complete without evidence. | Production retention/right obligations cannot be waived by engineering. | open |
| `PRIV-LAUNCH-008` | Data minimization and classification MUST cover API, DB, cache, vector, prompt, log, audit, analytics, notification, export and browser storage. | BLOCK | BLOCK | BLOCK | Data + Security Owner | Field inventory; schema allowlist; cache/log/browser DLP; cross-user isolation; export audit tests. | Unknown classified C3; reject field/export/provider call. | Secret, cross-user and prohibited telemetry controls NOT_WAIVABLE. | open |
| `PRIV-LAUNCH-009` | Sensitive/emergency data handling MUST minimize notification/summary, restrict access, use approved copy/contact and avoid diagnosis/profiling. | BLOCK | BLOCK | BLOCK | Privacy + Student Support Lead | Synthetic safety eval for demo; restricted-store/access/DLP tests; approved operating model and contacts for pilot/prod. | No fake contact; disable real safety service; route only to approved HITL when available. | Real-user sensitive/emergency processing NOT_WAIVABLE without approved operating/legal model. | open |
| `PRIV-LAUNCH-010` | Incident notification assessment, data-rights coordination, vendor/subprocessor deletion and periodic privacy review MUST have accountable operators. | CONDITIONAL | BLOCK | BLOCK | Privacy Incident Lead | Contact/RACI; incident and rights tabletop; vendor coordination; annual/material-change review schedule. | Keep real-data processing disabled or suspend affected flow. | Pilot/production accountable privacy operator cannot be waived. | open |

Privacy-control mapping:

| Launch blocker | Required controls |
|---|---|
| `PRIV-LAUNCH-001` | `PRIV-FLOW-001` đến `PRIV-FLOW-009`, `PRIV-FLOW-013`, `PRIV-FLOW-018`, `SEC-CTRL-001`, `SEC-CTRL-015` |
| `PRIV-LAUNCH-002` | `PRIV-DATA-001`, `PRIV-DATA-002`, `PRIV-DPIA-001`, `SEC-DATA-001`, `SEC-CTRL-030` |
| `PRIV-LAUNCH-003` | `PRIV-FLOW-010`, `PRIV-FLOW-011`, `PRIV-DPIA-014` |
| `PRIV-LAUNCH-004` | `PRIV-DPIA-001` đến `PRIV-DPIA-020`, `SEC-CTRL-015` |
| `PRIV-LAUNCH-005` | `PRIV-VEND-001` đến `PRIV-VEND-012`, `SEC-CTRL-022` |
| `PRIV-LAUNCH-006` | `PRIV-XFER-001` đến `PRIV-XFER-010`, `PRIV-FLOW-016` đến `PRIV-FLOW-018`, `SEC-CTRL-005`, `SEC-CTRL-016`, `SEC-CTRL-022` |
| `PRIV-LAUNCH-007` | `PRIV-FLOW-009`, `PRIV-DPIA-005`, `PRIV-DPIA-017`, `PRIV-RET-*`, `SEC-CTRL-015`, `SEC-CTRL-020` |
| `PRIV-LAUNCH-008` | `SEC-DATA-001` đến `SEC-DATA-006`, `PRIV-DATA-003`, `PRIV-DATA-004`, `PRIV-FLOW-012` đến `PRIV-FLOW-016`, `SEC-CTRL-006`, `SEC-CTRL-013`, `SEC-CTRL-018` |
| `PRIV-LAUNCH-009` | `PRIV-DPIA-007`, `PRIV-DPIA-016`, `SEC-CTRL-003`, `SEC-CTRL-025` |
| `PRIV-LAUNCH-010` | `PRIV-DPIA-017`, `PRIV-DPIA-020`, `SEC-CTRL-015`, `SEC-CTRL-021`, `SEC-CTRL-022` |

## 6. Open-question closure map (`OQ-001..008`)

Không open question nào được “đóng” bằng code. Closure cần owner, decision, scope, evidence và ngày review.

| Open question | Demo treatment | Pilot/production closure evidence | Blocking IDs | Fail-closed result |
|---|---|---|---|---|
| `OQ-001` — University Product Owner/final approver | Named internal demo owner được phép ký demo-only scope; không đại diện production. | Named university Product Owner, authority record, acceptance/rejection criteria and signed launch decision. | `SEC-LAUNCH-001`, `SEC-LAUNCH-016` | Không pilot/production launch. |
| `OQ-002` — Student-data owner/integration approval | Synthetic Data Steward phê duyệt generator/provenance. | Named Data Owner, field/purpose/recipient inventory and per-integration approval. | `PRIV-LAUNCH-001`, `PRIV-LAUNCH-008`, `SEC-LAUNCH-015` | Không real data/integration. |
| `OQ-003` — Emergency contacts/messages/staffed hours | Chỉ copy `DEMO — chưa cấu hình đầu mối khẩn cấp chính thức`; no fake contact. | Signed contacts, wording, hours, queue/on-call, escalation and drill. | `SEC-LAUNCH-008`, `SEC-LAUNCH-013`, `PRIV-LAUNCH-009` | Safety surface real-user bị disable; launch block nếu scope yêu cầu. |
| `OQ-004` — Entra tenant/claims/groups | Isolated mock auth; production mode hard rejects it. | Tenant/issuer/audience/app registration, role/claim mapping, MFA/CA, revocation and cutover/rollback evidence. | `SEC-LAUNCH-002`, `SEC-LAUNCH-003` | Deny pilot/prod authentication; no mock fallback. |
| `OQ-005` — Legal conditions for external LLM | Fake provider; live DeepSeek chỉ với synthetic C0/C1 + paid-service/egress approval. | Legal memorandum, DPA, transfer/vendor records, data-use/retention/subprocessor approval and runtime policy. | `SEC-LAUNCH-005`, `PRIV-LAUNCH-005`, `PRIV-LAUNCH-006` | External call denied; local deterministic fallback. |
| `OQ-006` — Retention/deletion periods | Configurable synthetic retention and purge test; no legal promise. | Approved schedule per data object; legal hold, rights, backup/vendor deletion and evidence. | `PRIV-LAUNCH-007`, `SEC-LAUNCH-011` | Minimize/disable storage; do not claim deletion complete. |
| `OQ-007` — SIS/LMS/ticket/room APIs | Deterministic synthetic adapters only; clearly non-authoritative. | Named owner, contract/sandbox, field classification, credentials, limits, idempotency and failure behavior per integration. | `SEC-LAUNCH-015`, `PRIV-LAUNCH-001`, `PRIV-LAUNCH-008` | Integration/capability disabled; no fabricated authoritative result. |
| `OQ-008` — AWS/LLM budget | No paid call by default; explicit bounded demo approval if used. | Approved monthly budget, per-service/provider hard/soft limits, alert owner, kill switch and overage decision. | `SEC-LAUNCH-014`, `SEC-LAUNCH-016` | Paid/AI-heavy path disabled at hard limit. |

## 7. Waiver and exception rules

### 7.1 Allowed only under explicit policy

Một exception hợp lệ MUST thỏa `SEC-CTRL-026` đến `SEC-CTRL-030` và có:

```yaml
launch_exception:
  exception_id: "EXC-..."
  blocker_id: "SEC-LAUNCH-...|PRIV-LAUNCH-..."
  release_id: "immutable-release-id"
  environments: []
  capabilities: []
  data_classes: []
  reason: "specific evidence-based reason"
  compensating_controls: []
  residual_risk: "explicit statement"
  owner: "named role/person"
  independent_reviewer: "named role/person"
  required_approvers: []
  evidence_refs: []
  approved_at: "RFC3339"
  expires_at: "RFC3339 no later than 90 days by default"
  rollback_or_disable_trigger: "measurable trigger"
  status: "requested|approved|expired|revoked"
```

### 7.2 Never implied

- Absence of a finding is not a waiver.
- A successful demo is not pilot/production approval.
- A vendor console setting is not legal approval.
- A Product Owner cannot alone waive Security/Privacy/Legal ownership.
- `not_applicable_for_release` requires proof the capability, route, data field, credential and UI claim are absent/disabled.
- Expired, scope-mismatched or changed evidence reopens the blocker automatically.

### 7.3 Non-waivable conditions

The following MUST block the affected pilot/production release unless the underlying requirement is actually closed; no engineering waiver can substitute:

- unauthorized access or cross-user/cross-unit disclosure;
- unconfirmed/non-idempotent write or unknown result presented as success;
- secret, C2/C3 or unapproved personal-data egress;
- production mock auth, wildcard issuer/audience or missing privileged MFA control;
- missing accountable Product/Data/Privacy/Security/Incident owner;
- unknown lawful condition, vendor legal entity, processing location/subprocessor or transfer condition for real data;
- inability to provide required privacy notice/rights/retention/deletion behavior;
- missing/unauditable security events for high-risk actions;
- real emergency/sensitive service without approved contact, operating model and privacy controls;
- unresolved Critical security finding or High finding prohibited by `SEC-CTRL-027`;
- use of real personal data in an environment approved only for synthetic data.

Legal Owner MAY determine that a legal requirement is satisfied, inapplicable or differently scoped, but that is a documented legal determination—not a waiver invented by an agent.

## 8. Launch decision algorithm

```text
1. Freeze release ID, source/config/model/corpus versions, stage and capability list.
2. Resolve every BLOCK item and every CONDITIONAL item whose capability is enabled.
3. Verify all referenced evidence belongs to this release/scope and is not expired.
4. Reopen items affected by changes, incidents, failed tests or unknown telemetry.
5. Validate exceptions against scope, approvers, compensating controls and expiry.
6. Confirm disabled items are absent from routes, credentials, jobs, UI claims and egress.
7. Product, Security, Privacy/Legal and Operations owners sign their sections.
8. Release Owner records GO or NO-GO. Missing/ambiguous evidence = NO-GO.
9. Production deployment remains a separate human-approved action.
10. Run post-release verification; drift/critical failure invokes rollback or safe mode.
```

Machine-readable decision shape:

```yaml
launch_decision:
  release_id: "immutable-release-id"
  stage: "simulated_demo|pilot|production"
  data_mode: "synthetic_only|approved_real_data_scope"
  enabled_capabilities: []
  blocker_results:
    - blocker_id: "SEC-LAUNCH-001"
      applicability: "BLOCK|CONDITIONAL|NOT_APPLICABLE"
      status: "open|evidence_pending|closed|waived_time_bound|not_applicable_for_release"
      evidence_refs: []
      exception_id: null
      owner: "role"
      verified_by: "independent role when required"
      verified_at: null
      expires_at: null
  unresolved_blockers: []
  decision: "NO_GO"
  approvers: []
  decided_at: null
```

Validation rules:

- `GO` is invalid when `unresolved_blockers` is non-empty.
- `GO` is invalid when a required approval or evidence reference is empty.
- `waived_time_bound` is invalid without active exception and compensating-control evidence.
- `not_applicable_for_release` is invalid when route, credential, UI claim, scheduled job or network path exists.
- A `simulated_demo` decision cannot be promoted to `pilot` or `production`; a new decision is required.

## 9. Stage-specific minimum go/no-go packs

### Simulated demo

At minimum close:

- `SEC-LAUNCH-001`, `002`, `004`, `006`, `007`, `008`, `009`, `012`, `013`, `016`;
- `PRIV-LAUNCH-001`, `002`, `004`, `007`, `008`, `009`;
- every conditional item whose provider, persistence, paid service or integration is enabled;
- banner/disclosure tests proving `HUCE Demo`, synthetic/non-official status and no human/emergency promise.

### Pilot

Close every `BLOCK` row plus every enabled conditional row, all `OQ-001..008` relevant to pilot scope, DPIA/vendor/transfer/retention/legal gates, real identity, staffed support, incident/rollback and time-bounded cohort/exit plan. No real user may be enrolled before the privacy notice and identity/access tests pass.

### Production

Close all production rows, complete independent penetration/security review, vendor/cross-border/legal sign-off, Entra/MFA/revocation drill, restore/incident/degraded-mode drill, operations readiness, immutable evidence bundle and human GO decision required by `SEC-SDLC-007`. Production agent deployment remains prohibited.

## 10. Traceability and change triggers

- Governance: `DEC-001`, `DEC-002`, `DEC-004`, `DEC-007` đến `DEC-010`, `DEC-014`, `DEC-015`, `DEC-020`; `OQ-001` đến `OQ-008`.
- Product/security NFR: `REQ-NF-SEC-001` đến `REQ-NF-SEC-008`, `REQ-NF-PRIV-001` đến `REQ-NF-PRIV-005`, `REQ-NF-REL-001` đến `REQ-NF-REL-005`, `REQ-NF-COST-001` đến `REQ-NF-COST-003`.
- Security gates: `SEC-SDLC-001` đến `SEC-SDLC-018`.
- Vendor/transfer: `PRIV-VEND-001` đến `PRIV-VEND-012`, `PRIV-XFER-001` đến `PRIV-XFER-010`.
- Control catalog: `SEC-CTRL-001` đến `SEC-CTRL-030`.
- DPIA: `PRIV-DPIA-001` đến `PRIV-DPIA-020`.

Re-run launch assessment after any change to requirement, data field/class/purpose, role/permission, auth provider/claim, vendor/legal entity, model/endpoint, region/location/subprocessor, prompt/tool, source corpus, retention, integration, write contract, emergency wording/contact, security control, infrastructure boundary or incident finding.
