import json
import logging

from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.domains.auth.curd import UserCurd
from app.domains.auth.schema import UserSelect


class RedisKey:

    @classmethod
    def USER_SCOPE(cls, username: str) -> str:
        return f"auth:user:scopes:{username}"

    @classmethod
    def USER_SCOPE_PATTERN(cls) -> str:
        return f"auth:user:scopes:*"


logger = logging.getLogger(__name__)


async def get_user_scopes_cached(redis: Redis, session: AsyncSession, username: str) -> list[str]:
    cache_key = RedisKey.USER_SCOPE(username)

    try:
        cached = await redis.get(cache_key)
        if cached:
            cached_str = cached.decode() if isinstance(cached, bytes) else cached
            scopes = json.loads(cached_str)
            return scopes
    except Exception as e:
        logger.error(f"Redis get failed for user {username}, fallback to database: {e}")

    user = await UserCurd.select(session, UserSelect(username=username))
    if not user:
        return []

    scopes = user.scopes
    try:
        await redis.setex(cache_key, settings.USER_SCOPES_CACHE_TTL, json.dumps(scopes))
    except Exception as e:
        logger.error(f"Redis set failed for user {username}: {e}")

    return scopes


async def clear_user_scopes_cache(redis: Redis, username: str) -> bool:
    cache_key = RedisKey.USER_SCOPE(username)

    try:
        deleted_count = await redis.delete(cache_key)
        if deleted_count > 0:
            logger.info(f"Cleared user scopes cache: {username}")
        return True
    except Exception as e:
        logger.error(f"Failed to clear cache for user {username}: {e}")
        return False


async def clear_users_scopes_cache(redis: Redis, usernames: list[str]) -> int:
    if not usernames:
        return 0

    keys = [RedisKey.USER_SCOPE(username) for username in usernames]

    try:
        deleted_count = await redis.delete(*keys)
        logger.info(f"Cleared {deleted_count} user scopes cache")
        return deleted_count
    except Exception as e:
        logger.error(f"Failed to clear batch cache: {e}")
        return 0


async def clear_all_user_scopes_cache(redis: Redis) -> int:
    try:
        pattern = RedisKey.USER_SCOPE_PATTERN()
        cursor = 0
        deleted_count = 0

        while True:
            cursor, keys = await redis.scan(cursor, match=pattern, count=100)
            if keys:
                deleted_count += await redis.delete(*keys)
            if cursor == 0:
                break

        logger.info(f"Cleared all user scopes cache, total: {deleted_count}")
        return deleted_count
    except Exception as e:
        logger.error(f"Failed to clear all cache: {e}")
        return 0
