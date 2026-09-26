---
document_id: "DOC-AGENT-005"
version: "1.0.0"
status: "reviewed"
owner: "Agentic Delivery Architecture"
approvers: ["Engineering Lead", "Security Owner"]
last_updated: "2026-09-22"
---

# Failure and escalation protocol

## Stop codes

Use one stable code: `SOURCE_NOT_APPROVED`, `SOURCE_CHANGED`, `MISSING_DEPENDENCY`, `MISSING_ARTIFACT`, `CONTRACT_MISMATCH`, `SCOPE_VIOLATION`, `WRITE_CONFLICT`, `APPROVAL_REQUIRED`, `UNAPPROVED_DEPENDENCY`, `SECURITY_DECISION_REQUIRED`, `DESTRUCTIVE_ACTION_REQUIRED`, `REAL_DATA_OR_SECRET_REQUIRED`, `PAID_SERVICE_REQUIRED`, `PRODUCTION_ACCESS_REQUIRED`, `VERIFICATION_UNAVAILABLE`, or `ACCEPTANCE_FAILED`.

## Escalation payload

Return the task-output schema with:

- exact blocker code and one-sentence summary;
- source IDs and path/line evidence;
- work safely completed before the blocker;
- changed files, if any;
- safe state of the repository/system;
- one to three bounded options;
- the exact decision or approval required.

Do not ask broad questions such as “what should I do?”. Never invent an answer to continue.

## Failure budget

Run a failing command once, diagnose from evidence, and attempt at most two distinct in-scope fixes. Repeating the same command without a state change does not count as progress. Infrastructure/network/transient failures may be retried only within the task's explicit policy.

## Sensitive escalation

Pause before any sensitive mutation. The human approval must identify task ID, target and effect. If target/scope changes after approval, approval is invalid and must be renewed.

