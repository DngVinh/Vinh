---
document_id: "DOC-QUAL-006"
version: "1.0.0"
status: "reviewed"
owner: "Security Quality Engineering Lead"
approvers: ["Security Architect", "Privacy Lead", "Architecture Lead", "Release Owner"]
last_updated: "2026-09-22"
---

# Security test plan

## 1. Policy

Security verification inherits `SEC-SDLC-001..008`, `SEC-CTRL-001..030`, security threat/abuse catalogs and `REQ-NF-SEC-*`/`REQ-NF-PRIV-*`. Tests use synthetic actors, canary secrets and authorized environments only. No test may contact real users, scrape credentials, exploit systems outside the project, or destroy data.

Critical/High unresolved findings block release unless the source policy permits a time-bound exception; auth bypass, cross-user disclosure, unconfirmed/duplicate write, secret/PII egress and S1 AI bypass are production non-waivable.

## 2. Test catalog

| Test ID | Scope and oracle | Phase/cadence | Trace |
|---|---|---|---|
| TEST-SEC-STATIC-001 | SAST finds no unreviewed Critical/High dataflow; suppressions have owner/expiry | every PR/RC | REQ-NF-SEC-007; SEC-SDLC-003,004 |
| TEST-SEC-SECRET-001 | repository, history supplied to scanner, generated files, image and logs contain zero real/canary secret exposure | every PR/image/RC | REQ-NF-SEC-004; SEC-CRYPTO-005..012 |
| TEST-SEC-SCA-001 | pinned lockfiles/SBOM/license/SCA; no unresolved blocking CVE | PR/RC | REQ-NF-MAINT-003; SEC-SDLC-002,004 |
| TEST-SEC-IAC-001 | no public DB/cache/ECS task/S3; scoped IAM; encryption/logging/network policy asserted | IaC PR/RC | REQ-NF-SEC-001,002; ARCH-005; SEC-CTRL-009..014 |
| TEST-SEC-IMAGE-001 | minimal non-root image, pinned base digest, no secret/debug package, signed/scanned artifact | image build/RC | SEC-SDLC-004,006 |
| TEST-SEC-AUTHN-001 | disabled/expired/revoked/forged session denied; cookie/PKCE/issuer/audience/clock policy enforced per environment | auth change/RC | REQ-F-AUTH-001,003,004; SEC-AUTHN-001..012 |
| TEST-SEC-AUTHZ-001 | full actor/resource/action/context matrix defaults deny | every protected API/tool | REQ-NF-SEC-003; SEC-AUTHZ-001..014 |
| TEST-SEC-IDOR-001 | list/direct/cursor/cache/tool requests cannot cross synthetic users or queues and reveal no existence | PR/nightly/RC | KPI-006; SEC-CTRL-007,008 |
| TEST-SEC-WRITE-001 | free text, forged/expired/replayed/mismatched confirmation causes zero side effects | every write change/RC | DEC-015; ADR-016; SEC-CTRL-003 |
| TEST-SEC-AUDIT-001 | protected decision/mutation creates append-only event; application role cannot update/delete; audit outage blocks high-impact write | merge/RC | REQ-NF-SEC-005; SEC-AUDIT-001..022 |
| TEST-SEC-INPUT-001 | allowlist/schema/semantic validation blocks XSS, injection, SQL/path/URL payload and extra fields before render/tool/storage | PR/nightly | REQ-NF-SEC-008; EVAL-RED-010,011 |
| TEST-SEC-WEB-001 | CSP/security headers, cookie flags, CSRF/CORS, clickjacking/content-type/cache behavior pass | staging/RC | SEC-SDLC-006; REQ-NF-SEC-001 |
| TEST-SEC-ABUSE-001 | rate/size/concurrency budgets reject excess with stable 429 and no excess processing; outage follows endpoint risk mode | merge/load/RC | REQ-NF-SEC-006; EVAL-RED-031 |
| TEST-SEC-RAG-001 | indirect prompt injection/poisoned source/tool result cannot control graph, exfiltrate or publish | AI/RAG change/RC | EVAL-RED-004..006,017,032; SEC-SDLC-005 |
| TEST-SEC-LLM-001 | outbound provider payload excludes prohibited identifiers/secrets; redaction/policy outage blocks call | provider/prompt change/RC | REQ-NF-PRIV-002,005; EVAL-RED-023 |
| TEST-SEC-MEM-001 | conversation/checkpoint/memory isolation; sensitive disclosures not persisted as preference | memory change/RC | EVAL-RED-024,025; PRIV-FLOW-* |
| TEST-SEC-DATA-001 | provenance scan/sample identifies synthetic-only dataset and no directly contactable identity | dataset build/RC | REQ-NF-PRIV-001; DEC-004 |
| TEST-SEC-ENV-001 | credentials/stores/keys isolated by environment; production data cannot be imported down | environment/IaC RC | REQ-NF-PRIV-004; SEC-CTRL-016,017 |
| TEST-SEC-RET-001 | retention selection obeys versioned policy/boundaries; destructive execution remains disabled without authorized workflow | policy change/RC | REQ-NF-PRIV-003; PRIV-RET-001..023 |
| TEST-SEC-DAST-001 | authenticated API/browser DAST in allowlisted staging has no blocking finding; scope and rate recorded | staging/RC | SEC-SDLC-006,007 |
| TEST-SEC-EGRESS-001 | network egress reaches only allowlisted destinations/ports; unknown route denied and alerted | staging/RC | REQ-NF-PRIV-005; ARCH-004,005 |
| TEST-SEC-DETECT-001 | authz/secret/canary/critical-config events produce deduplicated alert with owner/correlation; alert-path failure has secondary signal | staging/RC | REQ-NF-OBS-004; SEC-CTRL-018,020,021 |
| TEST-SEC-IR-001 | SEV0/SEV1 tabletop contains, preserves evidence, activates safe mode and controls recovery | pre-pilot/RC | SEC-IR-001..012; SVC-ESC-001,002 |

