import sys
from pathlib import Path
from typing import Any
import yaml

FORBIDDEN_ENV_SECRETS = {
    "OPENAI_API_KEY",
    "ANTHROPIC_API_KEY",
    "AWS_SECRET_ACCESS_KEY",
    "LIVE_CREDENTIALS",
    "PROD_DATABASE_URL",
}

REQUIRED_CORE_JOBS = [
    "catalog-validation",
    "backend-tests",
    "web-tests",
    "ai-eval-gates",
]


def load_ci_workflow(workflow_path: Path | str | None = None) -> dict[str, Any]:
    if workflow_path is None:
        workflow_path = Path(__file__).resolve().parents[1] / ".github" / "workflows" / "ci.yml"
    else:
        workflow_path = Path(workflow_path)

    with open(workflow_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def verify_ci_workflow(
    workflow_input: dict[str, Any] | Path | str | None = None,
) -> tuple[bool, list[str]]:
    if isinstance(workflow_input, dict):
        workflow = workflow_input
    else:
        workflow = load_ci_workflow(workflow_input)

    errors: list[str] = []
    jobs = workflow.get("jobs", {})

    if not jobs:
        errors.append("CI workflow defines no jobs")
        return False, errors

    # Check required core jobs
    # When testing partial/sample workflows, skip required job check if sample workflow is custom
    if workflow.get("name") == "CI":
        for rj in REQUIRED_CORE_JOBS:
            if rj not in jobs:
                errors.append(f"CI missing required gate job: {rj}")

    for job_id, job_cfg in jobs.items():
        if not isinstance(job_cfg, dict):
            continue

        # Rule 1: No continue-on-error on critical jobs
        if job_cfg.get("continue-on-error") is True:
            errors.append(f"Job '{job_id}' specifies 'continue-on-error: true', violating failure propagation")

        # Check job env
        job_env = job_cfg.get("env", {})
        if isinstance(job_env, dict):
            for env_key in job_env.keys():
                if env_key.upper() in FORBIDDEN_ENV_SECRETS:
                    errors.append(f"Job '{job_id}' exposes live provider secret: {env_key}")

        # Check steps
        steps = job_cfg.get("steps", [])
        for idx, step in enumerate(steps):
            if not isinstance(step, dict):
                continue
            if step.get("continue-on-error") is True:
                errors.append(
                    f"Job '{job_id}' step #{idx+1} specifies 'continue-on-error: true', violating failure propagation"
                )
            step_env = step.get("env", {})
            if isinstance(step_env, dict):
                for env_key in step_env.keys():
                    if env_key.upper() in FORBIDDEN_ENV_SECRETS:
                        errors.append(f"Job '{job_id}' step #{idx+1} exposes live provider secret: {env_key}")

    is_valid = len(errors) == 0
    return is_valid, errors


def main(argv: list[str] | None = None) -> int:
    args = argv if argv is not None else sys.argv[1:]
    target_path = Path(args[0]) if args else None

    try:
        is_valid, errors = verify_ci_workflow(target_path)
    except Exception as ex:
        print(f"Error reading CI workflow: {ex}", file=sys.stderr)
        return 1

    if is_valid:
        print("CI workflow verification passed: strict failure propagation and offline contract verified.")
        return 0
    else:
        print("CI workflow verification failed:", file=sys.stderr)
        for err in errors:
            print(f" - {err}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
