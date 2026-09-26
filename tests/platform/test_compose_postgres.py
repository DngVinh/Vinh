from __future__ import annotations

from pathlib import Path
import yaml


ROOT = Path(__file__).resolve().parents[2]


def test_compose_postgres_service_definition():
    """Verify compose.yaml contains the approved pgvector configuration."""
    compose_path = ROOT / "compose.yaml"
    assert compose_path.exists(), "compose.yaml must exist"

    with compose_path.open("r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    assert "services" in config, "compose.yaml must have services"
    assert "postgres" in config["services"], "postgres service must be declared"

    pg = config["services"]["postgres"]
    assert "pgvector" in pg["image"], f"Postgres image must use pgvector, got: {pg.get('image')}"
    assert any(p.endswith(":5432") for p in pg.get("ports", [])), "Port 5432 (container) must be exposed"

    env = pg.get("environment", {})
    assert env.get("POSTGRES_DB") == "campus247_local"
    assert env.get("POSTGRES_USER") == "campus247"


def test_postgres_init_sql_enables_vector():
    """Verify init.sql enables pgvector and uuid extensions."""
    init_sql_path = ROOT / "infra" / "local" / "postgres" / "init.sql"
    assert init_sql_path.exists(), "infra/local/postgres/init.sql must exist"

    content = init_sql_path.read_text(encoding="utf-8")
    assert 'CREATE EXTENSION IF NOT EXISTS "vector"' in content
    assert 'CREATE EXTENSION IF NOT EXISTS "uuid-ossp"' in content
