from __future__ import annotations

from pathlib import Path
import sys
import pytest

ROOT = Path(__file__).resolve().parents[3]
API_SRC = ROOT / "services" / "api" / "src"
SYNTH_SRC = ROOT / "packages" / "synthetic" / "src"
for p in [API_SRC, SYNTH_SRC]:
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from campus247.infrastructure.identity.mock import SyntheticIdentityAdapter
from campus247.ports.identity import IdentityRole


def test_synthetic_identity_adapter_mint_and_resolve() -> None:
    adapter = SyntheticIdentityAdapter(secret_key="mock-secret-key-for-testing", environment="test")
    
    # Mint token for student
    token = adapter.mint_token(user_id_or_code="SV240000")
    assert isinstance(token, str)
    assert len(token) > 20

    # Resolve token to IdentityContext
    ctx = adapter.resolve_token(token)
    assert ctx.is_authenticated is True
    assert ctx.has_role(IdentityRole.STUDENT)
    assert ctx.student_code == "SV240000"
    assert ctx.is_synthetic is True


def test_synthetic_identity_adapter_rejects_tampered_token() -> None:
    adapter = SyntheticIdentityAdapter(secret_key="mock-secret-key-for-testing", environment="test")
    token = adapter.mint_token(user_id_or_code="SV240000")
    tampered_token = token[:-5] + "xxxxx"

    with pytest.raises(ValueError, match="Invalid signature|Tampered token"):
        adapter.resolve_token(tampered_token)


def test_synthetic_identity_adapter_rejects_production() -> None:
    with pytest.raises(ValueError, match="production"):
        SyntheticIdentityAdapter(secret_key="key", environment="production")
