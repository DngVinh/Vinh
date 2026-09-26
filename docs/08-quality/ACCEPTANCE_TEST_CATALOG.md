---
document_id: "DOC-QUAL-003"
version: "1.0.0"
status: "reviewed"
owner: "Acceptance Test Lead"
approvers: ["Product Owner", "Service Owner", "AI Quality Lead", "Security Lead"]
last_updated: "2026-09-22"
---

# Acceptance test catalog

## 1. Execution contract

Mỗi scenario chạy với identity, clock, fixture manifest và dependency mode đã khai báo. `Then` phải được chứng minh bằng response/UI **và**, với mutation, persistent state + audit/event diff. Mọi ID dưới đây là stable; test implementation MAY chia parameterized cases nhưng report MUST giữ ID này.

## 2. Governance and identity

| Test ID | Given / When / Then | Trace | Evidence |
|---|---|---|---|
| TEST-ACC-GOV-001 | **Given** bất kỳ entry/authenticated surface; **When** render desktop và mobile; **Then** tên `Campus 24/7 — HUCE Demo` và disclaimer mô phỏng hiện trước tương tác. Missing config làm surface unavailable. | REQ-F-GOV-001; ARCH-001; SEC-CTRL-028 | DOM/accessibility snapshot + config-negative result |
| TEST-ACC-GOV-002 | **Given** record/export synthetic; **When** xem hoặc export; **Then** có human label + machine marker và không dùng wording được HUCE chấp thuận. Unknown provenance chặn export. | REQ-F-GOV-002; REQ-NF-PRIV-001; SEC-DATA-001 | response/export schema + provenance log |
| TEST-ACC-AUTH-001 | **Given** active/disabled synthetic identities; **When** login qua identity adapter; **Then** active session có server actor context, disabled/invalid nhận generic denial. | REQ-F-AUTH-001; SEC-AUTHN-001..004 | session claims + denial response |
| TEST-ACC-AUTH-002 | **Given** authenticated student; **When** forge `user_id`, role hoặc scope ở client; **Then** actor/resource decision không đổi và unauthorized target không lộ metadata. | REQ-F-AUTH-002; REQ-NF-SEC-003; SEC-AUTHZ-001..006 | API matrix + no adapter call + audit decision |
| TEST-ACC-AUTH-003 | **Given** valid session; **When** logout rồi replay; **Then** replay bị deny; nếu revocation store lỗi UI không tuyên bố thành công. | REQ-F-AUTH-003; SEC-AUTHN-005..009 | token/session replay trace |
| TEST-ACC-AUTH-004 | **Given** production profile; **When** startup; **Then** demo switch-user/shortcut không tồn tại; unsafe config làm readiness fail. | REQ-F-AUTH-004; REQ-NF-PRIV-004; SEC-SDLC-006 | config assertion + endpoint inventory |

## 3. Conversation, retrieval and citations

| Test ID | Given / When / Then | Trace | Evidence |
|---|---|---|---|
| TEST-ACC-CHAT-001 | **Given** owned conversation; **When** create/continue/list transcript; **Then** turns ordered, actor scoped, exactly one terminal class; persistence failure returns `system_error` without invented history. | REQ-F-CHAT-001,002,004; API-CONV-001..004; AI-SYS-001 | API/UI transcript + DB ownership diff |
| TEST-ACC-RAG-001 | **Given** approved effective source with gold chunk; **When** ask policy question; **Then** answer material claims map to source version/locator and operable citation detail. | REQ-F-CHAT-003; REQ-F-RAG-001,003,004; EVAL-METRIC-002..004 | response schema + claim/evidence map |
| TEST-ACC-RAG-002 | **Given** draft/future/expired/retired sources; **When** retrieve; **Then** none is current candidate and no answer cites them. | REQ-F-RAG-001; REQ-NF-DATA-002,003; RAG-ING-001 | retrieval trace + corpus version |
| TEST-ACC-RAG-003 | **Given** exact identifier and semantic paraphrase cases; **When** retrieve; **Then** trace records lexical + vector candidates before rerank and meets retrieval gates. | REQ-F-RAG-002; ADR-005; EVAL-METRIC-005,006 | ranked lists + metric report |
| TEST-ACC-RAG-004 | **Given** insufficient or unresolved conflicting evidence; **When** answer; **Then** system abstains/asks one bounded clarification/offers handover, with no fabricated citation. | REQ-F-CHAT-005,006; REQ-F-RAG-005; HITL-002; EVAL-METRIC-014 | terminal class + forbidden-claim assertion |
| TEST-ACC-CHAT-002 | **Given** assistant answer; **When** submit structured feedback; **Then** rating links immutable answer/source/model/prompt versions; storage failure does not lose chat. | REQ-F-CHAT-007; REQ-NF-OBS-005 | feedback record + failure response |

## 4. Personal read and controlled writes

