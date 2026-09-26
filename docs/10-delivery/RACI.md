---
document_id: "DOC-DEL-006"
version: "1.0.0"
status: "reviewed"
owner: "Program Governance Lead"
approvers: ["Product Owner", "Release Owner", "Security Lead", "AI Quality Lead", "Operations Lead"]
last_updated: "2026-09-22"
---

# RACI and decision rights

## 1. Roles

| Role | Accountability boundary |
|---|---|
| Product Owner (PO) | scope, outcomes, phase/go-live business decision; cannot override security/privacy hard gate |
| Delivery Lead (DL) | plan, dependency, milestone and blocker coordination |
| Engineering Lead (ENG) | implementation quality, dependencies and component ownership |
| Architecture Lead (ARCH) | ADR, boundaries, contract/data/event compatibility |
| Quality Lead (QE) | test strategy, acceptance oracle, evidence integrity and release-quality recommendation |
| AI Quality Lead (AIQ) | eval dataset/rubric/model-prompt-corpus promotion and AI quality decision |
| Security Lead (SEC) | threat/control/security finding and incident containment authority |
| Privacy/Legal Lead (PRIV) | data purpose/class/transfer/retention/vendor/legal approval |
| SRE/Operations Lead (OPS) | SLO, capacity, observability, incident, recovery and service modes |
| Release Owner (REL) | candidate custody, gate aggregation, deployment/rollback execution coordination |
| Student Support Lead (SUP) | queue, calendar, human process, training and support communications |
| Knowledge Governance Lead (KNOW) | source provenance, approval/version/publish/retire |
| Identity/Data/Integration Owner (INT) | Entra/SIS/LMS/room/ticket adapter contract and source authorization |
| Finance Owner (FIN) | AWS/LLM budget and paid-service approval |
| University Sponsor/Data Owner (UNI) | institutional authorization and real-data accountability; currently unassigned |

Names are `UNASSIGNED` until formally recorded. Agents may perform `R` implementation work but cannot be `A` or provide human approval.

## 2. Delivery RACI

| Activity | PO | DL | ENG | ARCH | QE | AIQ | SEC | PRIV | OPS | REL | SUP | KNOW | INT | FIN | UNI |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Approve V1 scope/requirement | A | R | C | C | C | C | C | C | C | I | C | C | C | C | I |
| Create/sequence micro-tasks | I | A/R | R | C | C | C | C | I | I | C | I | I | I | I | I |
| Approve architecture/ADR | C | I | R | A | C | C | C | C | C | I | I | I | C | C | I |
| Approve API/data/event/tool contract | I | I | R | A | C | C | C | C | C | I | C | C | C | I | I |
| Accept implementation task | I | C | A/R | C | R | C | C | C | I | I | I | I | I | I | I |
| Acceptance oracle/product sign-off | A | C | C | C | R | C | C | C | C | I | C | C | I | I | I |
| AI model/prompt/corpus promotion | C | I | R | C | C | A/R | C | C | C | I | I | C | I | C | I |
| Security finding severity/closure | I | I | R | C | C | C | A | C | C | I | I | I | I | I | I |
| Privacy/data transfer/retention | C | I | C | C | C | C | C | A/R | C | I | C | C | C | I | A for institutional data |
| Knowledge publish/retire | I | I | R | C | C | C | C | C | C | I | C | A/R | I | I | I |
| Support calendar/queue/training | C | I | C | I | C | C | C | C | C | I | A/R | I | I | I | C |
| Performance/capacity/SLO | I | C | R | C | R | C | C | I | A/R | C | C | I | C | C | I |
| Backup/restore/incident drill | I | I | R | C | C | I | C | C | A/R | C | I | I | C | I | I |
| Assemble release candidate/bundle | I | C | C | C | C | C | C | C | C | A/R | I | I | I | I | I |
| Gate decision per domain | C | I | C | C | A for quality | A for AI | A for security | A for privacy | A for ops | R/aggregate | C | C | C | C | I |
| Synthetic pilot go/no-go | A | R | C | C | approval | approval | approval | approval | approval | R | C | C | C | C | I |
| Production go/no-go | A | R | C | C | approval | approval | mandatory approval | mandatory approval | mandatory approval | R | mandatory approval | C | mandatory approval | mandatory approval | mandatory approval |
| Deployment execution | I | I | C | I | I | I | C | C | C | A/R | I | I | C | I | I |
| Activate containment/safe mode | I/C | I | C | I | I | C | A/R for security | A/R for privacy | A/R for reliability | R | I | I | I | I | I |
| Authorize recovery after SEV0/1 | C | I | C | C | C | C | A for security | A for privacy | A for ops | R | C | C | C | I | I |

`approval` means required sign-off but not sole accountability. There must be one named accountable owner in the operational registry; joint emergency containment rights do not mean ambiguous recovery approval.

## 3. Gate ownership

| Gate | A | R | Mandatory consulted/approval |
|---|---|---|---|
| GATE-REL-001 | PO/QE Governance | DL | ARCH, SEC for affected scope |
| GATE-REL-002 | ENG | component owners | QE, SEC supply chain |
| GATE-REL-003 | ARCH | contract/data owners | QE, SEC, AIQ as applicable |
| GATE-REL-004 | SEC/PRIV | Security QE | ARCH, REL |
| GATE-REL-005 | AIQ | AI QE | Product, SEC, KNOW |
| GATE-REL-006 | PO + QE | Acceptance QE | UX/SUP/domain owners |
| GATE-REL-007 | OPS | Performance QE | ARCH, FIN |
| GATE-REL-008 | OPS | SRE | REL, Data owner, SEC |
| GATE-REL-009 | OPS | SRE/Service owners | SEC, SUP, AIQ |
| GATE-REL-010 | PRIV/Test Data | Test Data owner | AIQ, KNOW, SEC |
| GATE-REL-011 | REL | Release Engineering | OPS, ARCH, QE |
| GATE-REL-012 | PO + UNI | REL/DL | all mandatory domain approvers |

## 4. Separation of duties

- Implementer/agent cannot approve its own security exception, critical gold-label change, production gate or destructive migration.
- Knowledge editor and publisher are separated where policy requires.
- Candidate builder and evidence/gate signer are distinct review passes.
- Operations may contain immediately; recovery after security/privacy incident requires respective owner.
- Product cannot accept risk owned by Security, Privacy, SRE or institutional Data Owner.

## 5. One-person project adaptation

While one human performs multiple roles, each decision record MUST name the role being exercised, use a separate review pass, record exact revision/evidence and disclose role conflict. For production, institutional/legal/security responsibilities cannot be simulated by an AI or collapsed into developer self-approval; unresolved roles remain launch blockers.
