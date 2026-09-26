---
document_id: "DOC-AGENT-002"
version: "1.0.0"
status: "reviewed"
owner: "Agentic Delivery Architecture"
approvers: ["Engineering Lead", "Release Owner"]
last_updated: "2026-09-22"
---

# Orchestrator protocol

## Scheduling loop

1. Validate catalog, index, DAG, external reference registry and requirement/AC binding catalog.
2. Reconcile task status from the authoritative evidence store.
3. Compute candidates whose dependencies are `accepted`.
4. Remove candidates blocked by source status, approval, environment or open-question gates.
5. Resolve each candidate's path patterns and conflict keys.
6. Select up to four mutually disjoint tasks, preferring critical-path and P0 work.
7. Acquire leases for task ID, paths and conflict keys.
8. Resolve direct and/or canonical requirement/AC bindings, add the exact product source sections to the bounded context pack, then dispatch one task per executor.
9. On result, verify schema, scope, commands and evidence independently.
10. Mark `accepted`, request changes, or block; release leases in all terminal cases.

## State ownership

Only the orchestrator or authorized human may move `reviewed -> ready`, `verification -> accepted`, or grant a waiver. Executors may propose `in_progress`, `verification`, `blocked` or `failed` through task output.

## Context pack

The pack contains the task verbatim; root contract; referenced approved source excerpts or complete files; dependency outputs; repository status; exact source revision; allowed path list; available commands; and approval record. It excludes unrelated docs, secrets, sealed eval answers and previous agents' speculation.

The pack also contains a machine-readable `upstream_traceability` object resolved from `tasks/requirement-acceptance-bindings.yaml`. For direct links it validates that every direct requirement and AC is a subset of the canonical entry. For canonical links it includes the bound task's requirements and ACs. The orchestrator rejects missing, stale or conflicting bindings before assigning a lease.

## Review gates

Before acceptance, confirm:

- changed files are a subset of resolved scope;
- no pre-existing user change was overwritten;
- all acceptance IDs passed;
- required negative/failure-path tests ran;
- traceability IDs are valid;
- direct and canonical requirement/AC bindings agree and are represented in executor output;
- evidence artifacts exist and contain no secret/PII;
- residual risks are explicit;
- contract/security/architecture changes were not smuggled into code.

## Retry and reassignment

An executor gets at most two materially different repair attempts. Reassignment preserves the original task and evidence; it does not reset the retry counter. Split or revise a task only through review, producing a new immutable task version.
