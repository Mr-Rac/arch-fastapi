from datetime import datetime

from pydantic import EmailStr
from sqlmodel import SQLModel, Field

from app.domains.base_schema import BaseData, BaseRequest
from app.domains.base_schema import BaseSelect, BaseUpdate, BaseDelete


class TokenData(BaseData):
    access_token: str | None = Field(default=None)
    refresh_token: str | None = Field(default=None)
    token_type: str = Field(default="Bearer")


class LogoutRequestBody(BaseRequest):
    username: str


class RefreshRequestBody(BaseRequest):
    refresh_token: str


class UserSelect(BaseSelect):
    username: str | None = Field(default=None, max_length=255)
    email: EmailStr | None = Field(default=None, max_length=255)


class UserCreate(SQLModel):
    username: str = Field(..., max_length=255)
    password: str = Field(..., max_length=128)
    email: EmailStr | None = Field(default=None, max_length=255)


class UserUpdate(BaseUpdate):
    username: str | None = Field(default=None, max_length=255)
    password: str | None = Field(default=None, max_length=128)
    email: EmailStr | None = Field(default=None, max_length=255)


class UserDelete(BaseDelete):
    ...


class UserPublic(SQLModel):
    id: int
    username: str
    email: EmailStr | None
    created_at: datetime
    updated_at: datetime

    roles: list["RolePublic"] | None = Field(default=None)


class RoleSelect(BaseSelect):
    name: str | None = Field(default=None, max_length=255)


class RoleCreate(SQLModel):
    name: str = Field(..., max_length=255)


class RoleUpdate(BaseUpdate):
    name: str | None = Field(default=None, max_length=255)


class RoleDelete(BaseDelete):
    ...


class RolePublic(SQLModel):
    id: int
    name: str
    created_at: datetime
    updated_at: datetime

    permissions: list["PermissionPublic"] | None = Field(default=None)


class PermissionSelect(BaseSelect):
    name: str | None = Field(default=None, max_length=255)


class PermissionCreate(SQLModel):
    name: str = Field(..., max_length=255)
    scope: str = Field(..., max_length=255)
    desc: str | None = Field(default=None, max_length=255)


class PermissionUpdate(BaseUpdate):
    name: str | None = Field(default=None, max_length=255)
    scope: str | None = Field(default=None, max_length=255)
    desc: str | None = Field(default=None, max_length=255)


class PermissionDelete(BaseDelete):
    ...


class PermissionPublic(SQLModel):
    id: int
    name: str
    scope: str
    desc: str | None
    created_at: datetime
    updated_at: datetime


class GrantRole(SQLModel):
    uid: int
    rid: int


class GrantPermission(SQLModel):
    rid: int
    pid: int
