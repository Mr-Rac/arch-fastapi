"""Redis-backed token allow-list and scope cache.

Key schema
----------
* ``token:allow:{jti}``            - token allow-list entry (TTL = token lifetime)
* ``token:user:{username}``        - set of all active JTIs belonging to a user
* ``cache:scopes:{username}``      - cached permission-scope list
"""

import logging

import orjson
from redis.asyncio import Redis

logger = logging.getLogger(__name__)


class RedisTokenRepository:
    """Implements ``TokenRepository`` using Redis."""

    def __init__(self, redis: Redis) -> None:  # type: ignore[type-arg]
        self._r = redis

    # ── Allow-list ────────────────────────────────────────────────────────

    async def allow(self, jti: str, username: str, ttl: int) -> None:
        """Add a JTI to the allow-list and track it under the user's set.

        Both the allow-list entry and the user-set member share the same
        TTL so they expire together.
        """
        pipe = self._r.pipeline()
        pipe.set(f"token:allow:{jti}", username, ex=ttl)
        pipe.sadd(f"token:user:{username}", jti)
        pipe.expire(f"token:user:{username}", ttl)
        await pipe.execute()

    async def is_allowed(self, jti: str) -> bool:
        """Check whether a JTI is still in the allow-list."""
        return await self._r.exists(f"token:allow:{jti}") > 0

    async def revoke(self, jti: str) -> None:
        """Remove a single JTI from the allow-list."""
        username = await self._r.get(f"token:allow:{jti}")
        pipe = self._r.pipeline()
        pipe.delete(f"token:allow:{jti}")
        if username:
            pipe.srem(f"token:user:{username}", jti)
        await pipe.execute()

    async def revoke_all(self, username: str) -> None:
        """Remove **all** active JTIs belonging to *username*."""
        key = f"token:user:{username}"
        jtis = await self._r.smembers(key)
        if jtis:
            pipe = self._r.pipeline()
            for jti in jtis:
                pipe.delete(f"token:allow:{jti}")
            pipe.delete(key)
            await pipe.execute()
            logger.info("Revoked %d tokens for username=%s", len(jtis), username)

    # ── Scope cache ───────────────────────────────────────────────────────

    async def get_cached_scopes(self, username: str) -> list[str] | None:
        """Return cached scopes or ``None`` on miss / error."""
        try:
            raw = await self._r.get(f"cache:scopes:{username}")
            if raw is None:
                return None
            return orjson.loads(raw)
        except Exception:
            logger.warning("scope cache read failed for %s", username, exc_info=True)
            return None

    async def cache_scopes(self, username: str, scopes: list[str], ttl: int) -> None:
        """Write scopes to cache with a TTL (seconds)."""
        try:
            await self._r.set(f"cache:scopes:{username}", orjson.dumps(scopes), ex=ttl)
        except Exception:
            logger.warning("scope cache write failed for %s", username, exc_info=True)

    async def clear_cached_scopes(self, username: str) -> None:
        """Invalidate cached scopes for a single user."""
        await self._r.delete(f"cache:scopes:{username}")
