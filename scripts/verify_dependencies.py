import sys
import re
from pathlib import Path
import tomllib

APPROVED_ALLOWLIST = {
    "fastapi",
    "uvicorn",
    "pydantic",
    "pydantic-settings",
    "sqlalchemy",
    "asyncpg",
    "alembic",
    "pgvector",
    "redis",
    "httpx",
    "pytest",
    "pytest-asyncio",
    "jsonschema",
    "pyyaml",
}


def normalize_package_name(raw_spec: str) -> str:
    # Extracts package name before [extras] or >= / == version specs
    match = re.match(r"^([a-zA-Z0-9_\-\.]+)", raw_spec.strip())
    if match:
        return match.group(1).lower().replace("_", "-")
    return raw_spec.strip().lower()


def load_declared_dependencies(pyproject_path: Path) -> set[str]:
    with open(pyproject_path, "rb") as f:
        data = tomllib.load(f)

    deps = set()
    project_deps = data.get("project", {}).get("dependencies", [])
    for d in project_deps:
        deps.add(normalize_package_name(d))

    dev_deps = data.get("dependency-groups", {}).get("dev", [])
    for d in dev_deps:
        deps.add(normalize_package_name(d))

    return deps


def load_locked_dependencies(lock_path: Path) -> set[str]:
    with open(lock_path, "rb") as f:
        data = tomllib.load(f)

    locked = set()
    packages = data.get("package", [])
    for pkg in packages:
        # Check direct dependencies under virtual root package
        if pkg.get("name") == "campus247":
            for d in pkg.get("dependencies", []):
                locked.add(normalize_package_name(d.get("name", "")))
            for d in pkg.get("dev-dependencies", {}).get("dev", []):
                locked.add(normalize_package_name(d.get("name", "")))
        else:
            pkg_name = pkg.get("name")
            if pkg_name:
                locked.add(normalize_package_name(pkg_name))

    return locked


def verify_dependencies(repo_root: Path | None = None) -> tuple[bool, list[str]]:
    if repo_root is None:
        repo_root = Path(__file__).resolve().parents[1]

    pyproject_path = repo_root / "pyproject.toml"
    lock_path = repo_root / "uv.lock"

    errors: list[str] = []

    if not pyproject_path.is_file():
        errors.append(f"pyproject.toml not found at {pyproject_path}")
        return False, errors

    if not lock_path.is_file():
        errors.append(f"uv.lock not found at {lock_path}")
        return False, errors

    declared = load_declared_dependencies(pyproject_path)
    locked = load_locked_dependencies(lock_path)

    # 1. Check against approved allowlist (AC-01, AC-03)
    for pkg in declared:
        if pkg not in APPROVED_ALLOWLIST:
            errors.append(f"Declared package '{pkg}' is not in approved allowlist (DEC-016)")

    for pkg in locked:
        if pkg != "campus247" and pkg not in APPROVED_ALLOWLIST:
            errors.append(f"Locked package '{pkg}' is not in approved allowlist (DEC-016)")

    # 2. Check lock drift (AC-02: verifier fails on lock drift)
    missing_in_lock = declared - locked
    if missing_in_lock:
        errors.append(f"Lock drift: packages declared in pyproject.toml missing in uv.lock: {sorted(missing_in_lock)}")

    # 3. Check undeclared dependencies in lock
    undeclared_in_lock = {p for p in locked if p != "campus247"} - declared
    if undeclared_in_lock:
        errors.append(f"Undeclared dependency in lock file: {sorted(undeclared_in_lock)}")

    return len(errors) == 0, errors


def main() -> int:
    is_valid, errors = verify_dependencies()
    if is_valid:
        print("Dependency verification passed: all packages approved, pinned, and locked without drift.")
        return 0
    else:
        print("Dependency verification failed:", file=sys.stderr)
        for err in errors:
            print(f" - {err}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
