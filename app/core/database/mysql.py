import logging

from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine, AsyncSession, async_sessionmaker
from sqlmodel import SQLModel

from app.core.config import settings
from app.domains.auth.curd import UserCurd, RoleCurd, PermissionCurd, RolePermissionCurd, UserRoleCurd
from app.domains.auth.schema import UserCreate, RoleCreate, PermissionCreate, GrantPermission, GrantRole, UserSelect, \
    RoleSelect, PermissionSelect


async def create_auth_mysql_engine() -> AsyncEngine:
    return create_async_engine(
        settings.MYSQL_AUTH_DB_URL,
        echo=settings.MYSQL_ECHO,
        echo_pool=settings.MYSQL_ECHO,
        isolation_level=settings.MYSQL_ISOLATION_LEVEL,
        max_overflow=settings.MYSQL_MAX_OVERFLOW,
        pool_pre_ping=settings.MYSQL_POOL_PRE_PING,
        pool_size=settings.MYSQL_POOL_SIZE,
        pool_recycle=settings.MYSQL_POOL_RECYCLE,
        pool_timeout=settings.MYSQL_POOL_TIMEOUT,
    )


async def create_auth_mysql_session_maker(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    async with engine.begin() as connection:
        await connection.run_sync(SQLModel.metadata.create_all)
    return async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        autoflush=False,
        expire_on_commit=False,
    )


async def init_auth_mysql(session: AsyncSession) -> None:
    user = await UserCurd.select(session, UserSelect(username=settings.ADMIN_USER_USERNAME))
    if not user:
        user_in = UserCreate(
            username=settings.ADMIN_USER_USERNAME,
            password=settings.ADMIN_USER_PASSWORD,
        )
        user = await UserCurd.create(session, user_in)

    role = await RoleCurd.select(session, RoleSelect(name=settings.ADMIN_ROLE_NAME))
    if not role:
        role_in = RoleCreate(
            name=settings.ADMIN_ROLE_NAME,
        )
        role = await RoleCurd.create(session, role_in)

    permission = await PermissionCurd.select(session, PermissionSelect(name=settings.ADMIN_PERMISSION_NAME))
    if not permission:
        permission_in = PermissionCreate(
            name=settings.ADMIN_PERMISSION_NAME,
            scope=settings.ADMIN_PERMISSION_SCOPE,
            desc=settings.ADMIN_PERMISSION_DESC,
        )
        permission = await PermissionCurd.create(session, permission_in)

    try:
        role_permission_in = GrantPermission(
            rid=role.id,
            pid=permission.id,
        )
        await RolePermissionCurd.create(session, role_permission_in)
    except Exception as e:
        logging.warning(e)

    try:
        user_role_in = GrantRole(
            uid=user.id,
            rid=role.id,
        )
        await UserRoleCurd.create(session, user_role_in)
    except Exception as e:
        logging.warning(e)
