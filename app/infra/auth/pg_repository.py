"""PostgreSQL implementations of auth repositories.

Each class receives an ``AsyncSession`` and translates domain operations
into SQLAlchemy queries.  The session lifecycle is managed by the
FastAPI dependency in ``api.deps``.

Write operations (save / update / delete) are wrapped in try / except
to ensure rollback and structured error logging on failure.
"""

import logging

from sqlalchemy import delete as sa_delete
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.auth.entity import (
    Permission,
    Role,
    RolePermissionLink,
    User,
    UserRoleLink,
)

logger = logging.getLogger(__name__)


class PgUserRepository:
    """PostgreSQL-backed ``UserRepository``."""

    def __init__(self, session: AsyncSession) -> None:
        self._s = session

    async def find_by_id(self, user_id: int) -> User | None:
        """Find a user by primary key."""
        return await self._s.get(User, user_id)

    async def find_by_username(self, username: str) -> User | None:
        """Find a user by unique username."""
        stmt = select(User).where(User.username == username)
        return (await self._s.execute(stmt)).scalar_one_or_none()

    async def find_all(self, offset: int = 0, limit: int = 20) -> list[User]:
        """Return a paginated slice of users ordered by id."""
        stmt = select(User).offset(offset).limit(limit).order_by(User.id)
        return list((await self._s.execute(stmt)).scalars().all())

    async def save(self, user: User) -> User:
        """Persist a new user and return the refreshed instance."""
        try:
            self._s.add(user)
            await self._s.commit()
            await self._s.refresh(user)
            return user
        except Exception:
            await self._s.rollback()
            logger.exception("Failed to save user username=%s", user.username)
            raise

    async def update(self, user_id: int, **fields: object) -> User | None:
        """Update fields on an existing user, returns ``None`` if not found."""
        user = await self.find_by_id(user_id)
        if user is None:
            return None
        try:
            for k, v in fields.items():
                setattr(user, k, v)
            await self._s.commit()
            await self._s.refresh(user)
            return user
        except Exception:
            await self._s.rollback()
            logger.exception("Failed to update user id=%d fields=%s", user_id, list(fields.keys()))
            raise

    async def delete(self, user_id: int) -> bool:
        """Delete a user and its role links, returns ``False`` if not found."""
        user = await self.find_by_id(user_id)
        if user is None:
            return False
        try:
            await self._s.execute(sa_delete(UserRoleLink).where(UserRoleLink.user_id == user_id))
            await self._s.delete(user)
            await self._s.commit()
            return True
        except Exception:
            await self._s.rollback()
            logger.exception("Failed to delete user id=%d", user_id)
            raise

    async def add_role(self, user_id: int, role_id: int) -> None:
        """Create a user-role link."""
        try:
            self._s.add(UserRoleLink(user_id=user_id, role_id=role_id))
            await self._s.commit()
        except Exception:
            await self._s.rollback()
            logger.exception("Failed to add role link user_id=%d role_id=%d", user_id, role_id)
            raise


