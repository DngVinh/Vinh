from __future__ import annotations


class ProductionSecurityError(Exception):
    """Raised when insecure demo identity or mock auth options are configured in production."""
    pass


def validate_identity_configuration(
    environment: str,
    auth_provider: str,
    allow_demo_login: bool,
) -> bool:
    is_prod = environment.strip().lower() == "production"
    is_mock = auth_provider.strip().lower() in ("mock", "synthetic")

    if is_prod:
        if is_mock or allow_demo_login:
            raise ProductionSecurityError(
                "Unsafe production configuration: Demo identity and mock auth are strictly forbidden in production."
            )
    return True
