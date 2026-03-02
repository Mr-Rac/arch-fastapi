"""PostgreSQL async engine and session factory.

Uses SQLAlchemy async with the ``asyncpg`` driver.  Connection pooling
parameters come from ``Settings``.
"""

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings


def create_pg_engine() -> AsyncEngine:
    """Create and return a pooled async engine for PostgreSQL."""
    return create_async_engine(
        settings.POSTGRES_URL,
        echo=settings.PG_ECHO,
        pool_size=settings.PG_POOL_SIZE,
        max_overflow=settings.PG_MAX_OVERFLOW,
        pool_pre_ping=True,
        pool_recycle=settings.PG_POOL_RECYCLE,
    )


def create_pg_session_maker(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    """Create a session factory bound to *engine*."""
    return async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
