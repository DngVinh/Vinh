"""Unit tests for offline fake-provider evaluation runner (TASK-EVAL-RUNNER-001)."""

from pathlib import Path
import pytest
import yaml
from packages.evals.src.runner import EvalRunner, RunConfig
from packages.evals.src.validate import validate_result

DATASETS_DIR = Path(__file__).resolve().parents[1] / "datasets"


def load_dataset(filename: str) -> list[dict]:
    path = DATASETS_DIR / filename
    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def test_runner_executes_rag_cases():
    cases = load_dataset("rag-dev.yaml")
    runner = EvalRunner(config=RunConfig(environment="local_fake"))
    results = runner.run_suite(cases)

    assert len(results) == len(cases)
    for result in results:
        assert validate_result(result) is True
        assert result["status"] == "passed"
        assert len(result["assertion_results"]) >= 1


def test_runner_executes_safety_and_red_team():
    safety_cases = load_dataset("safety-dev.yaml")
    red_cases = load_dataset("red-team-dev.yaml")
    runner = EvalRunner(config=RunConfig(environment="local_fake"))
    results = runner.run_suite(safety_cases + red_cases)

    assert len(results) == len(safety_cases) + len(red_cases)
    for r in results:
        assert validate_result(r) is True
        assert r["status"] == "passed"


def test_runner_assertion_failure():
    cases = load_dataset("rag-dev.yaml")
    tampered_case = dict(cases[0])
    tampered_case["assertions"] = [
        {"assertion_id": "A-01", "kind": "route_is", "target": "route", "expected": "wrong_route"}
    ]
    runner = EvalRunner(config=RunConfig(environment="local_fake"))
    results = runner.run_suite([tampered_case])

    assert len(results) == 1
    assert results[0]["status"] == "failed"
    assert "ASSERTION_FAILED" in results[0]["failure_codes"]
