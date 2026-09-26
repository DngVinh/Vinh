from __future__ import annotations

import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_task_catalog_validator_runs_cleanly():
    """Verify tasks/tools/validate_catalog.py executes with exit code 0."""
    script = ROOT / "tasks" / "tools" / "validate_catalog.py"
    assert script.exists(), "validate_catalog.py must exist"

    import os
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
    assert "VALID tasks=176" in result.stdout
    assert "PHASES P00=10" in result.stdout


def test_validate_tasks_script_exists():
    """Verify platform preflight script is present."""
    ps_script = ROOT / "scripts" / "validate-tasks.ps1"
    assert ps_script.exists(), "scripts/validate-tasks.ps1 must exist"
