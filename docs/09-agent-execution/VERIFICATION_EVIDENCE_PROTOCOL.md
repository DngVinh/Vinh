---
document_id: "DOC-AGENT-006"
version: "1.0.0"
status: "reviewed"
owner: "Quality Architecture"
approvers: ["Quality Owner", "Security Owner", "Release Owner"]
last_updated: "2026-09-22"
---

# Verification and evidence protocol

## Evidence hierarchy

Prefer, in order: deterministic automated test; contract/schema validator; static/architecture check; reproducible integration/e2e test; generated report with raw inputs; scoped manual review. Narrative alone is never proof of a deterministic criterion.

## Command evidence

For each command record working directory, exact sanitized command, start/end time, exit code, concise output summary and artifact paths. Expected exit code must match the task. Never include secret values or raw personal content.

## Acceptance mapping

Every `acceptance_criteria[].id` must have exactly one result entry: `passed`, `failed` or `not_verified`. `not_verified` blocks completion. Evidence must show the behavior, including required negative and failure paths.

The task output also records the resolved product requirement/AC set. Task-local acceptance IDs prove the micro-task; product AC IDs establish why the micro-task exists. A reviewer rejects an output when either set is absent, mismatched with the binding catalog, or lacks evidence appropriate to the claimed product behavior.

## Scope evidence

Capture initial/final `git status --short`, changed-file list and diff statistics. Confirm all changes belong to the task and identify pre-existing changes without modifying them.

## Artifact integrity

Reports and snapshots include source revision, task ID, generator/tool versions and SHA-256 when retained for release. Large artifacts stay outside Git at approved immutable storage; repository evidence stores a manifest and checksum.

## Independent acceptance

The reviewer reruns critical checks or validates immutable CI artifacts. Security, auth, migration, AI hard gates, restore, load and production evidence require the reviewer role specified by their governing source.
