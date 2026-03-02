"""Shared FastAPI dependencies.

This module wires the **infra** implementations to the **domain**
interfaces via FastAPI's dependency injection system.

Dependency graph::

    Route
     └─ get_auth_service()
         ├─ PgUserRepository(session)
         ├─ PgRoleRepository(session)
         ├─ PgPermissionRepository(session)
         └─ RedisTokenRepository(redis)
"""

from collections.abc import AsyncGenerator
from typing import Annotated

from fastapi import Depends, Request
from fastapi.security import OAuth2PasswordBearer
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.errors import BizError, ErrorCode
from app.core.security import decode_token
from app.domain.auth.service import AuthService
from app.infra.auth.pg_repository import (
    PgPermissionRepository,
    PgRoleRepository,
    PgUserRepository,
)
from app.infra.auth.redis_repository import RedisTokenRepository

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_PREFIX}/v1/auth/login")


# ── Database sessions ─────────────────────────────────────────────────────


async def get_pg_session(request: Request) -> AsyncGenerator[AsyncSession]:
    """Yield an async PostgreSQL session, closing it after the request."""
    session_maker = request.state.pg_session_maker
    async with session_maker() as session:
        yield session


async def get_redis(request: Request) -> AsyncGenerator[Redis]:  # type: ignore[type-arg]
    """Yield an async Redis client from the pool."""
    redis = Redis(connection_pool=request.state.redis_pool)
    try:
        yield redis
    finally:
        await redis.aclose()


PgDep = Annotated[AsyncSession, Depends(get_pg_session)]
RedisDep = Annotated[Redis, Depends(get_redis)]  # type: ignore[type-arg]


# ── Service factory ───────────────────────────────────────────────────────


async def get_auth_service(pg: PgDep, redis: RedisDep) -> AuthService:
    """Assemble ``AuthService`` with concrete repo implementations."""
    return AuthService(
        user_repo=PgUserRepository(pg),
        role_repo=PgRoleRepository(pg),
        permission_repo=PgPermissionRepository(pg),
        token_repo=RedisTokenRepository(redis),
    )


AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]


# ── Auth guard ────────────────────────────────────────────────────────────


async def get_current_user_scopes(
    token: Annotated[str, Depends(oauth2_scheme)],
    redis: RedisDep,
) -> list[str]:
    """Decode the JWT and return the scopes list.

    Also validates that the token is still in the allow-list.

    Raises:
        BizError: ``TOKEN_INVALID`` / ``TOKEN_EXPIRED`` / ``UNAUTHORIZED``.
    """
    payload = decode_token(token)
    jti = payload.get("jti")
    if not jti:
        raise BizError(ErrorCode.TOKEN_INVALID)

    token_repo = RedisTokenRepository(redis)
    if not await token_repo.is_allowed(jti):
        raise BizError(ErrorCode.TOKEN_INVALID, "token revoked")

    return payload.get("scopes", [])


def require_scopes(*required: str):
    """Factory that returns a FastAPI dependency checking required scopes.

    Usage::

        @router.post("/users", dependencies=[Depends(require_scopes("user:create"))])
        async def create_user(...): ...

    The special scope ``admin`` grants access to everything.
    """

    async def _check(scopes: Annotated[list[str], Depends(get_current_user_scopes)]) -> None:
        if "admin" in scopes:
            return
        if not set(required).issubset(scopes):
            raise BizError(ErrorCode.FORBIDDEN)

    return _check
