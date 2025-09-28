import asyncio
import logging
from typing import Callable, Awaitable, TypeVar, Any

from fastapi import status, HTTPException
from sqlmodel import SQLModel

from app.core.config import settings
from app.domains.base_exception import Error
from app.domains.base_schema import BaseData, BaseResponse

D = TypeVar("D", bound=BaseData | SQLModel)
R = TypeVar("R", bound=BaseResponse)


class BaseService:
    _instances = {}

    @classmethod
    def instance(cls):
        if cls not in cls._instances:
            cls._instances[cls] = cls()
        return cls._instances[cls]

    @staticmethod
    async def safe_execute(
            func: Callable[..., Awaitable[D]],
            *args,
            **kwargs,
    ) -> R:
        data: Any | None = None
        try:
            data: D = await func(*args, **kwargs)
            return BaseResponse(
                status_code=status.HTTP_200_OK,
                detail=Error.SUCCESS,
                data=data,
            )
        except asyncio.CancelledError:
            raise
        except HTTPException as e:
            if settings.DEBUG:
                logging.exception(f"{func.__name__} HTTPException: {e.detail}")
            return BaseResponse(
                status_code=e.status_code,
                detail=e.detail,
                data=data,
            )
        except Exception as e:
            if settings.DEBUG:
                logging.exception(f"{func.__name__} error")
            return BaseResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(e) or Error.FAILURE,
                data=data,
            )
