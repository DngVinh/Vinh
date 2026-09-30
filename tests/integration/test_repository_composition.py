"""Integration tests for repository composition."""
from __future__ import annotations

import pytest

from campus247.infrastructure.repositories.composition import RepositoryComposition


def test_development_composition_uses_synthetic_adapters():
    """In development, synthetic and in-memory adapters are allowed."""
    comp = RepositoryComposition(environment="development")
    
    assert isinstance(comp.ticket_store, dict)
    assert isinstance(comp.doc_store, dict)
    assert isinstance(comp.rooms_list, list)
    assert len(comp.rooms_list) > 0
    # ensure it doesn't fail


def test_production_composition_fails_closed_without_durable_adapters():
    """In production, starting without durable adapters must fail closed."""
    with pytest.raises(RuntimeError) as exc_info:
        RepositoryComposition(environment="production")
        
    error_msg = str(exc_info.value)
    assert "Startup aborted" in error_msg
    assert "missing" in error_msg.lower()
    
    # Must list missing adapters without exposing credentials
    assert "ticket_store" in error_msg
    assert "doc_store" in error_msg
    assert "schedule_adapter" in error_msg
    
    # Ensure no credentials leaked
    assert "password" not in error_msg.lower()
    assert "secret" not in error_msg.lower()


def test_every_repository_port_is_resolved():
    """Ensure all required ports are mapped on successful composition."""
    comp = RepositoryComposition(environment="testing")
    
    expected_ports = {
        "ticket_store",
        "doc_store",
        "handover_store",
        "sources_store",
        "versions_store",
        "rooms_list",
        "bookings_list",
        "schedule_adapter",
    }
    
    for port in expected_ports:
        assert hasattr(comp, port), f"Missing port {port} in composition"
