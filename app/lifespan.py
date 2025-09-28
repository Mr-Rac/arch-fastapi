import logging
import ssl
from contextlib import asynccontextmanager
from typing import TypedDict, AsyncIterator

import certifi
from aiohttp import ClientSession, ClientTimeout, TCPConnector
from fastapi import FastAPI
from redis.asyncio import Redis, ConnectionPool
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from app.core.config import settings
from app.core.database.mysql import create_auth_mysql_engine, create_auth_mysql_session_maker, init_auth_mysql
from app.core.database.redis import create_auth_redis_pool


class LifespanState(TypedDict, total=False):
    aiohttp_session: ClientSession
    auth_redis_pool: ConnectionPool
    auth_mysql_engine: AsyncEngine
    auth_mysql_session_maker: async_sessionmaker[AsyncSession]


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[LifespanState]:
    # init aiohttp session
    ssl_context = ssl.create_default_context(cafile=certifi.where())
    aiohttp_session = ClientSession(
        timeout=ClientTimeout(total=settings.AIOHTTP_TIMEOUT),
        connector=TCPConnector(ssl=ssl_context),
    )
    logging.warning("Initialized aiohttp session.")

    # init redis
    auth_redis_pool = await create_auth_redis_pool()
    auth_redis = Redis.from_pool(auth_redis_pool)
    await auth_redis.ping()
    logging.warning("Initialized redis.")

    # init mysql
    auth_mysql_engine = await create_auth_mysql_engine()
    auth_mysql_session_maker = await create_auth_mysql_session_maker(auth_mysql_engine)
    async with auth_mysql_session_maker() as session:
        await init_auth_mysql(session)
    logging.warning("Initialized mysql.")

    yield LifespanState(
        aiohttp_session=aiohttp_session,
        auth_redis_pool=auth_redis_pool,
        auth_mysql_engine=auth_mysql_engine,
        auth_mysql_session_maker=auth_mysql_session_maker,
    )

    await auth_mysql_engine.dispose()
    await auth_redis_pool.aclose()
    await aiohttp_session.close()
