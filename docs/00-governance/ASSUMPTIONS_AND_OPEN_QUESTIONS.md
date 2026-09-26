---
document_id: "DOC-GOV-ASSUMPTIONS-001"
version: "1.0.0"
status: "approved"
owner: "Documentation Chief Editor"
approvers: ["Product Owner", "Architecture Owner", "Security Owner"]
last_updated: "2026-09-22"
---

# Assumptions and open questions

## Accepted planning assumptions

| ID | Assumption | Validation point |
|---|---|---|
| ASM-001 | Pilot capacity is 5,000 student accounts, 100 staff accounts and 200 concurrent users. | Revisit after load-test results or a real institutional agreement. |
| ASM-002 | Expected peak demand is 10,000 chat requests/day and 1,000 ticket actions/day. | Revisit after telemetry from the first pilot. |
| ASM-003 | Initial knowledge volume is 150-300 documents and up to 100,000 parsed pages/chunks for stress testing. | Tune index and ingestion limits through performance tests. |
| ASM-004 | User-facing language is Vietnamese; English localization is future scope. | Product review before public pilot. |
| ASM-005 | Web responsive/PWA is sufficient for V1; native mobile applications are future scope. | Product roadmap review. |
| ASM-006 | AI and read-only services target 99.9% monthly availability; RPO is 15 minutes and RTO is 60 minutes. | Architecture and cost review. |
| ASM-007 | Conversation retention defaults to 90 days in simulation and remains configurable. | Privacy review before use of real personal data. |
| ASM-008 | Staff operate during published business hours; 24/7 AI does not imply 24/7 human staffing. | Service owner must provide actual schedules before pilot. |
| ASM-009 | Critical events are queued within 5 seconds; human response targets cannot be promised until a staffed operating model is approved. | Service design approval. |
| ASM-010 | WCAG 2.2 AA is the accessibility target. | UX and accessibility review. |

## Blocking questions before real-data or production launch

These questions do not block documentation or simulated implementation, but they block launch with real users or data.

| ID | Question | Required owner |
|---|---|---|
| OQ-001 | Who is the university Product Owner and final business approver? | University sponsor |
| OQ-002 | Who owns student data and approves each integration? | Data owner |
| OQ-003 | Which official emergency contacts, messages and staffed hours are approved? | Student affairs/security |
| OQ-004 | Which identity provider tenant, claims and group mappings will be used? | Identity administrator |
| OQ-005 | What are the legal conditions for sending any personal data to an external LLM provider? | Privacy/legal owner |
| OQ-006 | What are the contractual retention and deletion periods for chat, tickets and audit records? | Records/privacy owner |
| OQ-007 | What are the real SIS, LMS, ticketing and room-booking APIs and sandbox limits? | Integration owners |
| OQ-008 | What monthly AWS and LLM budget is approved? | Product/finance owner |