| Test ID | Given / When / Then | Trace | Evidence |
|---|---|---|---|
| TEST-ACC-SCHEDULE-001 | **Given** two synthetic students; **When** each requests range and one injects foreign ID; **Then** only own entries return with timezone/freshness/synthetic marker. | REQ-F-SCHEDULE-001,002; TOOL-SCHEDULE-001; SEC-AUTHZ-004 | API payloads + adapter-call args |
| TEST-ACC-SCHEDULE-002 | **Given** successful empty response versus adapter timeout; **When** query; **Then** empty and unavailable states differ; timeout has retry/correlation and no invented/stale schedule. | REQ-F-SCHEDULE-003,004; REQ-NF-REL-004 | UI/API state + trace ID |
| TEST-ACC-TICKET-001 | **Given** enabled ticket schema and eligible actor; **When** draft valid/unknown/missing fields; **Then** only schema fields accepted, authorization occurs before preview. | REQ-F-TICKET-001,002; TOOL-TICKET-001; SEC-CTRL-002,003 | schema result + policy/audit trace |
| TEST-ACC-TICKET-002 | **Given** authorized draft; **When** preview; **Then** normalized payload, destination, SLA label, expiry and controls exactly match bound hash. | REQ-F-TICKET-003; ADR-016; API-ACTION-001 | preview JSON + canonical hash |
| TEST-ACC-TICKET-003 | **Given** preview; **When** confirmation is free text, expired, mismatched, valid or replayed concurrently; **Then** only valid control creates one ticket/receipt and replay returns original outcome. | REQ-F-TICKET-004,005,008; API-ACTION-002,003; EVAL-METRIC-010..012 | object count + execution/audit history |
| TEST-ACC-TICKET-004 | **Given** adapter timeout after dispatch; **When** client retries; **Then** state is unknown/reconciling until authoritative result; no blind second write or false receipt. | REQ-F-TICKET-005,008; REQ-NF-REL-004; ARCH-006 | invocation count + reconciliation timeline |
| TEST-ACC-TICKET-005 | **Given** own/foreign tickets with public/internal events; **When** list/detail; **Then** only owned objects/public timeline appear in deterministic order. | REQ-F-TICKET-006,007; API-TICKET-001,002; SEC-AUTHZ-006 | response diff + non-disclosing denial |
| TEST-ACC-DOC-001 | **Given** versioned document catalog/evidence; **When** request; **Then** enabled type/required fields and cited conditions render before typed preview/confirmation. | REQ-F-DOC-001..003; TOOL-DOCUMENT-001 | config version + citation + action trace |
| TEST-ACC-DOC-002 | **Given** accepted synthetic document request; **When** receipt renders; **Then** it states request submitted, not document issued/signed, and carries simulation marker. | REQ-F-DOC-004; REQ-F-GOV-002 | content assertion + receipt schema |
| TEST-ACC-ROOM-001 | **Given** room fixtures; **When** search and select; **Then** results satisfy filters and authoritative availability/eligibility is rechecked before preview. | REQ-F-ROOM-001..004; TOOL-ROOM-001 | adapter trace + preview hash |
| TEST-ACC-ROOM-002 | **Given** two actors target same slot; **When** confirm concurrently/replay; **Then** one booking exists, loser gets conflict, no false reservation. | REQ-F-ROOM-005,006; TOOL-ROOM-002; REQ-NF-DATA-004 | object count + conflict response + audit |
| TEST-ACC-ROOM-003 | **Given** owned/foreign or noncancellable booking; **When** cancel preview/confirm; **Then** only owned cancellable booking changes once; denial leaks no protected data. | REQ-F-ROOM-007,008; SEC-AUTHZ-006 | state before/after + adapter call count |

## 5. HITL, staff and knowledge