## 3. Authorization matrix execution

For each protected operation generate cases across four roles (`STUDENT`, `SUPPORT_OFFICER`, `KNOWLEDGE_ADMIN`, `SYSTEM_ADMIN`) and contexts: own, other synthetic user, permitted queue, foreign queue, valid state, invalid state, active/disabled identity, missing/stale policy. Assert response, resource count, adapter invocation count, audit decision and cache key scope.

A 403 alone is insufficient: test MUST prove no side effect, no protected metadata in body/timing-sensitive detail/log and no permissive cache artifact.

## 4. Privacy and synthetic-data checks

Canary categories include synthetic name/student code/email/phone-like value, bearer-looking token and unique prompt marker. Scanners search repository fixtures, DB snapshots, S3 test objects, logs, traces, metrics labels, prompt/provider payloads, errors and exported evidence. Expected synthetic patterns must be manifest-listed; unlisted directly contactable-looking data is quarantined and `not_verified` until reviewed.

No security evidence bundle may contain raw transcript, full token, secret or direct identifier. Store hashes, case IDs and redacted excerpts only.

## 5. Supply-chain gate

Dependency addition requires purpose, owner, pinned version, source/maintenance/license/transitive-risk review, SBOM update and scan. The DeepSeek SDK, AWS SDK or framework package MUST NOT cross forbidden domain boundaries. Missing scan, stale vulnerability database beyond declared freshness, scan error or unreviewed suppression equals failed gate.

## 6. Penetration and adversarial testing

Before production, an independent authorized review must cover identity/session, IDOR/BOLA, staff/knowledge/admin privilege, preview-confirm replay, cursor/object reference, file ingestion, SSRF/egress, XSS/markdown rendering, prompt injection, source poisoning, tool argument abuse, secrets and cloud configuration. Findings must link reproducible synthetic evidence; testers MUST remain inside written scope.

## 7. Severity and response

| Severity | Gate behavior | Required response |
|---|---|---|
| Critical/S1 | immediate block, no production waiver | contain/disable, incident record, fix + regression + independent approval |
| High/S2 | block affected route/release | fix or keep route disabled; only policy-permitted non-production waiver |
| Medium | owner/expiry/compensating control | fix before agreed phase |
| Low/S3 | track | regression if behavior changes |

Scanner disagreement or unavailable test environment yields `not_verified`, not downgraded severity.

## 8. Evidence

Each report records tool/database signature version, scope, source/image/config hashes, synthetic dataset hash, exact test IDs, findings with file/endpoint/control trace, sanitized reproduction, false-positive review, waiver ID and reviewer. Evidence must satisfy `GATE-REL-004` and `TRACEABILITY_AND_EVIDENCE.md`.
