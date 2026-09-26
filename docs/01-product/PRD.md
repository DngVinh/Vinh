---
document_id: "DOC-PROD-PRD-001"
version: "1.0.0"
status: "approved"
owner: "Product Management"
approvers: ["Product Owner", "Architecture Owner", "Security Owner", "AI Quality Owner"]
last_updated: "2026-09-21"
---

# Product Requirements Document

## Product summary

Campus 24/7 provides grounded information and controlled student-service workflows for one university. HUCE Demo uses only synthetic operational/personal data and visibly identifies itself as unofficial.

## Target users

See `PERSONAS_AND_ROLES.md`. V1 supports students, support officers, knowledge administrators and system/operations administrators.

## Capabilities

### Grounded assistance

The system retrieves only approved/current sources, combines lexical and semantic retrieval, reranks candidates, validates evidence and generates claim-level citations. It must abstain or hand over when evidence is insufficient.

### Personal read tools

After authentication and authorization, the system may read the current student's synthetic schedule and own ticket data. Identity always comes from trusted auth context.

### Controlled write tools

Ticket, document request and room booking flows produce an immutable preview, request explicit confirmation and execute exactly once under a valid authorization decision.

### Human service

Users may request human help. Safety classifiers and deterministic rules can force handover. Staff receive bounded context, evidence and routing reason in an auditable queue.

### Governance and operations

Knowledge admins manage source lifecycle. Operations admins view quality, reliability and cost signals, manage safe configuration and activate degraded modes.

## Product invariants

1. No policy/procedure assertion without citation.
2. No write action without confirmation and idempotency.
3. No object access based only on a client-provided user identifier.
4. No direct model access to databases, secrets or arbitrary network/code execution.
5. No real personal data in simulation.
6. No fabricated emergency contact or claim of human response.
7. No release after a failed P0 security or AI quality gate.

## Detailed requirements

`requirements.yaml` is the machine-readable normative catalog. Design and tasks MUST reference its IDs rather than restating altered behavior.

## Dependencies

- Knowledge answers depend on source governance, retrieval contracts and eval data.
- Every tool depends on identity, authorization, audit and error contracts.
- Every write tool additionally depends on action preview, confirmation and idempotency.
- HITL depends on queue state machine and service operating rules.
- Dashboards depend on stable event/metric definitions and redaction.

## Acceptance

V1 is acceptable only when all P0 requirements and gates pass, documentation traceability has no orphan IDs, backup restore and rollback are demonstrated, and open real-deployment questions remain explicitly blocked rather than silently assumed.

