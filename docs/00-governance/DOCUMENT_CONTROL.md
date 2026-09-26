---
document_id: "DOC-GOV-CONTROL-001"
version: "1.0.0"
status: "approved"
owner: "Documentation Chief Editor"
approvers: ["Product Owner", "Architecture Owner", "Security Owner", "Quality Owner"]
last_updated: "2026-09-22"
---

# Document control policy

## Purpose

This policy prevents human authors and implementation agents from producing contradictory behavior. Every normative artifact MUST have a stable ID, status, owner, review evidence and traceable downstream consumers.

## Artifact lifecycle

`draft -> reviewed -> approved -> superseded`

- `draft`: incomplete and not safe for implementation.
- `reviewed`: internally checked but not yet authoritative.
- `approved`: normative and may be referenced by `ready` tasks.
- `superseded`: retained for audit but no longer authoritative.

Atomic tasks use a separate lifecycle:

`draft -> reviewed -> ready -> in_progress -> verification -> accepted | blocked | failed`

Only the orchestrator or a human reviewer may set `ready` or `accepted`.

## Required document header

Every normative document MUST include:

```yaml
document_id: "DOC-..."
version: "x.y.z"
status: "draft|reviewed|approved|superseded"
owner: "role"
approvers: ["role"]
last_updated: "YYYY-MM-DD"
```

## Change classification

| Class | Examples | Approval |
|---|---|---|
| Editorial | Typo, formatting, non-normative clarification | Document owner |
| Compatible | New optional field, additional test, tighter explanation without behavior change | Owner plus affected engineering reviewer |
| Behavioral | Requirement, workflow, threshold, API or state change | Product/architecture approval and traceability update |
| Security/privacy | Authorization, identity, retention, encryption, data transfer | Security/privacy approval |
| Breaking | Contract removal, schema incompatibility, destructive migration | Formal change request, migration and rollback plan |

## Agent conflict policy

An agent MUST stop and emit a structured blocker when:

- referenced artifacts are missing or not approved;
- requirement and contract disagree;
- a dependency task is not accepted;
- the change requires files outside the task allowlist;
- a new dependency or architecture decision is necessary;
- verification cannot be performed as specified.

The agent MUST NOT resolve a normative conflict by guessing, silently broadening scope or weakening a test/control.
