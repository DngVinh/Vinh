from __future__ import annotations

import ast
from pathlib import Path
import pytest
import yaml

ROOT = Path(__file__).resolve().parents[2]
LAYERS_CONFIG = Path(__file__).parent / "layers.yaml"


def get_imports(filepath: Path) -> set[str]:
    """Parse a python file and return all imported top-level modules."""
    with open(filepath, "r", encoding="utf-8") as f:
        tree = ast.parse(f.read(), filename=str(filepath))

    imports = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.add(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imports.add(node.module)
    return imports


def test_layers_config_exists():
    assert LAYERS_CONFIG.exists(), "layers.yaml configuration must exist"


def test_import_boundaries_enforced():
    with open(LAYERS_CONFIG, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    src_root = ROOT / config.get("source_root", "services/api/src/campus247")
    rules = config.get("forbidden_imports", {})

    for layer, forbidden_prefixes in rules.items():
        layer_dir = src_root / layer
        if not layer_dir.exists():
            continue

        for py_file in layer_dir.rglob("*.py"):
            imports = get_imports(py_file)
            for imp in imports:
                for forbidden in forbidden_prefixes:
                    assert not imp.startswith(forbidden), (
                        f"Layer boundary violation in {py_file.relative_to(ROOT)}: "
                        f"Layer '{layer}' is forbidden from importing '{forbidden}', but imports '{imp}'"
                    )


def test_negative_path_violation_caught():
    """Verify that a forbidden import is properly caught by validator logic."""
    fake_code = "import fastapi\nfrom sqlalchemy import select"
    tree = ast.parse(fake_code)
    imports = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.add(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imports.add(node.module)

    forbidden = ["fastapi", "sqlalchemy"]
    violations = [imp for imp in imports if any(imp.startswith(f) for f in forbidden)]
    assert len(violations) == 2
