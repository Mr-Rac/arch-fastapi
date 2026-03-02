"""Redis async connection pool.

Uses ``redis.asyncio`` with optional hiredis acceleration.
"""

from redis.asyncio import ConnectionPool

from app.core.config import settings


def create_redis_pool() -> ConnectionPool:
    """Create and return an async Redis connection pool."""
    return ConnectionPool.from_url(
        settings.REDIS_URL,
        decode_responses=True,
        max_connections=settings.REDIS_MAX_CONNECTIONS,
        retry_on_timeout=True,
    )
