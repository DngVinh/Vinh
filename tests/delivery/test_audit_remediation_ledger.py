"""Verify the audit remediation ledger in the markdown status document."""
from __future__ import annotations

import re
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
DOC_PATH = ROOT / "docs/10-delivery/AUDIT_REMEDIATION_STATUS_2026-09-27.md"
TASKS_DIR = ROOT / "tasks"

def parse_ledger() -> list[dict[str, str]]:
    """Parse the markdown table from the document."""
    content = DOC_PATH.read_text(encoding="utf-8")
    lines = content.splitlines()
    
    in_table = False
    headers = []
    rows = []
    
    for line in lines:
        line = line.strip()
        if not line:
            in_table = False
            continue
            
        if line.startswith("|") and "Finding ID" in line:
            in_table = True
            headers = [h.strip() for h in line.split("|")[1:-1]]
            continue
            
        if in_table and line.startswith("|") and "---" in line:
            continue
            
        if in_table and line.startswith("|"):
            values = [v.strip() for v in line.split("|")[1:-1]]
            if len(values) == len(headers):
                rows.append(dict(zip(headers, values)))
                
    return rows

def load_catalog_tasks() -> set[str]:
    """Load all valid task IDs from the catalog."""
    index = yaml.safe_load((TASKS_DIR / "task-index.yaml").read_text(encoding="utf-8"))
    ids = set()
    for phase in index.get("phases", []):
        for task in phase.get("tasks", []):
            ids.add(task["id"])
    for task in index.get("supplemental_tasks", []):
        ids.add(task["id"])
    return ids

def test_ledger_has_rows():
    rows = parse_ledger()
    assert len(rows) > 0, "Ledger table not found or empty"

def test_ledger_columns():
    rows = parse_ledger()
    if not rows:
        return
    expected_cols = {"Finding ID", "Type", "Severity", "Description", "Primary Task", "Supporting Tasks", "Wave", "Status", "Closure Evidence"}
    assert set(rows[0].keys()) == expected_cols

def test_unique_finding_ids():
    rows = parse_ledger()
    ids = [row["Finding ID"] for row in rows]
    duplicates = set(x for x in ids if ids.count(x) > 1)
    assert not duplicates, f"Duplicate finding IDs found: {duplicates}"

def test_types_and_severities():
    rows = parse_ledger()
    valid_types = {"observed fact", "inference", "unresolved question", "accepted risk"}
    valid_severities = {"critical", "high", "medium", "low"}
    
    for i, row in enumerate(rows):
        assert row["Type"].lower() in valid_types, f"Row {i} has invalid Type: {row['Type']}"
        assert row["Severity"].lower() in valid_severities, f"Row {i} has invalid Severity: {row['Severity']}"

def test_primary_and_supporting_tasks():
    rows = parse_ledger()
    catalog = load_catalog_tasks()
    
    for row in rows:
        primary = row["Primary Task"].strip().strip("`")
        assert primary, f"Finding {row['Finding ID']} has no primary task"
        assert primary in catalog, f"Finding {row['Finding ID']} has unknown primary task: {primary}"
        
        supporting = row["Supporting Tasks"]
        if supporting and supporting != "-":
            tasks = [t.strip().strip("`") for t in supporting.split(",")]
            for t in tasks:
                assert t in catalog, f"Finding {row['Finding ID']} has unknown supporting task: {t}"
                assert t != primary, f"Finding {row['Finding ID']} lists {t} as both primary and supporting"

def test_status_and_evidence():
    rows = parse_ledger()
    for row in rows:
        status = row["Status"].lower()
        assert status in {"open", "closed"}, f"Finding {row['Finding ID']} has invalid status: {status}"
        
        if status == "closed":
            evidence = row["Closure Evidence"]
            assert evidence and evidence != "-", f"Finding {row['Finding ID']} is closed but missing evidence"
