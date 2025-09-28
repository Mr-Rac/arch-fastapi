from redis.asyncio import ConnectionPool

from app.core.config import settings


async def create_auth_redis_pool() -> ConnectionPool:
    return ConnectionPool.from_url(
        url=settings.AUTH_REDIS_DB_URL,
        decode_responses=settings.REDIS_DECODE_RESPONSES,
        retry_on_timeout=settings.REDIS_RETRY_ON_TIMEOUT,
        max_connections=settings.REDIS_MAX_CONNECTIONS,
    )
