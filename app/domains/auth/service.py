from typing import Annotated

from fastapi import Depends
from fastapi.security import OAuth2PasswordRequestForm
from redis.asyncio import Redis

from app.core.token import Token
from app.domains.auth.const import TokenType
from app.domains.auth.curd import *
from app.domains.auth.schema import *
from app.domains.base_service import BaseService
from app.models.auth import *


class AuthService(BaseService):

    @staticmethod
    async def login(
            form: Annotated[OAuth2PasswordRequestForm, Depends()],
            session: AsyncSession,
            redis: Redis,
    ) -> TokenData:
        user = await UserCurd.authenticate(session, form.username, form.password)
        access_token = await Token.create(redis, TokenType.ACCESS, user.username, user.scopes)
        refresh_token = await Token.create(redis, TokenType.REFRESH, user.username, user.scopes)
        return TokenData(access_token=access_token, refresh_token=refresh_token)

    @staticmethod
    async def refresh_token(
            body: RefreshRequestBody,
            redis: Redis,
    ) -> TokenData:
        access_token = await Token.refresh(redis, body.refresh_token)
        return TokenData(access_token=access_token)

    @staticmethod
    async def logout(
            body: LogoutRequestBody,
            session: AsyncSession,
            redis: Redis,
    ):
        user: User = await UserCurd.select(session, UserSelect(username=body.username))
        await Token.clear(redis, user.username)

    @classmethod
    async def select_user(cls, session: AsyncSession, user_in: UserSelect) -> UserPublic:
        user = await UserCurd.select(session, user_in)
        return UserPublic.model_validate(user)

    @staticmethod
    async def create_user(session: AsyncSession, user_in: UserCreate) -> UserPublic:
        user = await UserCurd.create(session, user_in)
        return UserPublic.model_validate(user)

    @staticmethod
    async def update_user(session: AsyncSession, user_in: UserUpdate) -> UserPublic:
        user = await UserCurd.update(session, user_in)
        return UserPublic.model_validate(user)

    @staticmethod
    async def delete_user(session: AsyncSession, user_in: UserDelete):
        await UserCurd.delete(session, user_in)

    @classmethod
    async def select_role(cls, session: AsyncSession, role_in: RoleSelect) -> RolePublic:
        role = await RoleCurd.select(session, role_in)
        return RolePublic.model_validate(role)

    @staticmethod
    async def create_role(session: AsyncSession, role_in: RoleCreate) -> RolePublic:
        role = await RoleCurd.create(session, role_in)
        return RolePublic.model_validate(role)

    @staticmethod
    async def update_role(session: AsyncSession, role_in: RoleUpdate) -> RolePublic:
        role = await RoleCurd.update(session, role_in)
        return RolePublic.model_validate(role)

    @staticmethod
    async def delete_role(session: AsyncSession, role_in: RoleDelete):
        await RoleCurd.delete(session, role_in)

    @classmethod
    async def select_permission(cls, session: AsyncSession, permission_in: PermissionSelect) -> PermissionPublic:
        permission = await PermissionCurd.select(session, permission_in)
        return PermissionPublic.model_validate(permission)

    @staticmethod
    async def create_permission(session: AsyncSession, permission_in: PermissionCreate) -> PermissionPublic:
        permission = await PermissionCurd.create(session, permission_in)
        return PermissionPublic.model_validate(permission)

    @staticmethod
    async def update_permission(session: AsyncSession, permission_in: PermissionUpdate) -> PermissionPublic:
        permission = await PermissionCurd.update(session, permission_in)
        return PermissionPublic.model_validate(permission)

    @staticmethod
    async def delete_permission(session: AsyncSession, permission_in: PermissionDelete):
        await PermissionCurd.delete(session, permission_in)