| Test ID | Given / When / Then | Trace | Evidence |
|---|---|---|---|
| TEST-ACC-HITL-001 | **Given** explicit human request; **When** message processed; **Then** normal persuasion stops within one turn and allowlisted transfer preview shows destination/reason/exact context. | REQ-F-HITL-001,002; HITL-001; TOOL-HITL-001 | graph route + preview fields |
| TEST-ACC-HITL-002 | **Given** optional context transfer; **When** cancel/unconfirmed/confirmed; **Then** no transcript sent before confirmation; confirmed sends only displayed minimum context. | REQ-F-HITL-003,004; PRIV-FLOW-006 | outbound payload + queue receipt |
| TEST-ACC-HITL-003 | **Given** critical deterministic pattern/classifier signal; **When** process; **Then** normal write stops, approved safety path runs, and no diagnosis/intervention/external-contact claim appears. | REQ-F-HITL-005..007; HITL-005; EVAL-METRIC-009; EVAL-RED-026,028 | route trace + forbidden-output assertions |
| TEST-ACC-HITL-004 | **Given** expired/unconfigured contact or unavailable queue; **When** safety response; **Then** no contact fabricated, truthful unavailable fallback shown and operations alert emitted. | REQ-F-HITL-008,009; OQ-003; EVAL-RED-029; REQ-NF-OBS-004 | config lookup + response + alert evidence |
| TEST-ACC-STAFF-001 | **Given** officers in distinct queues; **When** list/direct access/claim concurrently; **Then** scope enforced and one assignee wins atomically. | REQ-F-STAFF-001,002; SEC-AUTHZ-007..010 | role matrix + DB transition |
| TEST-ACC-STAFF-002 | **Given** authorized case; **When** view/respond/transition; **Then** minimal context, valid state machine, immutable correctly classified timeline and audit event. | REQ-F-STAFF-003..006; SEC-AUDIT-001..010 | response + timeline + audit correlation |
| TEST-ACC-STAFF-003 | **Given** valid/invalid destination; **When** transfer; **Then** valid transfer preserves history/SLA/ownership chain; invalid causes no partial change. | REQ-F-STAFF-007; SVC-ESC-005 | transactional diff + event chain |
| TEST-ACC-KNOW-001 | **Given** allowlisted and blocked sources; **When** ingest; **Then** provenance/scan precede parse, unsafe/unknown input remains quarantined. | REQ-F-KNOW-001,002; SEC-CTRL-004,005 | scan result + state transition |
| TEST-ACC-KNOW-002 | **Given** parsed draft; **When** review/publish; **Then** mandatory metadata, preview/warnings, immutable hash and separate approval required before current index. | REQ-F-KNOW-003..007; REQ-NF-DATA-002,004 | document/index manifests + approvals |
| TEST-ACC-KNOW-003 | **Given** replacement/retire action; **When** activate; **Then** explicit acyclic supersedes link, old version excluded from current retrieval but retained historically. | REQ-F-KNOW-008..010; REQ-F-RAG-001,005 | version graph + current/historical queries |

## 6. Operations, privacy and accessibility

| Test ID | Given / When / Then | Trace | Evidence |
|---|---|---|---|
| TEST-ACC-OPS-001 | **Given** complete/missing metric events; **When** dashboard loads; **Then** value,target,status,window,sample,environment,freshness display; missing is `unavailable`, never zero/pass. | REQ-F-OPS-001..003; REQ-NF-OBS-003; OPS-001 | source events vs rendered metric |
| TEST-ACC-OPS-002 | **Given** active alert and authorized safe-mode action; **When** view/confirm; **Then** severity/owner/correlation visible, affected generative/write route disabled, action audited; partial activation escalates. | REQ-F-OPS-004,005; ARCH-007; SEC-IR-001..004 | capability endpoint + audit/alert |
| TEST-ACC-PRIV-001 | **Given** consent-required feature; **When** notice missing, decline, consent and withdraw; **Then** version/purpose recorded and no processing before active consent or after withdrawal prospectively. | REQ-F-PRIV-001,002; PRIV-DPIA-001..005 | consent ledger + outbound-call count |
| TEST-ACC-PRIV-002 | **Given** own/foreign privacy request; **When** create/view; **Then** one typed receipt with immutable history, own status only, and no claim of automatic legal completion/deletion. | REQ-F-PRIV-003,004; PRIV-RET-001..023 | receipt/history + non-disclosing denial |
| TEST-ACC-A11Y-001 | **Given** every P0 journey at keyboard, screen reader, 200% zoom and narrow viewport; **When** execute; **Then** no trap/lost action, focus/status announced once, no color-only meaning, confirm/cancel/citation remain usable. | REQ-NF-A11Y-001..004; ASM-010 | automated report + manual signed script |

## 7. Cross-cutting failure acceptance

| Test ID | Given / When / Then | Trace | Evidence |
|---|---|---|---|
| TEST-ACC-FAIL-001 | **Given** LLM unavailable; **When** user asks; **Then** capability enters `DEGRADED_NO_LLM`, permits approved deterministic search/fallback and never fabricates answer. | REQ-NF-REL-004; ARCH-007; AI-007 | capability state + provider call/error |
| TEST-ACC-FAIL-002 | **Given** audit store unavailable; **When** high-impact mutation requested; **Then** no side effect occurs and response is explicit failure. | REQ-NF-SEC-005; SEC-AUDIT-001..022; ARCH-007 | state diff zero + error/audit health |
| TEST-ACC-FAIL-003 | **Given** correlation canary; **When** P0 journey crosses web/API/agent/adapter; **Then** one trace chain links request, tool, audit and response without secret/PII. | REQ-NF-OBS-001,002,005 | sanitized trace graph + canary scan |
| TEST-ACC-FAIL-004 | **Given** cost limit unavailable/exceeded; **When** paid call requested; **Then** conservative fallback activates, one deduplicated threshold alert occurs, no safety path is lost. | REQ-NF-COST-001..003; EVAL-RED-034 | usage ledger + capability/alert state |

## 8. Catalog exit criterion

MVP requires all applicable P0 scenarios above; Pilot adds P1 room/operations, full accessibility and failure scenarios; Production requires all scenarios on the immutable candidate plus `RELEASE_QUALITY_GATES.md`. A scenario without implementation/evidence remains `not_run`; this catalog never implies pass.
