from __future__ import annotations

from campus247.bootstrap.app import create_app
from campus247.bootstrap.settings import get_settings
from campus247.infrastructure.identity.production_guard import validate_identity_configuration

settings = get_settings()

# Ensure production cannot start with unsafe demo credentials or mock auth
validate_identity_configuration(
    environment=settings.ENVIRONMENT,
    auth_provider="mock" if settings.DEMO_MODE else "entra",
    allow_demo_login=settings.DEMO_MODE,
)

app = create_app()
