from __future__ import annotations

import sys
from pathlib import Path
import pytest
from pydantic import ValidationError

ROOT = Path(__file__).resolve().parents[2]
API_SRC = ROOT / "services" / "api" / "src"
if str(API_SRC) not in sys.path:
    sys.path.insert(0, str(API_SRC))

from campus247.bootstrap.settings import Settings


def test_default_settings():
    settings = Settings()
    assert settings.APP_NAME == "Campus 24/7 API"
    assert settings.ENVIRONMENT in ("development", "testing", "staging", "production")
    assert settings.PORT == 8000
    assert "postgresql" in settings.DATABASE_URL
    assert "redis" in settings.REDIS_URL
    assert settings.DEMO_MODE is True


def test_custom_environment_settings(monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "testing")
    monkeypatch.setenv("PORT", "9000")
    monkeypatch.setenv("DEMO_MODE", "false")

    settings = Settings()
    assert settings.ENVIRONMENT == "testing"
    assert settings.PORT == 9000
    assert settings.DEMO_MODE is False


def test_invalid_settings_validation():
    with pytest.raises(ValidationError):
        Settings(PORT=70000)

    with pytest.raises(ValidationError):
        Settings(ENVIRONMENT="invalid_env_name")
