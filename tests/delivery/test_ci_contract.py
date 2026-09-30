import sys
from pathlib import Path
import pytest
import yaml

repo_root = str(Path(__file__).resolve().parents[2])
if repo_root not in sys.path:
    sys.path.insert(0, repo_root)

from scripts.verify_ci_contract import verify_ci_workflow, load_ci_workflow


def test_ci_workflow_meets_governance_contract():
    is_valid, errors = verify_ci_workflow()
    assert is_valid is True, f"CI workflow contract failed: {errors}"
    assert len(errors) == 0


def test_ci_rejects_allow_failure_or_continue_on_error():
    sample_workflow = {
        "name": "Compromised CI",
        "jobs": {
            "critical_gate": {
                "runs-on": "ubuntu-latest",
                "continue-on-error": True,
                "steps": [{"run": "echo bypass"}]
            }
        }
    }
    is_valid, errors = verify_ci_workflow(sample_workflow)
    assert is_valid is False
    assert any("continue-on-error" in err.lower() for err in errors)


def test_ci_rejects_live_provider_secrets():
    sample_workflow = {
        "name": "Leaky CI",
        "jobs": {
            "test_job": {
                "runs-on": "ubuntu-latest",
                "env": {
                    "OPENAI_API_KEY": "${{ secrets.PROD_OPENAI_KEY }}"
                },
                "steps": [{"run": "pytest"}]
            }
        }
    }
    is_valid, errors = verify_ci_workflow(sample_workflow)
    assert is_valid is False
    assert any("live provider secret" in err.lower() or "openai_api_key" in err.lower() for err in errors)


def test_ci_requires_all_core_remediation_gates():
    workflow = load_ci_workflow()
    jobs = workflow.get("jobs", {})
    required_jobs = ["catalog-validation", "backend-tests", "web-tests", "ai-eval-gates"]
    for rj in required_jobs:
        assert rj in jobs, f"CI missing required gate job: {rj}"
