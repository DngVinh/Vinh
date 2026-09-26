---
document_id: "DOC-GOV-REVIEW-001"
version: "1.0.0"
status: "approved"
owner: "Documentation Chief Editor"
approvers: ["Product Owner", "Architecture Owner", "Security Owner", "AI Quality Owner"]
last_updated: "2026-09-21"
---

# Cross-review checklist

The chief editor applies this checklist after each documentation wave and before any task is marked `ready`.

## Product consistency

- V1 remains single-institution and does not introduce SaaS/multi-tenant requirements.
- Every capability belongs to the approved V1 scope or is explicitly future scope.
- KPI formulas define numerator, denominator, window, exclusions, data source and owner.
- Business promises do not exceed the approved service operating model.

## Architecture consistency

- Component ownership and trust boundaries are unambiguous.
- API, event, data and tool names match across documents.
- No LLM has direct database credentials or unrestricted tool access.
- Write operations share one confirmation and idempotency model.
- Failure and degraded modes exist for LLM, retrieval, Redis, database and integration outages.
- AWS design is implementable by the stated delivery model and has a lower-cost pilot profile.

## AI and knowledge consistency

- Retrieval uses official/approved source status, version and effective-date filters.
- Answer coverage is never treated as correctness.
- Evidence/citation failure leads to abstention or handover.
- Memory does not become an ungoverned knowledge source.
- Model routing cannot weaken safety, authorization or citation requirements.
- Eval datasets cover Vietnamese text, no-diacritic input, typos, adversarial prompts and multi-turn flows.

## Security and privacy consistency

- Simulation forbids real personal data.
- Identity is derived from trusted authentication context, not request-supplied user IDs.
- Every role and API has a least-privilege rule.
- Logs, traces, metrics and eval artifacts use the same redaction policy.
- External LLM calls pass through PII minimization and egress controls.
- No document claims legal or standards certification without evidence.

## Agent executability

- The atomic task references only approved artifacts.
- The objective is singular and measurable.
- Allowed and forbidden files are explicit.
- Dependencies are accepted and non-circular.
- Commands and expected exit codes are specified.
- Stop conditions prevent guessing and scope expansion.
- Completion output requires requirement-level evidence.
- Parallel tasks have disjoint write sets.

## Release readiness

- Contract, migration, security, AI eval, accessibility, load and recovery evidence are present.
- Rollback is executable and does not rely on destructive cleanup.
- Open questions that block real deployment remain visible.
- Documentation version and deployed artifact version are linked.

