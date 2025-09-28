from typing import Any

from fastapi import status
from sqlmodel import SQLModel, Field

from app.domains.base_exception import Error


class BaseData(SQLModel):
    ...


class BaseRequest(SQLModel):
    ...


class BaseResponse(SQLModel):
    status_code: int = Field(default=status.HTTP_200_OK, description="status code")
    detail: str = Field(default=Error.SUCCESS, description="detail")
    data: Any | None = Field(default=None, description="data")


class BaseSelect(SQLModel):
    id: int | None = Field(default=None)


class BaseUpdate(SQLModel):
    id: int


class BaseDelete(SQLModel):
    id: int