class PgRoleRepository:
    """PostgreSQL-backed ``RoleRepository``."""

    def __init__(self, session: AsyncSession) -> None:
        self._s = session

    async def find_by_id(self, role_id: int) -> Role | None:
        """Find a role by primary key."""
        return await self._s.get(Role, role_id)

    async def find_by_name(self, name: str) -> Role | None:
        """Find a role by unique name."""
        stmt = select(Role).where(Role.name == name)
        return (await self._s.execute(stmt)).scalar_one_or_none()

    async def find_all(self, offset: int = 0, limit: int = 20) -> list[Role]:
        """Return a paginated slice of roles ordered by id."""
        stmt = select(Role).offset(offset).limit(limit).order_by(Role.id)
        return list((await self._s.execute(stmt)).scalars().all())

    async def save(self, role: Role) -> Role:
        """Persist a new role and return the refreshed instance."""
        try:
            self._s.add(role)
            await self._s.commit()
            await self._s.refresh(role)
            return role
        except Exception:
            await self._s.rollback()
            logger.exception("Failed to save role name=%s", role.name)
            raise

    async def update(self, role_id: int, **fields: object) -> Role | None:
        """Update fields on an existing role, returns ``None`` if not found."""
        role = await self.find_by_id(role_id)
        if role is None:
            return None
        try:
            for k, v in fields.items():
                setattr(role, k, v)
            await self._s.commit()
            await self._s.refresh(role)
            return role
        except Exception:
            await self._s.rollback()
            logger.exception("Failed to update role id=%d fields=%s", role_id, list(fields.keys()))
            raise

    async def delete(self, role_id: int) -> bool:
        """Delete a role and its links, returns ``False`` if not found."""
        role = await self.find_by_id(role_id)
        if role is None:
            return False
        try:
            await self._s.execute(sa_delete(RolePermissionLink).where(RolePermissionLink.role_id == role_id))
            await self._s.execute(sa_delete(UserRoleLink).where(UserRoleLink.role_id == role_id))
            await self._s.delete(role)
            await self._s.commit()
            return True
        except Exception:
            await self._s.rollback()
            logger.exception("Failed to delete role id=%d", role_id)
            raise

    async def add_permission(self, role_id: int, permission_id: int) -> None:
        """Create a role-permission link."""
        try:
            self._s.add(RolePermissionLink(role_id=role_id, permission_id=permission_id))
            await self._s.commit()
        except Exception:
            await self._s.rollback()
            logger.exception("Failed to add permission link role_id=%d permission_id=%d", role_id, permission_id)
            raise


class PgPermissionRepository:
    """PostgreSQL-backed ``PermissionRepository``."""

    def __init__(self, session: AsyncSession) -> None:
        self._s = session

    async def find_by_id(self, permission_id: int) -> Permission | None:
        """Find a permission by primary key."""
        return await self._s.get(Permission, permission_id)

    async def find_by_name(self, name: str) -> Permission | None:
        """Find a permission by unique name."""
        stmt = select(Permission).where(Permission.name == name)
        return (await self._s.execute(stmt)).scalar_one_or_none()

    async def find_all(self, offset: int = 0, limit: int = 20) -> list[Permission]:
        """Return a paginated slice of permissions ordered by id."""
        stmt = select(Permission).offset(offset).limit(limit).order_by(Permission.id)
        return list((await self._s.execute(stmt)).scalars().all())

    async def save(self, permission: Permission) -> Permission:
        """Persist a new permission and return the refreshed instance."""
        try:
            self._s.add(permission)
            await self._s.commit()
            await self._s.refresh(permission)
            return permission
        except Exception:
            await self._s.rollback()
            logger.exception("Failed to save permission name=%s", permission.name)
            raise

    async def update(self, permission_id: int, **fields: object) -> Permission | None:
        """Update fields on an existing permission, returns ``None`` if not found."""
        perm = await self.find_by_id(permission_id)
        if perm is None:
            return None
        try:
            for k, v in fields.items():
                setattr(perm, k, v)
            await self._s.commit()
            await self._s.refresh(perm)
            return perm
        except Exception:
            await self._s.rollback()
            logger.exception("Failed to update permission id=%d fields=%s", permission_id, list(fields.keys()))
            raise

    async def delete(self, permission_id: int) -> bool:
        """Delete a permission and its role links, returns ``False`` if not found."""
        perm = await self.find_by_id(permission_id)
        if perm is None:
            return False
        try:
            await self._s.execute(
                sa_delete(RolePermissionLink).where(RolePermissionLink.permission_id == permission_id)
            )
            await self._s.delete(perm)
            await self._s.commit()
            return True
        except Exception:
            await self._s.rollback()
            logger.exception("Failed to delete permission id=%d", permission_id)
            raise
