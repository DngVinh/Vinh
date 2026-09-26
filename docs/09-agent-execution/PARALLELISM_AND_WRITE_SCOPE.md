---
document_id: "DOC-AGENT-008"
version: "1.0.0"
status: "reviewed"
owner: "Agentic Delivery Architecture"
approvers: ["Engineering Lead", "Release Owner"]
last_updated: "2026-09-22"
---

# Parallelism and write-scope protocol

## Maximum concurrency

The repository-wide maximum is four executing tasks. Lower it when migrations, generated contracts, lockfiles, shared snapshots or environment capacity create serialization needs.

## Conflict test

Two tasks may run together only when:

1. all dependencies are accepted;
2. resolved allowed paths do not overlap and neither path is an ancestor of the other;
3. conflict-key sets are disjoint;
4. neither modifies a lockfile, migration head, generated client, shared index, root config or release manifest used by the other;
5. neither consumes an unaccepted output from the other;
6. the combined work does not require one shared mutable external environment.

Read overlap is allowed. Write overlap is not negotiated between executors.

## Leases

The orchestrator acquires leases for exact task ID, canonical paths and conflict keys. A lease records owner, source revision, start, expiry and heartbeat. Expired work is inspected before reassignment; another agent must not overwrite partial changes.

## Scope patterns

Allowed paths are repository-relative files or narrow directory patterns. They do not authorize deletion, moving, generated output outside the pattern, parent traversal, workspace root mutation or following a symlink outside the repository.

## Common serialization keys

Use `root-config`, `python-lock`, `web-lock`, `db-migration-head`, `openapi-generated`, `asyncapi-generated`, `task-catalog`, `shared-snapshots`, `cdk-context`, `release-manifest`, and environment keys such as `staging-deploy` or `production-deploy`.

