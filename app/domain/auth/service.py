"""Auth domain service - core business logic.

``AuthService`` orchestrates repositories, security utilities and
caching to implement authentication, token management, and RBAC CRUD.

All validation / authorization errors are raised as ``BizError`` so
that the global exception handler returns a consistent response.
"""

import logging

from app.core.config import settings
from app.core.errors import BizError, ErrorCode
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.domain.auth.entity import Permission, Role, User, _utcnow
from app.domain.auth.repository import (
    PermissionRepository,
    RoleRepository,
    TokenRepository,
    UserRepository,
)
from app.domain.auth.schema import (
    PermissionCreate,
    PermissionPublic,
    PermissionQuery,
    PermissionUpdate,
    RoleCreate,
    RolePublic,
    RoleQuery,
    RoleUpdate,
    TokenPair,
    UserCreate,
    UserPublic,
    UserQuery,
    UserUpdate,
)

logger = logging.getLogger(__name__)


class AuthService:
    """Stateless service - a new instance is created per request via DI."""

    def __init__(
        self,
        user_repo: UserRepository,
        role_repo: RoleRepository,
        permission_repo: PermissionRepository,
        token_repo: TokenRepository,
    ) -> None:
        self._users = user_repo
        self._roles = role_repo
        self._permissions = permission_repo
        self._tokens = token_repo

    # ── Authentication ────────────────────────────────────────────────────

    async def login(self, username: str, password: str) -> TokenPair:
        """Verify credentials and issue a JWT token pair.

        Raises:
            BizError: ``INVALID_CREDENTIALS`` on bad username / password.
        """
        user = await self._users.find_by_username(username)
        if user is None or not verify_password(password, user.password):
            logger.warning("Login failed for username=%s", username)
            raise BizError(ErrorCode.INVALID_CREDENTIALS)

        scopes = await self._resolve_scopes(user)

        access, access_jti = create_access_token(user.username, scopes)
        refresh, refresh_jti = create_refresh_token(user.username, scopes)

        await self._tokens.allow(access_jti, settings.ACCESS_TOKEN_EXPIRE_SECONDS)
        await self._tokens.allow(refresh_jti, settings.REFRESH_TOKEN_EXPIRE_SECONDS)

        logger.info("Login succeeded for username=%s scopes=%s", user.username, scopes)
        return TokenPair(access_token=access, refresh_token=refresh)

    async def refresh_token(self, refresh_token_str: str) -> TokenPair:
        """Exchange a valid refresh token for a new token pair.

        Raises:
            BizError: ``TOKEN_INVALID`` / ``TOKEN_EXPIRED``.
        """
        payload = decode_token(refresh_token_str)
        if payload.get("type") != "refresh":
            raise BizError(ErrorCode.TOKEN_INVALID, "not a refresh token")

        old_jti = payload["jti"]
        if not await self._tokens.is_allowed(old_jti):
            raise BizError(ErrorCode.TOKEN_INVALID, "token revoked")

        await self._tokens.revoke(old_jti)

        subject: str = payload["sub"]
        scopes: list[str] = payload.get("scopes", [])

        access, access_jti = create_access_token(subject, scopes)
        refresh, refresh_jti = create_refresh_token(subject, scopes)

        await self._tokens.allow(access_jti, settings.ACCESS_TOKEN_EXPIRE_SECONDS)
        await self._tokens.allow(refresh_jti, settings.REFRESH_TOKEN_EXPIRE_SECONDS)

        logger.info("Token refreshed for subject=%s", subject)
        return TokenPair(access_token=access, refresh_token=refresh)

    async def logout(self, username: str) -> None:
        """Revoke **all** tokens for a user and clear cached scopes."""
        await self._tokens.revoke_all(username)
        await self._tokens.clear_cached_scopes(username)
        logger.info("Logout: all tokens revoked for username=%s", username)

    # ── User CRUD ─────────────────────────────────────────────────────────

    async def get_user(self, query: UserQuery) -> UserPublic:
        """Fetch a single user by id or username.

        Raises:
            BizError: ``USER_NOT_FOUND``.
        """
        user: User | None = None
        if query.id is not None:
            user = await self._users.find_by_id(query.id)
        elif query.username is not None:
            user = await self._users.find_by_username(query.username)
        if user is None:
            raise BizError(ErrorCode.USER_NOT_FOUND)
        return self._to_user_public(user)

    async def list_users(self, offset: int = 0, limit: int = 20) -> list[UserPublic]:
        """Return a paginated list of users."""
        users = await self._users.find_all(offset, limit)
        return [self._to_user_public(u) for u in users]

    async def create_user(self, body: UserCreate) -> UserPublic:
        """Create a new user.

        Raises:
            BizError: ``USER_ALREADY_EXISTS`` if username is taken.
        """
        if await self._users.find_by_username(body.username):
            raise BizError(ErrorCode.USER_ALREADY_EXISTS)
        user = User(username=body.username, password=hash_password(body.password), email=body.email)
        user = await self._users.save(user)
        logger.info("User created: id=%d username=%s", user.id, user.username)
        return self._to_user_public(user)

    async def update_user(self, body: UserUpdate) -> UserPublic:
        """Update user fields.

        Raises:
            BizError: ``USER_NOT_FOUND``.
        """
        fields: dict[str, object] = {}
        if body.username is not None:
            fields["username"] = body.username
        if body.password is not None:
            fields["password"] = hash_password(body.password)
        if body.email is not None:
            fields["email"] = body.email
        if fields:
            fields["updated_at"] = _utcnow()
        user = await self._users.update(body.id, **fields)
        if user is None:
            raise BizError(ErrorCode.USER_NOT_FOUND)
        logger.info("User updated: id=%d fields=%s", body.id, list(fields.keys()))
        return self._to_user_public(user)

    async def delete_user(self, user_id: int) -> None:
        """Delete a user by id.

        Raises:
            BizError: ``USER_NOT_FOUND``.
        """
        if not await self._users.delete(user_id):
            raise BizError(ErrorCode.USER_NOT_FOUND)
        logger.info("User deleted: id=%d", user_id)

    # ── Role CRUD ─────────────────────────────────────────────────────────

    async def get_role(self, query: RoleQuery) -> RolePublic:
        """Fetch a single role by id or name.

        Raises:
            BizError: ``ROLE_NOT_FOUND``.
        """
        role: Role | None = None
        if query.id is not None:
            role = await self._roles.find_by_id(query.id)
        elif query.name is not None:
            role = await self._roles.find_by_name(query.name)
        if role is None:
            raise BizError(ErrorCode.ROLE_NOT_FOUND)
        return self._to_role_public(role)

    async def list_roles(self, offset: int = 0, limit: int = 20) -> list[RolePublic]:
        """Return a paginated list of roles."""
        roles = await self._roles.find_all(offset, limit)
        return [self._to_role_public(r) for r in roles]

    async def create_role(self, body: RoleCreate) -> RolePublic:
        """Create a new role.

        Raises:
            BizError: ``ROLE_ALREADY_EXISTS`` if name is taken.
        """
        if await self._roles.find_by_name(body.name):
            raise BizError(ErrorCode.ROLE_ALREADY_EXISTS)
        role = Role(name=body.name)
        role = await self._roles.save(role)
        logger.info("Role created: id=%d name=%s", role.id, role.name)
        return self._to_role_public(role)

    async def update_role(self, body: RoleUpdate) -> RolePublic:
        """Update role fields.

        Raises:
            BizError: ``ROLE_NOT_FOUND``.
        """
        fields: dict[str, object] = {}
        if body.name is not None:
            fields["name"] = body.name
        if fields:
            fields["updated_at"] = _utcnow()
        role = await self._roles.update(body.id, **fields)
        if role is None:
            raise BizError(ErrorCode.ROLE_NOT_FOUND)
        logger.info("Role updated: id=%d fields=%s", body.id, list(fields.keys()))
        return self._to_role_public(role)

    async def delete_role(self, role_id: int) -> None:
        """Delete a role by id.

        Raises:
            BizError: ``ROLE_NOT_FOUND``.
        """
        if not await self._roles.delete(role_id):
            raise BizError(ErrorCode.ROLE_NOT_FOUND)
        logger.info("Role deleted: id=%d", role_id)

    # ── Permission CRUD ───────────────────────────────────────────────────

    async def get_permission(self, query: PermissionQuery) -> PermissionPublic:
        """Fetch a single permission by id or name.

        Raises:
            BizError: ``PERMISSION_NOT_FOUND``.
        """
        perm: Permission | None = None
        if query.id is not None:
            perm = await self._permissions.find_by_id(query.id)
        elif query.name is not None:
            perm = await self._permissions.find_by_name(query.name)
        if perm is None:
            raise BizError(ErrorCode.PERMISSION_NOT_FOUND)
        return self._to_permission_public(perm)

    async def list_permissions(self, offset: int = 0, limit: int = 20) -> list[PermissionPublic]:
        """Return a paginated list of permissions."""
        perms = await self._permissions.find_all(offset, limit)
        return [self._to_permission_public(p) for p in perms]

    async def create_permission(self, body: PermissionCreate) -> PermissionPublic:
        """Create a new permission.

        Raises:
            BizError: ``PERMISSION_ALREADY_EXISTS`` if name is taken.
        """
        if await self._permissions.find_by_name(body.name):
            raise BizError(ErrorCode.PERMISSION_ALREADY_EXISTS)
        perm = Permission(name=body.name, scope=body.scope, description=body.description)
        perm = await self._permissions.save(perm)
        logger.info("Permission created: id=%d name=%s scope=%s", perm.id, perm.name, perm.scope)
        return self._to_permission_public(perm)

    async def update_permission(self, body: PermissionUpdate) -> PermissionPublic:
        """Update permission fields.

        Raises:
            BizError: ``PERMISSION_NOT_FOUND``.
        """
        fields: dict[str, object] = {}
        if body.name is not None:
            fields["name"] = body.name
        if body.scope is not None:
            fields["scope"] = body.scope
        if body.description is not None:
            fields["description"] = body.description
        if fields:
            fields["updated_at"] = _utcnow()
        perm = await self._permissions.update(body.id, **fields)
        if perm is None:
            raise BizError(ErrorCode.PERMISSION_NOT_FOUND)
        logger.info("Permission updated: id=%d fields=%s", body.id, list(fields.keys()))
        return self._to_permission_public(perm)

    async def delete_permission(self, permission_id: int) -> None:
        """Delete a permission by id.

        Raises:
            BizError: ``PERMISSION_NOT_FOUND``.
        """
        if not await self._permissions.delete(permission_id):
            raise BizError(ErrorCode.PERMISSION_NOT_FOUND)
        logger.info("Permission deleted: id=%d", permission_id)

    # ── Grant / Revoke ────────────────────────────────────────────────────

    async def grant_role(self, user_id: int, role_id: int) -> None:
        """Assign a role to a user and invalidate the scope cache."""
        await self._users.add_role(user_id, role_id)
        await self._tokens.clear_cached_scopes((await self._users.find_by_id(user_id)).username)  # type: ignore[union-attr]
        logger.info("Role granted: user_id=%d role_id=%d", user_id, role_id)

    async def grant_permission(self, role_id: int, permission_id: int) -> None:
        """Assign a permission to a role."""
        await self._roles.add_permission(role_id, permission_id)
        logger.info("Permission granted: role_id=%d permission_id=%d", role_id, permission_id)

    # ── Helpers ───────────────────────────────────────────────────────────

    async def _resolve_scopes(self, user: User) -> list[str]:
        """Resolve scopes with cache-aside pattern."""
        cached = await self._tokens.get_cached_scopes(user.username)
        if cached is not None:
            return cached
        scopes = user.scopes
        await self._tokens.cache_scopes(user.username, scopes, settings.USER_SCOPES_CACHE_TTL)
        return scopes

    @staticmethod
    def _to_user_public(user: User) -> UserPublic:
        """Convert a ``User`` entity to its public representation."""
        return UserPublic(
            id=user.id,  # type: ignore[arg-type]
            username=user.username,
            email=user.email,
            created_at=user.created_at,
            updated_at=user.updated_at,
            roles=[
                RolePublic(
                    id=r.id,  # type: ignore[arg-type]
                    name=r.name,
                    created_at=r.created_at,
                    updated_at=r.updated_at,
                    permissions=[
                        PermissionPublic(
                            id=p.id,  # type: ignore[arg-type]
                            name=p.name,
                            scope=p.scope,
                            description=p.description,
                            created_at=p.created_at,
                            updated_at=p.updated_at,
                        )
                        for p in r.permissions
                    ],
                )
                for r in user.roles
            ],
        )

    @staticmethod
    def _to_role_public(role: Role) -> RolePublic:
        """Convert a ``Role`` entity to its public representation."""
        return RolePublic(
            id=role.id,  # type: ignore[arg-type]
            name=role.name,
            created_at=role.created_at,
            updated_at=role.updated_at,
            permissions=[
                PermissionPublic(
                    id=p.id,  # type: ignore[arg-type]
                    name=p.name,
                    scope=p.scope,
                    description=p.description,
                    created_at=p.created_at,
                    updated_at=p.updated_at,
                )
                for p in role.permissions
            ],
        )

    @staticmethod
    def _to_permission_public(perm: Permission) -> PermissionPublic:
        """Convert a ``Permission`` entity to its public representation."""
        return PermissionPublic(
            id=perm.id,  # type: ignore[arg-type]
            name=perm.name,
            scope=perm.scope,
            description=perm.description,
            created_at=perm.created_at,
            updated_at=perm.updated_at,
        )
