"""Application lifecycle management.

Handles startup (database connections, table creation, admin seeding)
and shutdown (connection cleanup) using FastAPI's lifespan protocol.
"""

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from redis.asyncio import ConnectionPool, Redis
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker
from sqlmodel import SQLModel

from app.core.config import settings
from app.core.database.mongo import create_mongo_client, get_mongo_database
from app.core.database.postgres import create_pg_engine, create_pg_session_maker
from app.core.database.redis import create_redis_pool
from app.core.security import hash_password
from app.domain.auth.entity import Permission, Role, User

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[dict]:
    """Startup and shutdown lifecycle for all shared resources."""

    # ── Validate config ───────────────────────────────────────────────────
    if not settings.SECRET_KEY or len(settings.SECRET_KEY) < 32:
        raise RuntimeError("SECRET_KEY is not configured or too short")

    # ── PostgreSQL ────────────────────────────────────────────────────────
    pg_engine: AsyncEngine = create_pg_engine()
    pg_session_maker: async_sessionmaker[AsyncSession] = create_pg_session_maker(pg_engine)

    async with pg_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    logger.info("PostgreSQL connected - tables ensured.")

    async with pg_session_maker() as session:
        await _seed_admin(session)

    # ── MongoDB ───────────────────────────────────────────────────────────
    mongo_client = create_mongo_client()
    mongo_db = get_mongo_database(mongo_client)
    logger.info("MongoDB client created - db=%s", mongo_db.name)

    # ── Redis ─────────────────────────────────────────────────────────────
    redis_pool: ConnectionPool = create_redis_pool()
    redis = Redis(connection_pool=redis_pool)
    await redis.ping()
    await redis.aclose()
    logger.info("Redis connected.")

    # ── Yield state ───────────────────────────────────────────────────────
    yield {
        "pg_engine": pg_engine,
        "pg_session_maker": pg_session_maker,
        "mongo_client": mongo_client,
        "mongo_db": mongo_db,
        "redis_pool": redis_pool,
    }

    # ── Shutdown ──────────────────────────────────────────────────────────
    await pg_engine.dispose()
    await redis_pool.aclose()
    mongo_client.close()
    logger.info("All connections closed.")


async def _seed_admin(session: AsyncSession) -> None:
    """Create admin user / role / permission if they don't exist yet."""
    from sqlalchemy import select

    from app.domain.auth.entity import (
        RolePermissionLink,
        UserRoleLink,
    )

    # user
    existing = (
        await session.execute(select(User).where(User.username == settings.ADMIN_USERNAME))
    ).scalar_one_or_none()
    if existing is None:
        user = User(username=settings.ADMIN_USERNAME, password=hash_password(settings.ADMIN_PASSWORD))
        session.add(user)
        await session.commit()
        await session.refresh(user)
    else:
        user = existing

    # role
    existing_role = (await session.execute(select(Role).where(Role.name == settings.ADMIN_ROLE))).scalar_one_or_none()
    if existing_role is None:
        role = Role(name=settings.ADMIN_ROLE)
        session.add(role)
        await session.commit()
        await session.refresh(role)
    else:
        role = existing_role

    # permission
    existing_perm = (
        await session.execute(select(Permission).where(Permission.name == settings.ADMIN_PERMISSION))
    ).scalar_one_or_none()
    if existing_perm is None:
        perm = Permission(name=settings.ADMIN_PERMISSION, scope=settings.ADMIN_SCOPE, description="admin full access")
        session.add(perm)
        await session.commit()
        await session.refresh(perm)
    else:
        perm = existing_perm

    # links (ignore if already present)
    rp = (
        await session.execute(
            select(RolePermissionLink).where(
                RolePermissionLink.role_id == role.id,
                RolePermissionLink.permission_id == perm.id,
            )
        )
    ).scalar_one_or_none()
    if rp is None:
        session.add(RolePermissionLink(role_id=role.id, permission_id=perm.id))  # type: ignore[arg-type]
        await session.commit()

    ur = (
        await session.execute(
            select(UserRoleLink).where(
                UserRoleLink.user_id == user.id,
                UserRoleLink.role_id == role.id,
            )
        )
    ).scalar_one_or_none()
    if ur is None:
        session.add(UserRoleLink(user_id=user.id, role_id=role.id))  # type: ignore[arg-type]
        await session.commit()

    logger.info("Admin seed complete (user=%s, role=%s).", user.username, role.name)
