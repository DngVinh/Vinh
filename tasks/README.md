# Campus 24/7 implementation task catalog

This directory is the machine-readable delivery plan from an empty implementation repository to a production-ready single-institution product.

## Files

- `task.schema.json` validates every `items/*.yaml` task.
- `task-output.schema.json` validates executor results.
- `task-index.yaml` is the ordered catalog.
- `dag.yaml` is the dependency graph and phase-gate view.
- `items/` contains one immutable file per micro-task.
- `templates/` and `examples/` support task authors.
- `tools/validate_catalog.py` validates YAML/JSON, schemas, references and cycles.
- `tools/generate_catalog.py` is the deterministic source used to materialize the initial catalog. It refuses to overwrite files.

## Workflow

1. Run `python tasks/tools/validate_catalog.py`.
2. Select a `ready` task whose dependencies are `accepted`.
3. Resolve and lease its write scope.
4. Dispatch it with the prompt in `docs/09-agent-execution/PROMPT_TEMPLATE.md`.
5. Validate the returned JSON against `task-output.schema.json`.
6. Review evidence and set `accepted` only outside the executor.

All initial tasks are `draft`. This is intentional: architecture, AI and security packages contain draft/reviewed sources that require human approval before implementation readiness.

## Phase map

| Phase | Outcome |
|---|---|
| P00 | normative readiness, dependency allowlist and repository skeleton |
| P01 | runnable local foundation and CI |
| P02 | data model, additive migrations and deterministic fixtures |
| P03 | identity, authorization, action control, audit and outbox |
| P04 | RAG, LLM gateway, controlled graph, memory and guardrails |
| P05 | backend vertical slices and APIs |
| P06 | accessible responsive web experiences |
| P07 | eval, security, integration and end-to-end quality gates |
| P08 | AWS IaC, observability, performance and recovery hardening |
| P09 | pilot, release candidate and human-gated production launch |

## Authoring rules

Copy the template; assign a never-reused ID; keep one objective; list exact dependencies; limit writes to three paths; provide positive and failure-path acceptance; use non-destructive recovery; and run the catalog validator. A changed task is a new reviewed version, not an undocumented edit after execution began.

