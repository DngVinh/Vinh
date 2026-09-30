from __future__ import annotations

import json
import sys
from collections import Counter, defaultdict, deque
from pathlib import Path

import jsonschema
import yaml


ROOT = Path(__file__).resolve().parents[2]
TASKS = ROOT / "tasks"
ITEMS = TASKS / "items"


def load_yaml(path: Path):
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def frontmatter_status(path: Path) -> str | None:
    if path.suffix.lower() not in {".md", ".markdown"}:
        return None
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        return None
    end = text.find("\n---", 4)
    if end < 0:
        return None
    data = yaml.safe_load(text[4:end]) or {}
    return data.get("status")


def validate_traceability(tasks: dict[str, dict], errors: list[str]) -> None:
    product = load_yaml(ROOT / "docs/01-product/requirements.yaml")
    requirements = {item["id"]: item for item in product["requirements"]}
    ac_owner = {ac["id"]: req_id for req_id, item in requirements.items() for ac in item["acceptance_criteria"]}
    bindings = load_yaml(TASKS / "requirement-acceptance-bindings.yaml")["bindings"]
    registry = load_yaml(TASKS / "traceability-registry.yaml")["registries"]
    for category in ("design", "contracts", "controls", "evals"):
        for source in registry[category]["source_paths"]:
            if not (ROOT / source).exists():
                errors.append(f"Missing registry source path: {category} -> {source}")
    if set(bindings) != set(requirements):
        errors.append(f"Requirement binding mismatch: missing={sorted(set(requirements)-set(bindings))}, extra={sorted(set(bindings)-set(requirements))}")
    covered_tasks: set[str] = set()
    covered_acs: set[str] = set()
    for req_id, binding in bindings.items():
        task_ids = set(binding.get("tasks", []))
        if not task_ids:
            errors.append(f"Uncovered requirement: {req_id}")
        if not task_ids.issubset(tasks):
            errors.append(f"Binding unknown task: {req_id} -> {sorted(task_ids-set(tasks))}")
        covered_tasks.update(task_ids)
        bound_acs = binding.get("acceptance_criteria", {})
        expected = {ac["id"] for ac in requirements[req_id]["acceptance_criteria"]} if req_id in requirements else set()
        if set(bound_acs) != expected:
            errors.append(f"Binding AC mismatch: {req_id}")
        for ac_id, ac_tasks in bound_acs.items():
            if ac_owner.get(ac_id) != req_id:
                errors.append(f"AC owner mismatch: {req_id} -> {ac_id}")
            if not ac_tasks or not set(ac_tasks).issubset(tasks):
                errors.append(f"AC task coverage invalid: {ac_id}")
            covered_acs.add(ac_id)
    if set(ac_owner) != covered_acs:
        errors.append(f"Acceptance coverage mismatch: missing={sorted(set(ac_owner)-covered_acs)}")
    direct: dict[str, set[str]] = defaultdict(set)
    for task_id, task in tasks.items():
        trace = task.get("traceability", {})
        for category in ("design", "contracts", "controls", "evals"):
            known = set(registry[category]["ids"]) | set(registry[category].get("aliases", {}))
            unknown = set(trace.get(category, [])) - known
            if unknown:
                errors.append(f"Unknown {category} ID: {task_id} -> {sorted(unknown)}")
        reqs, acs = set(trace.get("requirements", [])), set(trace.get("acceptance_criteria", []))
        is_direct = bool(trace.get("acceptance_criteria") or trace.get("binding_mode") or trace.get("coverage_binding_ref"))
        if is_direct:
            if trace.get("binding_mode") not in {"direct", "mixed"} or trace.get("coverage_binding_ref") != "tasks/requirement-acceptance-bindings.yaml":
                errors.append(f"Direct trace metadata invalid: {task_id}")
            for req_id in reqs:
                direct[req_id].add(task_id)
                if req_id not in requirements or task_id not in bindings.get(req_id, {}).get("tasks", []):
                    errors.append(f"Direct requirement binding mismatch: {task_id} -> {req_id}")
            for ac_id in acs:
                if ac_owner.get(ac_id) not in reqs or task_id not in bindings.get(ac_owner[ac_id], {}).get("acceptance_criteria", {}).get(ac_id, []):
                    errors.append(f"Direct AC binding mismatch: {task_id} -> {ac_id}")
        if task.get("status") == "ready":
            for input_spec in task.get("inputs", []):
                status = frontmatter_status(ROOT / input_spec["path"])
                if status not in {"approved", "accepted"}:
                    errors.append(f"Ready task uses non-approved input: {task_id} -> {input_spec['path']} ({status})")
        allowed = task.get("write_scope", {}).get("allowed_paths", [])
        forbidden = task.get("write_scope", {}).get("forbidden_paths", [])
        if any(not p or p.startswith(("/", "\\")) or ":" in p or ".." in Path(p).parts for p in allowed + forbidden):
            errors.append(f"Unsafe write scope path: {task_id}")
        if set(allowed) & set(forbidden) or len(allowed) != len(set(allowed)):
            errors.append(f"Invalid write scope overlap: {task_id}")
    high_risk = [req_id for req_id, item in requirements.items() if item["metadata"]["priority"] == "P0" and any(token in req_id for token in ("-AUTH-", "-KNOW-", "-STAFF-", "-PRIV-"))]
    nfr = [req_id for req_id in requirements if req_id.startswith("REQ-NF-")]
    for req_id in high_risk + nfr:
        if not direct.get(req_id):
            errors.append(f"Required direct task trace missing: {req_id}")


