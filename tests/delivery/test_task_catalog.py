from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[2]


def test_task_catalog_validator_runs_cleanly():
    """Verify tasks/tools/validate_catalog.py executes with exit code 0."""
    script = ROOT / "tasks" / "tools" / "validate_catalog.py"
    assert script.exists(), "validate_catalog.py must exist"

    env = dict(os.environ)
    env["PYTHONDONTWRITEBYTECODE"] = "1"

    result = subprocess.run(
        [sys.executable, str(script)],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        env=env,
    )
    assert result.returncode == 0, f"Validator failed with output:\n{result.stdout}\n{result.stderr}"
    assert "VALID tasks=" in result.stdout
    assert "PHASES P00=" in result.stdout


def test_validate_tasks_script_exists():
    """Verify platform preflight script is present."""
    ps_script = ROOT / "scripts" / "validate-tasks.ps1"
    assert ps_script.exists(), "scripts/validate-tasks.ps1 must exist"


def test_readiness_gates(tmp_path):
    """Test that missing dependencies, evidence, and approvals block readiness."""
    script = ROOT / "tasks" / "tools" / "validate_catalog.py"
    env = dict(os.environ)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    
    # Create a temporary ready task missing dependencies and approvals
    items_dir = ROOT / "tasks" / "items"
    dummy_task = items_dir / "TASK-DUMMY-999.yaml"
    
    task_content = {
        "schema_version": "1.1",
        "id": "TASK-DUMMY-999",
        "phase": "P00",
        "title": "Dummy",
        "status": "ready",
        "objective": "Dummy",
        "layer": "governance",
        "bounded_context": "dummy",
        "priority": "P0",
        "estimated_minutes": 30,
        "sensitivity": "low",
        "human_approval_required": True,
        "approval_reasons": [],
        "traceability": {
            "requirements": [],
            "design": [],
            "contracts": [],
            "controls": [],
            "evals": []
        },
        "dependencies": ["TASK-NONEXISTENT-999"],
        "inputs": [],
        "write_scope": {
            "allowed_paths": [],
            "forbidden_paths": [],
            "max_files": 1,
            "max_added_lines": 10
        },
        "preconditions": [],
        "steps": [],
        "acceptance_criteria": [],
        "verification": [],
        "evidence_required": [],
        "recovery": {
            "strategy": "reverse_patch",
            "steps": []
        },
        "stop_conditions": [],
        "parallelism": {
            "eligible": True,
            "conflict_keys": []
        },
        "execution_policy": {
            "max_fix_attempts": 2,
            "network_access": False,
            "paid_services": False,
            "destructive_operations": False
        }
    }
    
    try:
        dummy_task.write_text(yaml.safe_dump(task_content), encoding="utf-8")
        
        result = subprocess.run(
            [sys.executable, str(script)],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            env=env,
        )
        assert result.returncode == 1
        assert "Ready task has unresolved dependency" in result.stdout
        assert "Approval reason missing" in result.stdout
        assert "Ready task missing evidence_required" in result.stdout
        
    finally:
        if dummy_task.exists():
            dummy_task.unlink()
