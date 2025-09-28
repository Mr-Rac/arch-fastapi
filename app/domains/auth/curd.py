from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.auth.exception import UserError
from app.domains.auth.schema import UserSelect, UserCreate, UserUpdate
from app.domains.base_curd import Curd
from app.models.auth import User, Role, Permission, UserRoleLink, RolePermissionLink

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class UserCurd(Curd):
    model = User

    @classmethod
    async def authenticate(cls, session: AsyncSession, username: str, password: str) -> User:
        user = await cls.select(session, UserSelect(username=username))
        if not pwd_context.verify(password, user.password):
            raise Exception(UserError.INCORRECT_PASSWORD)
        return user

    @classmethod
    async def create(cls, session: AsyncSession, user_in: UserCreate, update: dict | None = None) -> User:
        update = update or {}
        update.update({
            "password": pwd_context.hash(user_in.password),
        })
        return await super().create(session, user_in, update)

    @classmethod
    async def update(cls, session: AsyncSession, user_in: UserUpdate, update: dict | None = None) -> User:
        update = update or {}
        if user_in.password:
            update.update({
                "password": pwd_context.hash(user_in.password),
            })
        return await super().update(session, user_in, update)


class RoleCurd(Curd):
    model = Role


class PermissionCurd(Curd):
    model = Permission


class UserRoleCurd(Curd):
    model = UserRoleLink


class RolePermissionCurd(Curd):
    model = RolePermissionLink
