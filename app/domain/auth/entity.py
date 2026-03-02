"""Auth domain entities (SQLModel ORM models).

Entities are the core of the domain layer.  They represent database
tables **and** carry domain properties like ``User.scopes``.

Relationship loading strategy is ``selectin`` (eager) so that
role → permission chains are available without extra queries.
"""

from datetime import UTC, datetime

from sqlmodel import Field, Relationship, SQLModel

# ── Link tables ───────────────────────────────────────────────────────────


class UserRoleLink(SQLModel, table=True):
    """Many-to-many link between User and Role."""

    __tablename__ = "user_role_link"

    user_id: int = Field(foreign_key="user.id", primary_key=True)
    role_id: int = Field(foreign_key="role.id", primary_key=True)


class RolePermissionLink(SQLModel, table=True):
    """Many-to-many link between Role and Permission."""

    __tablename__ = "role_permission_link"

    role_id: int = Field(foreign_key="role.id", primary_key=True)
    permission_id: int = Field(foreign_key="permission.id", primary_key=True)


# ── Entities ──────────────────────────────────────────────────────────────


def _utcnow() -> datetime:
    """Return current UTC time as a naive datetime (no tzinfo).

    asyncpg requires naive datetimes for ``TIMESTAMP WITHOUT TIME ZONE`` columns.
    """
    return datetime.now(UTC).replace(tzinfo=None)


class User(SQLModel, table=True):
    """System user with role-based access control."""

    __tablename__ = "user"

    id: int | None = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=_utcnow)
    updated_at: datetime = Field(default_factory=_utcnow)
    username: str = Field(max_length=64, unique=True, index=True)
    password: str = Field(max_length=128)
    email: str | None = Field(default=None, max_length=128, unique=True, index=True)

    roles: list["Role"] = Relationship(
        back_populates="users",
        link_model=UserRoleLink,
        sa_relationship_kwargs={"lazy": "selectin"},
    )

    @property
    def scopes(self) -> list[str]:
        """Aggregate permission scopes from all roles."""
        return list({p.scope for r in self.roles for p in r.permissions})


class Role(SQLModel, table=True):
    """Authorization role - groups a set of permissions."""

    __tablename__ = "role"

    id: int | None = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=_utcnow)
    updated_at: datetime = Field(default_factory=_utcnow)
    name: str = Field(max_length=64, unique=True, index=True)

    users: list["User"] = Relationship(
        back_populates="roles",
        link_model=UserRoleLink,
        sa_relationship_kwargs={"lazy": "selectin"},
    )
    permissions: list["Permission"] = Relationship(
        back_populates="roles",
        link_model=RolePermissionLink,
        sa_relationship_kwargs={"lazy": "selectin"},
    )


class Permission(SQLModel, table=True):
    """Fine-grained permission identified by a unique scope string."""

    __tablename__ = "permission"

    id: int | None = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=_utcnow)
    updated_at: datetime = Field(default_factory=_utcnow)
    name: str = Field(max_length=64, unique=True, index=True)
    scope: str = Field(max_length=128, unique=True, index=True)
    description: str | None = Field(default=None, max_length=256)

    roles: list["Role"] = Relationship(
        back_populates="permissions",
        link_model=RolePermissionLink,
        sa_relationship_kwargs={"lazy": "selectin"},
    )
