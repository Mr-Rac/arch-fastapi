"""Auth domain DTOs (Data Transfer Objects).

Schemas are the **public** contract of the domain:
  * ``*Create`` / ``*Update`` / ``*Query`` — request bodies
  * ``*Public`` — response bodies (never expose ``password``)
  * ``TokenPair`` — login / refresh response
"""

from datetime import datetime

from pydantic import BaseModel, EmailStr, Field

# ── Token ─────────────────────────────────────────────────────────────────


class TokenPair(BaseModel):
    """Access + refresh token pair returned on login / refresh."""

    access_token: str
    refresh_token: str
    token_type: str = "Bearer"


class RefreshRequest(BaseModel):
    refresh_token: str


class LogoutRequest(BaseModel):
    username: str


# ── User ──────────────────────────────────────────────────────────────────


class UserCreate(BaseModel):
    username: str = Field(max_length=64)
    password: str = Field(max_length=128)
    email: EmailStr | None = Field(default=None, max_length=128)


class UserUpdate(BaseModel):
    id: int
    username: str | None = Field(default=None, max_length=64)
    password: str | None = Field(default=None, max_length=128)
    email: EmailStr | None = Field(default=None, max_length=128)


class UserQuery(BaseModel):
    id: int | None = None
    username: str | None = None
    email: str | None = None


class UserDelete(BaseModel):
    id: int


class UserPublic(BaseModel):
    """User representation visible to API consumers."""

    id: int
    username: str
    email: str | None
    created_at: datetime
    updated_at: datetime
    roles: list["RolePublic"] | None = None


# ── Role ──────────────────────────────────────────────────────────────────


class RoleCreate(BaseModel):
    name: str = Field(max_length=64)


class RoleUpdate(BaseModel):
    id: int
    name: str | None = Field(default=None, max_length=64)


class RoleQuery(BaseModel):
    id: int | None = None
    name: str | None = None


class RoleDelete(BaseModel):
    id: int


class RolePublic(BaseModel):
    """Role representation visible to API consumers."""

    id: int
    name: str
    created_at: datetime
    updated_at: datetime
    permissions: list["PermissionPublic"] | None = None


# ── Permission ────────────────────────────────────────────────────────────


class PermissionCreate(BaseModel):
    name: str = Field(max_length=64)
    scope: str = Field(max_length=128)
    description: str | None = Field(default=None, max_length=256)


class PermissionUpdate(BaseModel):
    id: int
    name: str | None = Field(default=None, max_length=64)
    scope: str | None = Field(default=None, max_length=128)
    description: str | None = Field(default=None, max_length=256)


class PermissionQuery(BaseModel):
    id: int | None = None
    name: str | None = None


class PermissionDelete(BaseModel):
    id: int


class PermissionPublic(BaseModel):
    """Permission representation visible to API consumers."""

    id: int
    name: str
    scope: str
    description: str | None
    created_at: datetime
    updated_at: datetime


# ── Grant / Revoke ────────────────────────────────────────────────────────


class GrantRole(BaseModel):
    """Assign a role to a user."""

    user_id: int
    role_id: int


class GrantPermission(BaseModel):
    """Assign a permission to a role."""

    role_id: int
    permission_id: int
