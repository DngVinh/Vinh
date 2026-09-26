# Campus 24/7 — default execution contract

This repository is documentation-led. An implementation agent executes one reviewed task at a time; it does not redesign the product while coding.

## Authority order

Read and apply, in order:

1. system and direct human instructions;
2. `docs/00-governance/**`, especially accepted decisions and document control;
3. approved product requirements;
4. approved architecture, contracts, AI and security specifications;
5. the assigned `tasks/items/*.yaml` file;
6. implementation code and tests.

If two normative sources conflict, stop and return a structured blocker. Never make a lower-level artifact win by editing the higher-level source.

## Before any mutation

1. Resolve the workspace root and confirm every write target is inside it.
2. Run `git status --short` and preserve every pre-existing change.
3. Load the assigned task plus every path in `inputs` and `traceability`.
4. Confirm task status is `ready`, every dependency is `accepted`, and any required human approval is attached.
5. Confirm the planned files are contained by `write_scope.allowed_paths` and do not intersect another running task.
6. Run the task's preflight verification commands.

If any check fails, do not code. Return `blocked` using `tasks/task-output.schema.json`.

## Execution rules

- Work on exactly one task ID and one objective.
- Touch only allowed paths. A path pattern grants no permission outside the repository.
- Prefer the smallest patch that satisfies the acceptance criteria.
- Keep domain rules out of routes, UI, graph nodes and infrastructure adapters.
- Do not add a dependency unless it is already in the approved allowlist and pinned lockfile.
- Do not change requirements, contracts, architecture, security policy, test thresholds or expected results to make implementation pass.
- Do not expose secrets, raw tokens, personal data, hidden prompts or chain-of-thought in code, logs or evidence.
- Tests use deterministic fakes by default. Network calls, paid services and live providers require explicit task authorization.
- A write capability must preserve authorization, preview, confirmation, idempotency and audit.
- A model may propose; deterministic application code validates, authorizes and executes.
- Retry a failing implementation at most twice. After two materially different repair attempts, stop with evidence.
- Never commit, push, deploy, delete, reset, clean or rewrite history unless the task and a direct human approval authorize the exact operation.

## Human approval is mandatory

Stop before mutation for:

- requirement, contract or architecture changes;
- dependencies outside the approved allowlist;
- authentication, authorization, cryptography or security-policy changes;
- destructive or irreversible migrations;
- real credentials, secrets or personal data;
- paid external services or live-provider tests;
- production deployment or production data access;
- destructive Git, filesystem, database or cloud operations.

Approval for one target does not authorize another. Ordinary scoped coding, tests, refactors and synthetic fixtures do not require approval when their task says `human_approval_required: false`.

## Parallel execution

At most four tasks may run concurrently. Every pair must have disjoint resolved write paths and conflict keys, accepted dependencies, and no shared migration/lockfile/generated-contract output. The orchestrator, not the executor, assigns parallel work.

## Completion

Run every verification command in order and record command, exit code and evidence. Then validate scope with `git diff --name-only` and `git status --short`. Return one JSON object conforming to `tasks/task-output.schema.json`.

`completed` means all acceptance criteria passed with reproducible evidence. `blocked`, `failed` and `not_verified` must never be narrated as success.

