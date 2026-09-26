import os
import subprocess
import pytest


def test_restore_script_file_exists_and_syntax():
    # AC-01: verify PowerShell restore script exists
    script_path = os.path.join(os.path.dirname(__file__), "..", "..", "scripts", "dr", "verify-postgres-restore.ps1")
    assert os.path.exists(script_path), f"Script not found at {script_path}"

    with open(script_path, "r", encoding="utf-8") as f:
        content = f.read()

    assert "[CmdletBinding()]" in content or "param(" in content
    assert "SnapshotId" in content
    assert "RTO" in content or "RPO" in content
    assert "pgvector" in content or "extension" in content


def test_restore_script_dry_run_execution():
    # AC-01: verify dry run execution succeeds with exit code 0
    script_path = os.path.join(os.path.dirname(__file__), "..", "..", "scripts", "dr", "verify-postgres-restore.ps1")

    cmd = [
        "powershell",
        "-ExecutionPolicy",
        "Bypass",
        "-File",
        script_path,
        "-SnapshotId",
        "snap-campus247-demo-001",
        "-ValidateOnly",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    assert result.returncode == 0
    assert "RESTORE_SIMULATION_OK" in result.stdout


def test_restore_script_missing_snapshot_failure():
    # AC-02: failure path - missing SnapshotId fails
    script_path = os.path.join(os.path.dirname(__file__), "..", "..", "scripts", "dr", "verify-postgres-restore.ps1")

    cmd = [
        "powershell",
        "-ExecutionPolicy",
        "Bypass",
        "-File",
        script_path,
        "-SnapshotId",
        "",
        "-ValidateOnly",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    assert result.returncode != 0
