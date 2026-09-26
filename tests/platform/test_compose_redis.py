from __future__ import annotations

from pathlib import Path
import yaml


ROOT = Path(__file__).resolve().parents[2]


def test_compose_redis_service_definition():
    """Verify compose.yaml contains the approved Redis configuration."""
    compose_path = ROOT / "compose.yaml"
    assert compose_path.exists(), "compose.yaml must exist"

    with compose_path.open("r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    assert "services" in config, "compose.yaml must have services"
    assert "redis" in config["services"], "redis service must be declared"

    redis_cfg = config["services"]["redis"]
    assert "redis:7" in redis_cfg["image"], f"Redis image must use redis:7, got: {redis_cfg.get('image')}"
    assert any(p.endswith(":6379") for p in redis_cfg.get("ports", [])), "Port 6379 (container) must be exposed"
    assert "redis_data" in config.get("volumes", {}), "redis_data volume must be declared"
