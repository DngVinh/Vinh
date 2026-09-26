from __future__ import annotations

from typing import Protocol


class RevocationError(Exception):
    """Raised when session revocation fails in store."""
    pass


class RevocationStore(Protocol):
    def revoke(self, token_or_session_id: str) -> None:
        ...

    def is_revoked(self, token_or_session_id: str) -> bool:
        ...


class InMemoryRevocationStore:
    def __init__(self) -> None:
        self._revoked: set[str] = set()

    def revoke(self, token_or_session_id: str) -> None:
        self._revoked.add(token_or_session_id)

    def is_revoked(self, token_or_session_id: str) -> bool:
        return token_or_session_id in self._revoked


class LogoutService:
    def __init__(self, revocation_store: RevocationStore) -> None:
        self._store = revocation_store

    def logout(self, token_or_session_id: str) -> None:
        if not token_or_session_id:
            raise ValueError("Token or session ID required for logout")
        self._store.revoke(token_or_session_id)
