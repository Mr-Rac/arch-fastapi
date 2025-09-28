from datetime import datetime

from pydantic import EmailStr
from sqlmodel import SQLModel, Field, Relationship


class AuthBaseModel(SQLModel):
    id: int | None = Field(default=None, primary_key=True)
    created_at: datetime | None = Field(default_factory=datetime.now)
    updated_at: datetime | None = Field(default_factory=datetime.now, sa_column_kwargs={"onupdate": datetime.now})


class UserRoleLink(SQLModel, table=True):
    uid: int | None = Field(default=None, foreign_key="user.id", primary_key=True)
    rid: int | None = Field(default=None, foreign_key="role.id", primary_key=True)


class RolePermissionLink(SQLModel, table=True):
    rid: int | None = Field(default=None, foreign_key="role.id", primary_key=True)
    pid: int | None = Field(default=None, foreign_key="permission.id", primary_key=True)


class User(AuthBaseModel, table=True):
    username: str = Field(..., unique=True, index=True, max_length=255)
    password: str = Field(..., max_length=128)
    email: EmailStr | None = Field(default=None, unique=True, index=True, max_length=255)

    roles: list["Role"] = Relationship(
        back_populates="users",
        link_model=UserRoleLink,
        sa_relationship_kwargs={
            "lazy": "selectin"
        }
    )

    @property
    def scopes(self) -> list[str]:
        return [permission.scope for role in self.roles for permission in role.permissions]


class Role(AuthBaseModel, table=True):
    name: str = Field(..., unique=True, index=True)

    users: list["User"] = Relationship(
        back_populates="roles",
        link_model=UserRoleLink,
        sa_relationship_kwargs={
            "lazy": "selectin"
        }
    )
    permissions: list["Permission"] = Relationship(
        back_populates="roles",
        link_model=RolePermissionLink,
        sa_relationship_kwargs={
            "lazy": "selectin"
        }
    )


class Permission(AuthBaseModel, table=True):
    name: str = Field(..., unique=True, index=True, max_length=255)
    scope: str = Field(..., unique=True, index=True, max_length=255)
    desc: str | None = Field(default=None, max_length=255)

    roles: list["Role"] = Relationship(
        back_populates="permissions",
        link_model=RolePermissionLink,
        sa_relationship_kwargs={
            "lazy": "selectin"
        }
    )
