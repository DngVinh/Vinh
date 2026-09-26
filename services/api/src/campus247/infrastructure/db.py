from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)


def get_engine(url: str, echo: bool = False) -> AsyncEngine:
    """Create async SQLAlchemy engine with connection pool configuration."""
    return create_async_engine(
        url,
        echo=echo,
        pool_pre_ping=True,
    )


def get_session_factory(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    """Create sessionmaker for async transactions."""
    return async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )


@asynccontextmanager
async def transaction_scope(
    session_factory: async_sessionmaker[AsyncSession],
) -> AsyncGenerator[AsyncSession, None]:
    """Provide a transactional scope around a series of operations with automatic rollback."""
    async with session_factory() as session:
        try:
            async with session.begin():
                yield session
        except Exception:
            await session.rollback()
            raise
