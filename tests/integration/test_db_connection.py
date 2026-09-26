from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock
import pytest
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

ROOT = Path(__file__).resolve().parents[2]
API_SRC = ROOT / "services" / "api" / "src"
if str(API_SRC) not in sys.path:
    sys.path.insert(0, str(API_SRC))

from campus247.infrastructure.db import get_engine, get_session_factory, transaction_scope


def test_get_engine_creates_async_engine():
    """Verify get_engine properly configures an AsyncEngine with postgresql+asyncpg."""
    url = "postgresql+asyncpg://campus:campus_secret@localhost:5432/campus247"
    engine = get_engine(url=url)
    assert isinstance(engine, AsyncEngine)
    assert engine.url.drivername == "postgresql+asyncpg"
    assert engine.url.database == "campus247"


def test_get_session_factory_configuration():
    """Verify session factory returns async_sessionmaker configured with AsyncSession."""
    url = "postgresql+asyncpg://campus:campus_secret@localhost:5432/campus247"
    engine = get_engine(url=url)
    session_factory = get_session_factory(engine)
    assert isinstance(session_factory, async_sessionmaker)
    assert session_factory.class_ == AsyncSession


@pytest.mark.asyncio
async def test_transaction_scope_clean_commit():
    """Verify transaction scope executes and manages transaction cleanly."""
    mock_session = AsyncMock(spec=AsyncSession)
    mock_begin_ctx = AsyncMock()
    mock_session.begin.return_value = mock_begin_ctx
    mock_begin_ctx.__aenter__.return_value = None
    mock_begin_ctx.__aexit__.return_value = None

    mock_session_factory = MagicMock()
    mock_session_factory.return_value.__aenter__.return_value = mock_session
    mock_session_factory.return_value.__aexit__.return_value = None

    async with transaction_scope(mock_session_factory) as session:
        assert session is mock_session

    mock_session.begin.assert_called_once()
    mock_session.rollback.assert_not_called()


@pytest.mark.asyncio
async def test_transaction_scope_rollback_on_failure():
    """Verify transaction scope rolls back when exception occurs in block (negative path)."""
    mock_session = AsyncMock(spec=AsyncSession)
    mock_begin_ctx = AsyncMock()
    mock_session.begin.return_value = mock_begin_ctx
    mock_begin_ctx.__aenter__.return_value = None
    mock_begin_ctx.__aexit__.return_value = None

    mock_session_factory = MagicMock()
    mock_session_factory.return_value.__aenter__.return_value = mock_session
    mock_session_factory.return_value.__aexit__.return_value = None

    with pytest.raises(ValueError, match="Database transaction error"):
        async with transaction_scope(mock_session_factory):
            raise ValueError("Database transaction error")

    mock_session.rollback.assert_called_once()
