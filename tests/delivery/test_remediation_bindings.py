"""Verify every remediation task is covered by at least one canonical requirement binding.

RED target: this test must fail before TASK-GOV-AUD-003 adds remediation tasks to bindings.
"""
from __future__ import annotations

import re
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
TASKS = ROOT / "tasks"


def _load(path: Path):
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def _remediation_task_ids() -> set[str]:
    """Return IDs listed in supplemental_tasks of task-index.yaml."""
    index = _load(TASKS / "task-index.yaml")
    return {entry["id"] for entry in index.get("supplemental_tasks", [])}


def _binding_task_coverage() -> dict[str, set[str]]:
    """Return {task_id: {req_ids}} from bindings file."""
    bindings = _load(TASKS / "requirement-acceptance-bindings.yaml")["bindings"]
    coverage: dict[str, set[str]] = {}
    for req_id, binding in bindings.items():
        for task_id in binding.get("tasks", []):
            coverage.setdefault(task_id, set()).add(req_id)
    return coverage


REQ_PATTERN = re.compile(r"^REQ-(F|NF)-[A-Z0-9-]+$")
AC_PATTERN = re.compile(r"^AC-REQ-(F|NF)-[A-Z0-9-]+$")


class TestRemediationBindings:
    """Every remediation (supplemental) task must appear in at least one canonical binding."""

    def test_every_remediation_task_has_binding(self):
        remediation_ids = _remediation_task_ids()
        coverage = _binding_task_coverage()
        uncovered = sorted(tid for tid in remediation_ids if tid not in coverage)
        assert uncovered == [], f"Remediation tasks missing from canonical bindings: {uncovered}"

    def test_binding_requirement_ids_match_output_schema_pattern(self):
        coverage = _binding_task_coverage()
        remediation_ids = _remediation_task_ids()
        bad: list[str] = []
        for tid in sorted(remediation_ids):
            req_ids = coverage.get(tid, set())
            for req_id in req_ids:
                if not REQ_PATTERN.match(req_id):
                    bad.append(f"{tid} -> {req_id}")
        assert bad == [], f"Requirement IDs not matching output pattern: {bad}"

    def test_remediation_task_has_at_least_one_ac_in_binding(self):
        """Each remediation task appears in at least one AC's task list."""
        bindings = _load(TASKS / "requirement-acceptance-bindings.yaml")["bindings"]
        remediation_ids = _remediation_task_ids()
        ac_covered: set[str] = set()
        for _req_id, binding in bindings.items():
            for _ac_id, ac_tasks in binding.get("acceptance_criteria", {}).items():
                for tid in ac_tasks:
                    if tid in remediation_ids:
                        ac_covered.add(tid)
        uncovered = sorted(remediation_ids - ac_covered)
        assert uncovered == [], f"Remediation tasks missing from AC bindings: {uncovered}"

    def test_existing_bindings_preserved(self):
        """Existing non-remediation task coverage is not removed."""
        bindings = _load(TASKS / "requirement-acceptance-bindings.yaml")["bindings"]
        remediation_ids = _remediation_task_ids()
        # Spot-check: known existing tasks must still appear
        known_existing = {
            "REQ-F-AUTH-001": {"TASK-API-IDENTITY-001", "TASK-API-IDENTITY-002"},
            "REQ-F-CHAT-001": {"TASK-API-CHAT-001", "TASK-WEB-CHAT-001"},
            "REQ-NF-SEC-001": {"TASK-INFRA-EDGE-001", "TASK-TEST-SEC-002"},
        }
        for req_id, expected_tasks in known_existing.items():
            actual = set(bindings[req_id]["tasks"])
            missing = expected_tasks - actual
            assert missing == set(), f"Existing tasks removed from {req_id}: {missing}"

    def test_supplemental_tasks_exist(self):
        """Sanity: supplemental_tasks list is non-empty."""
        ids = _remediation_task_ids()
        assert len(ids) >= 38, f"Expected >=38 remediation tasks, got {len(ids)}"