def main() -> int:
    errors: list[str] = []

    for path in sorted(TASKS.rglob("*.json")):
        try:
            json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:  # validation tool must report every file
            errors.append(f"JSON parse: {path.relative_to(ROOT)}: {exc}")

    for path in sorted(TASKS.rglob("*.yaml")):
        try:
            load_yaml(path)
        except Exception as exc:
            errors.append(f"YAML parse: {path.relative_to(ROOT)}: {exc}")

    schema = json.loads((TASKS / "task.schema.json").read_text(encoding="utf-8"))
    validator = jsonschema.Draft202012Validator(schema, format_checker=jsonschema.FormatChecker())
    tasks: dict[str, dict] = {}
    item_paths: dict[str, str] = {}

    sample_paths = [TASKS / "templates" / "task-template.yaml", *sorted((TASKS / "examples").glob("*.yaml"))]
    for path in sample_paths:
        sample = load_yaml(path)
        issues = sorted(validator.iter_errors(sample), key=lambda error: list(error.path))
        for issue in issues:
            location = ".".join(str(part) for part in issue.path) or "$"
            errors.append(f"Sample schema: {path.relative_to(ROOT)}:{location}: {issue.message}")

    for path in sorted(ITEMS.glob("*.yaml")):
        try:
            task = load_yaml(path)
        except Exception:
            continue
        issues = sorted(validator.iter_errors(task), key=lambda error: list(error.path))
        for issue in issues:
            location = ".".join(str(part) for part in issue.path) or "$"
            errors.append(f"Schema: {path.relative_to(ROOT)}:{location}: {issue.message}")
        task_id = task.get("id")
        if task_id in tasks:
            errors.append(f"Duplicate task id: {task_id}")
        tasks[task_id] = task
        item_paths[task_id] = path.relative_to(ROOT).as_posix()
        if path.stem != task_id:
            errors.append(f"Filename/id mismatch: {path.name} != {task_id}.yaml")
        for input_spec in task.get("inputs", []):
            input_path = ROOT / input_spec["path"]
            if not input_path.exists():
                errors.append(f"Missing input path: {task_id} -> {input_spec['path']}")
        allowed = task.get("write_scope", {}).get("allowed_paths", [])
        if len(allowed) > task.get("write_scope", {}).get("max_files", 0):
            errors.append(f"Scope count exceeds max_files: {task_id}")
        if task.get("estimated_minutes", 0) < 15 or task.get("estimated_minutes", 0) > 45:
            errors.append(f"Estimate outside 15-45 minutes: {task_id}")

    for task_id, task in tasks.items():
        for dependency in task.get("dependencies", []):
            if dependency not in tasks:
                errors.append(f"Missing dependency: {task_id} -> {dependency}")

    ready_tasks = {tid: t for tid, t in tasks.items() if t.get("status") == "ready" and not (ITEMS / f"{tid}-output.json").exists()}
    for tid, t in ready_tasks.items():
        # 1. Unresolved task dependencies (all dependencies must have output JSON OR status accepted)
        for dep in t.get("dependencies", []):
            dep_output = ITEMS / f"{dep}-output.json"
            dep_status = tasks.get(dep, {}).get("status")
            if not dep_output.exists() and dep_status != "accepted":
                errors.append(f"Ready task has unresolved dependency: {tid} -> {dep}")
        # 2. Approval-reason mismatches
        req_approval = bool(t.get("human_approval_required"))
        reasons = t.get("approval_reasons", [])
        if req_approval and not reasons:
            errors.append(f"Approval reason missing for task requiring approval: {tid}")
        if not req_approval and reasons:
            errors.append(f"Approval reason provided for task not requiring approval: {tid}")
        # 3. Missing evidence mappings
        if not t.get("evidence_required"):
            errors.append(f"Ready task missing evidence_required mappings: {tid}")
    
    # 4. Scope overlap among ready tasks
    ready_task_ids = sorted(ready_tasks.keys())
    for i in range(len(ready_task_ids)):
        for j in range(i + 1, len(ready_task_ids)):
            t1 = ready_task_ids[i]
            t2 = ready_task_ids[j]
            t1_allowed = set(ready_tasks[t1].get("write_scope", {}).get("allowed_paths", []))
            t2_allowed = set(ready_tasks[t2].get("write_scope", {}).get("allowed_paths", []))
            if t1_allowed & t2_allowed:
                errors.append(f"Ready task write scope overlap: {t1} and {t2} share {t1_allowed & t2_allowed}")

    indegree = {task_id: 0 for task_id in tasks}
    children: dict[str, list[str]] = defaultdict(list)
    for task_id, task in tasks.items():
        for dependency in task.get("dependencies", []):
            indegree[task_id] += 1
            children[dependency].append(task_id)
    queue = deque(sorted(task_id for task_id, degree in indegree.items() if degree == 0))
    visited: list[str] = []
    while queue:
        current = queue.popleft()
        visited.append(current)
        for child in children[current]:
            indegree[child] -= 1
            if indegree[child] == 0:
                queue.append(child)
    if len(visited) != len(tasks):
        cycle_nodes = sorted(task_id for task_id, degree in indegree.items() if degree > 0)
        errors.append(f"Dependency cycle detected: {cycle_nodes}")

    index = load_yaml(TASKS / "task-index.yaml")
    dag = load_yaml(TASKS / "dag.yaml")
    index_ids = [entry["id"] for phase in index["phases"] for entry in phase["tasks"]] + [entry["id"] for entry in index.get("supplemental_tasks", [])]
    dag_ids = [node["id"] for node in dag["nodes"]]
    for label, ids in (("index", index_ids), ("dag", dag_ids)):
        duplicates = sorted(key for key, count in Counter(ids).items() if count > 1)
        if duplicates:
            errors.append(f"Duplicate {label} ids: {duplicates}")
        if set(ids) != set(tasks):
            errors.append(f"{label} mismatch: missing={sorted(set(tasks)-set(ids))}, extra={sorted(set(ids)-set(tasks))}")
    if dag.get("max_parallel_tasks") != 4:
        errors.append("DAG max_parallel_tasks must equal 4")
    for node in dag["nodes"]:
        if node["dependencies"] != tasks[node["id"]]["dependencies"]:
            errors.append(f"DAG dependency mismatch: {node['id']}")

    output_schema = json.loads((TASKS / "task-output.schema.json").read_text(encoding="utf-8"))
    jsonschema.Draft202012Validator.check_schema(schema)
    jsonschema.Draft202012Validator.check_schema(output_schema)
    validate_traceability(tasks, errors)

    if errors:
        for error in errors:
            print(f"ERROR {error}")
        print(f"FAILED errors={len(errors)} tasks={len(tasks)}")
        return 1
    phase_counts = Counter(task["phase"] for task in tasks.values())
    approval_count = sum(bool(task["human_approval_required"]) for task in tasks.values())
    print(f"VALID tasks={len(tasks)} phases={len(phase_counts)} approval_required={approval_count}")
    print("PHASES " + " ".join(f"{phase}={phase_counts[phase]}" for phase in sorted(phase_counts)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
