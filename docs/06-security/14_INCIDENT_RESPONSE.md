---
document_id: "DOC-SEC-009"
version: "0.1.0"
status: "draft"
owner: "Incident Response Owner"
approvers: ["Security Architect", "Privacy/Legal Owner", "Operations Owner", "University Sponsor"]
last_updated: "2026-09-21"
---

# Security and privacy incident response

## 1. Authority and current limitation

Tên người trực, kênh liên hệ, cơ quan/đầu mối pháp lý và hours of coverage chưa được chỉ định. Vì vậy tài liệu là framework sơ bộ; production launch bị chặn. AI/agent MUST không tự thông báo cơ quan nhà nước, sinh viên, báo chí hoặc vendor ngoài approved playbook.

NIST SP 800-61 Rev. 3 khuyến nghị tích hợp incident response vào quản trị rủi ro toàn vòng đời; tài liệu này dùng [NIST SP 800-61 Rev. 3](https://csrc.nist.gov/pubs/sp/800/61/r3/final) làm baseline, không phải chứng nhận.

## 2. Severity

| Severity | Tiêu chí | Internal target |
|---|---|---|
| SEV-0 | Confirmed ongoing mass/critical harm; broad real PII/secret exfiltration; destructive compromise | Page immediately; acknowledge ≤15 min; executive/privacy/legal immediately |
| SEV-1 | Cross-user disclosure, auth bypass, unauthorized write, restricted-data exposure, audit/key compromise | Acknowledge ≤30 min; contain ≤4 h target |
| SEV-2 | Bounded control failure/no confirmed disclosure; exploitable High finding | Acknowledge ≤4 business h |
| SEV-3 | Low-impact anomaly/policy violation | Triage ≤1 business day |

Targets là internal operational objectives, không thay statutory deadline/SLA. Nếu phân loại không chắc chắn, MUST chọn severity cao hơn tạm thời.

## 3. Roles

| Role | Responsibility | MUST NOT |
|---|---|---|
| Incident Commander | Declare severity, coordinate containment/recovery | Tự quyết legal notice nếu không có authority |
| Security Lead | Technical triage, evidence, containment | Modify original evidence |
| Privacy/Legal Lead | Assess personal-data scope, rights/authority/vendor notices | Delay triage while facts incomplete |
| Operations Lead | Service switch, rollback, restore, communications execution | Reopen before exit criteria |
| Product/University Owner | Business/student impact and approved messaging | Promise outcome before verified |
| Scribe/Evidence Custodian | Timeline, decisions, hashes, custody | Put secrets/PII into broad chat |

Một người MAY giữ nhiều vai trong simulation drill; production MUST name primary and backup.

## 4. Lifecycle

```text
Detect/Report -> Triage -> Declare -> Contain -> Preserve/Investigate
              -> Eradicate -> Recover -> Notify as legally approved
              -> Post-incident review -> Control/DPIA update
```

### Triage minimum

- what was observed and by whom;
- first known/possible occurrence and detection time;
- affected environment/components/data classes;
- whether real/synthetic data, secrets, users or external transfer involved;
- active threat and safe containment options;
- evidence locations and access restrictions.

### Containment priorities

1. prevent ongoing harm/exfiltration;
2. preserve evidence and time line;
3. revoke/rotate exposed credentials;
4. disable affected tool/provider/source/feature with kill switch;
5. move to approved degraded mode;
6. avoid destructive “cleanup” that erases evidence.

## 5. Playbooks

### `SEC-IR-001` — Suspected credential/secret exposure

1. mark credential compromised; do not print it;
2. revoke/rotate through owner-approved path;
3. identify accesses since earliest exposure;
4. preserve relevant audit/build history;
5. invalidate sessions/derived credentials when applicable;
6. verify replacement and remove vulnerable source;
7. run leak scan and document residual risk.

### `PRIV-IR-001` — Personal-data disclosure

1. set severity at least SEV-1 until bounded;
2. stop affected flow and external transfer;
3. identify data subjects/categories, sensitivity, recipients, geography and duration;
4. preserve minimal evidence in C3 vault;
5. Privacy/Legal Lead assesses notifications and statutory clocks;
6. coordinate processor/vendor evidence/deletion;
7. approved communication MUST state verified facts only.

[Luật 91/2025/QH15](https://vbpl.vn/TW/Pages/ivbpq-toanvan.aspx?ItemID=179252&Keyword=) và [Nghị định 356/2025/NĐ-CP](https://vbpl.vn/bocongan/Pages/vbpq-toanvan.aspx?ItemID=187276) govern personal-data incident duties. Legal Owner MUST maintain an authoritative notification matrix and current forms; implementation MUST not hard-code a legal deadline based only on this draft.

### `SEC-IR-002` — Prompt injection/unauthorized tool action

1. disable affected tool/source/prompt version;
2. reconcile all tool execution IDs and side effects;
3. revoke confirmation/session if compromised;
4. quarantine malicious source/input signature;
5. run related `THR-ABUSE-*` corpus;
6. update threat/control/eval; do not rely on prompt patch alone.

### `SEC-IR-003` — Knowledge poisoning/misinformation

1. retire affected source/version and disable RAG collection;
2. identify answers/citations generated from source checksum;
3. switch to ticket/search-only mode;
4. independent Knowledge + Security review;
5. republish only after corpus/eval regression;
6. assess user correction notice through Product/Legal.

### `SEC-IR-004` — Provider compromise/outage/cross-border anomaly

1. trip provider circuit breaker and block egress;
2. switch fake/approved alternative only under configuration policy or degrade;
3. preserve provider request IDs, contract/version/location evidence;
4. rotate provider secret if indicated;
5. Privacy/Legal assesses transfer impact;
6. no silent provider substitution with different terms/region.

### `SEC-IR-005` — Ransomware/destructive data event

1. isolate affected workload/account; preserve snapshots/evidence when safe;
2. block write and credential paths;
3. validate clean backup and infrastructure source;
4. rebuild from trusted artifact, not compromised host;
5. replay deletion tombstones before reopen;
6. verify integrity, auth, audit and core controls before recovery.

## 6. Normative requirements

| ID | Requirement | Evidence | Failure behavior |
|---|---|---|---|
| `SEC-IR-006` | Every production incident MUST have immutable case/timeline, commander, severity and decision log. | Case export/hash. | Escalate governance failure. |
| `SEC-IR-007` | Evidence MUST preserve provenance/hash/access chain and remain C3. | Custody log and access audit. | Evidence marked unreliable; no silent repair. |
| `SEC-IR-008` | Destructive remediation MUST not occur before evidence/target/recovery review unless necessary to stop imminent harm and documented. | Decision record. | Stop action/escalate. |
| `SEC-IR-009` | External communication/notification MUST be approved by Privacy/Legal and authorized university role. | Approval + sent artifact. | No send. |
| `SEC-IR-010` | Recovery MUST satisfy explicit exit criteria: root cause bounded, credentials handled, clean artifact/data, controls/tests passing, monitoring elevated. | Recovery checklist. | Remain degraded/offline. |
| `SEC-IR-011` | SEV-0/1 post-incident review MUST complete within 10 business days target and create tracked control actions. | PIR document/action list. | Escalate overdue. |
| `SEC-IR-012` | Tabletop and technical drills MUST occur before production and at least annually; critical playbooks SHOULD be tested more frequently after major change. | Drill reports. | Production/review gate fails. |
| `PRIV-IR-002` | Notification deadline tracking MUST start from legally relevant event determined by Legal Owner; system MUST preserve detection/occurrence timestamps. | Notification decision record. | Escalate immediately. |
| `PRIV-IR-003` | Communications MUST minimize data and never disclose another subject's details. | Legal/privacy review. | Message blocked. |

## 7. Incident record schema

```yaml
incident:
  id: "SEC-INC-opaque"
  severity: "SEV-0|SEV-1|SEV-2|SEV-3"
  status: "triage|contained|eradication|recovery|closed"
  commander: "named-role"
  detected_at: "RFC3339"
  earliest_known_at: "RFC3339|null"
  data_classes: ["CONFIDENTIAL"]
  real_personal_data: false
  affected_components: ["logical-name"]
  threat_ids: ["THR-..."]
  containment_actions: ["change/evidence ref"]
  evidence_refs: ["restricted-uri-and-hash"]
  legal_privacy_assessment_ref: "ref|null"
  external_notifications: []
  recovery_evidence: ["test/drill ref"]
  residual_risk: "statement"
```

## 8. Traceability

- Controls: `SEC-CTRL-018`, `SEC-CTRL-020`, `SEC-CTRL-021`.
- Threats/abuse: all `THR-*`, especially `THR-T-004`, `THR-I-*`, `THR-LLM-*`.
- Launch blockers: `SEC-LAUNCH-010`, `PRIV-LAUNCH-008`.

Nguồn được truy cập ngày `2026-09-21`.
