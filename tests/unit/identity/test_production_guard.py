from __future__ import annotations

from pathlib import Path
import sys
import pytest

ROOT = Path(__file__).resolve().parents[3]
API_SRC = ROOT / "services" / "api" / "src"
if str(API_SRC) not in sys.path:
    sys.path.insert(0, str(API_SRC))

from campus247.infrastructure.identity.production_guard import (
    ProductionSecurityError,
    validate_identity_configuration,
)


def test_production_fails_with_mock_auth() -> None:
    with pytest.raises(ProductionSecurityError, match="forbidden in production"):
        validate_identity_configuration(
            environment="production",
            auth_provider="mock",
            allow_demo_login=False,
        )


def test_production_fails_with_demo_login_enabled() -> None:
    with pytest.raises(ProductionSecurityError, match="forbidden in production"):
        validate_identity_configuration(
            environment="production",
            auth_provider="entra",
            allow_demo_login=True,
        )


def test_production_passes_with_safe_config() -> None:
    result = validate_identity_configuration(
        environment="production",
        auth_provider="entra",
        allow_demo_login=False,
    )
    assert result is True


def test_non_production_allows_mock_auth() -> None:
    for env in ("local", "development", "test", "demo-synthetic"):
        assert validate_identity_configuration(
            environment=env,
            auth_provider="mock",
            allow_demo_login=True,
        ) is True
