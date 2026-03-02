"""Auth HTTP endpoints - login, token refresh, RBAC CRUD.

Every handler delegates to ``AuthService`` and returns ``Result``.
Protected routes use ``require_scopes(...)`` as a dependency guard.
"""

from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm

from app.api.deps import AuthServiceDep, oauth2_scheme, require_scopes
from app.core.response import Result
from app.domain.auth.schema import (
    GrantPermission,
    GrantRole,
    PermissionCreate,
    PermissionQuery,
    PermissionUpdate,
    RefreshRequest,
    RoleCreate,
    RoleQuery,
    RoleUpdate,
    UserCreate,
    UserQuery,
    UserUpdate,
)

router = APIRouter(prefix="/auth", tags=["auth"])


# ── Authentication ────────────────────────────────────────────────────────


@router.post("/login")
async def login(
    form: Annotated[OAuth2PasswordRequestForm, Depends()],
    svc: AuthServiceDep,
) -> Result:
    """Authenticate with username + password, returns JWT token pair."""
    pair = await svc.login(form.username, form.password)
    return Result.ok(pair.model_dump())


@router.post("/refresh-token")
async def refresh_token(body: RefreshRequest, svc: AuthServiceDep) -> Result:
    """Exchange a valid refresh token for a new token pair.

    Scopes are re-resolved from DB so permission changes take effect.
    """
    pair = await svc.refresh_token(body.refresh_token)
    return Result.ok(pair.model_dump())


@router.post("/logout")
async def logout(
    token: Annotated[str, Depends(oauth2_scheme)],
    svc: AuthServiceDep,
) -> Result:
    """Revoke all tokens for the current authenticated user."""
    await svc.logout_current(token)
    return Result.ok()


# ── User CRUD ─────────────────────────────────────────────────────────────


@router.post("/users/query", dependencies=[Depends(require_scopes("user:read"))])
async def query_user(body: UserQuery, svc: AuthServiceDep) -> Result:
    """Query a single user by id, username, or email."""
    user = await svc.get_user(body)
    return Result.ok(user.model_dump())


@router.get("/users", dependencies=[Depends(require_scopes("user:read"))])
async def list_users(svc: AuthServiceDep, offset: int = 0, limit: int = 20) -> Result:
    """Return a paginated user list."""
    users = await svc.list_users(offset, limit)
    return Result.ok([u.model_dump() for u in users])


@router.post("/users", dependencies=[Depends(require_scopes("user:create"))])
async def create_user(body: UserCreate, svc: AuthServiceDep) -> Result:
    """Create a new user."""
    user = await svc.create_user(body)
    return Result.ok(user.model_dump())


@router.put("/users", dependencies=[Depends(require_scopes("user:update"))])
async def update_user(body: UserUpdate, svc: AuthServiceDep) -> Result:
    """Update user fields."""
    user = await svc.update_user(body)
    return Result.ok(user.model_dump())


@router.delete("/users/{user_id}", dependencies=[Depends(require_scopes("user:delete"))])
async def delete_user(user_id: int, svc: AuthServiceDep) -> Result:
    """Delete a user by id."""
    await svc.delete_user(user_id)
    return Result.ok()


# ── Role CRUD ─────────────────────────────────────────────────────────────


@router.post("/roles/query", dependencies=[Depends(require_scopes("role:read"))])
async def query_role(body: RoleQuery, svc: AuthServiceDep) -> Result:
    """Query a single role by id or name."""
    role = await svc.get_role(body)
    return Result.ok(role.model_dump())


@router.get("/roles", dependencies=[Depends(require_scopes("role:read"))])
async def list_roles(svc: AuthServiceDep, offset: int = 0, limit: int = 20) -> Result:
    """Return a paginated role list."""
    roles = await svc.list_roles(offset, limit)
    return Result.ok([r.model_dump() for r in roles])


@router.post("/roles", dependencies=[Depends(require_scopes("role:create"))])
async def create_role(body: RoleCreate, svc: AuthServiceDep) -> Result:
    """Create a new role."""
    role = await svc.create_role(body)
    return Result.ok(role.model_dump())


@router.put("/roles", dependencies=[Depends(require_scopes("role:update"))])
async def update_role(body: RoleUpdate, svc: AuthServiceDep) -> Result:
    """Update role fields."""
    role = await svc.update_role(body)
    return Result.ok(role.model_dump())


@router.delete("/roles/{role_id}", dependencies=[Depends(require_scopes("role:delete"))])
async def delete_role(role_id: int, svc: AuthServiceDep) -> Result:
    """Delete a role by id."""
    await svc.delete_role(role_id)
    return Result.ok()


# ── Permission CRUD ───────────────────────────────────────────────────────


@router.post("/permissions/query", dependencies=[Depends(require_scopes("permission:read"))])
async def query_permission(body: PermissionQuery, svc: AuthServiceDep) -> Result:
    """Query a single permission by id or name."""
    perm = await svc.get_permission(body)
    return Result.ok(perm.model_dump())


@router.get("/permissions", dependencies=[Depends(require_scopes("permission:read"))])
async def list_permissions(svc: AuthServiceDep, offset: int = 0, limit: int = 20) -> Result:
    """Return a paginated permission list."""
    perms = await svc.list_permissions(offset, limit)
    return Result.ok([p.model_dump() for p in perms])


@router.post("/permissions", dependencies=[Depends(require_scopes("permission:create"))])
async def create_permission(body: PermissionCreate, svc: AuthServiceDep) -> Result:
    """Create a new permission."""
    perm = await svc.create_permission(body)
    return Result.ok(perm.model_dump())


@router.put("/permissions", dependencies=[Depends(require_scopes("permission:update"))])
async def update_permission(body: PermissionUpdate, svc: AuthServiceDep) -> Result:
    """Update permission fields."""
    perm = await svc.update_permission(body)
    return Result.ok(perm.model_dump())


@router.delete("/permissions/{perm_id}", dependencies=[Depends(require_scopes("permission:delete"))])
async def delete_permission(perm_id: int, svc: AuthServiceDep) -> Result:
    """Delete a permission by id."""
    await svc.delete_permission(perm_id)
    return Result.ok()


# ── Grant / Revoke ────────────────────────────────────────────────────────


@router.post("/roles/grant", dependencies=[Depends(require_scopes("role:grant"))])
async def grant_role(body: GrantRole, svc: AuthServiceDep) -> Result:
    """Assign a role to a user. Invalidates the user's scope cache."""
    await svc.grant_role(body.user_id, body.role_id)
    return Result.ok()


@router.post("/roles/revoke", dependencies=[Depends(require_scopes("role:revoke"))])
async def revoke_role(body: GrantRole, svc: AuthServiceDep) -> Result:
    """Remove a role from a user. Invalidates the user's scope cache."""
    await svc.revoke_role(body.user_id, body.role_id)
    return Result.ok()


@router.post("/permissions/grant", dependencies=[Depends(require_scopes("permission:grant"))])
async def grant_permission(body: GrantPermission, svc: AuthServiceDep) -> Result:
    """Assign a permission to a role. Invalidates all affected users' caches."""
    await svc.grant_permission(body.role_id, body.permission_id)
    return Result.ok()


@router.post("/permissions/revoke", dependencies=[Depends(require_scopes("permission:revoke"))])
async def revoke_permission(body: GrantPermission, svc: AuthServiceDep) -> Result:
    """Remove a permission from a role. Invalidates all affected users' caches."""
    await svc.revoke_permission(body.role_id, body.permission_id)
    return Result.ok()
