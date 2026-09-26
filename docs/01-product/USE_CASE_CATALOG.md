---
document_id: "DOC-PROD-UC-001"
version: "1.1.0"
status: "reviewed"
owner: "Product Management"
approvers: ["Product Owner", "Service Owner", "Architecture Owner"]
last_updated: "2026-09-22"
---

# Use case catalog

| ID | Priority | Actor | Outcome |
|---|---|---|---|
| UC-CHAT-001 | P0 | Student | Ask a policy/procedure question and receive a grounded answer with citations. |
| UC-CHAT-002 | P0 | Student | Receive an abstention/clarification when evidence is insufficient. |
| UC-CHAT-003 | P0 | Student | Receive one bounded clarification for an ambiguous supported intent, then a safe next step. |
| UC-CHAT-004 | P1 | Student | Rate an owned answer as helpful/not helpful with optional feedback tied to immutable answer metadata. |
| UC-AUTH-001 | P0 | User/System | Establish, derive and revoke a trusted server-side demo identity session; production disables demo shortcuts. |
| UC-SCHEDULE-001 | P0 | Student | View own upcoming schedule through an authorized read-only tool. |
| UC-TICKET-001 | P0 | Student | Preview, confirm and create a support ticket. |
| UC-TICKET-002 | P0 | Student | Track own ticket status and history. |
| UC-TICKET-003 | P0 | Student/System | Replay a confirmed ticket request safely and receive the original result without duplicate side effect. |
| UC-DOCREQ-001 | P1 | Student | Request a simulated student document through a confirmed workflow. |
| UC-DOC-001 | P0 | Student | Discover a versioned document-request catalog, cited conditions and request-only receipt. |
| UC-ROOM-001 | P1 | Student | Search room availability and submit a booking request after confirmation. |
| UC-ROOM-002 | P1 | Student | Resolve a room conflict or cancel an owned booking through preview and explicit confirmation. |
| UC-HITL-001 | P0 | Student | Ask to meet a human and enter the correct queue. |
| UC-HITL-002 | P0 | System/Staff | Detect a sensitive case and hand over with bounded context. |
| UC-HITL-003 | P0 | System/User | Safely disclose unavailable live handover/contact without inventing contact details. |
| UC-STAFF-001 | P0 | Support officer | Triage, assign, respond, transfer and resolve queued cases. |
| UC-STAFF-002 | P0 | Support officer | Transfer an authorized case while preserving immutable ownership, SLA and event history. |
| UC-KNOW-001 | P0 | Knowledge admin | Import and review a synthetic or approved source version. |
| UC-KNOW-002 | P0 | Knowledge admin | Publish/supersede a source and run regression evaluation. |
| UC-OPS-001 | P1 | Operations admin | Observe quality, latency, cost, queue and incident metrics. |
| UC-PRIV-001 | P1 | Student | View privacy information, stored conversation list and request deletion/export in simulation. |
| UC-GOV-001 | P0 | System/User | See the HUCE Demo unofficial-simulation disclaimer and synthetic provenance on every relevant surface. |

## Standard flow requirements

Every use case specifies authentication, authorization, input validation, audit, timeout, error state, retry behavior and telemetry. Write use cases additionally require preview, confirmation, expiry and idempotency. Sensitive use cases additionally require safe copy, handover reason and no fabricated contact information.
