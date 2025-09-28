import json
import logging
from typing import Optional

from aiohttp import ClientSession, web
from fastapi import Request, HTTPException, status

from app.core.config import settings
from app.domains.base_exception import Error


async def get_aiohttp(request: Request) -> ClientSession:
    if session := getattr(request.app.state, "aiohttp", None):
        return session
    raise HTTPException(
        status_code=status.HTTP_424_FAILED_DEPENDENCY,
        detail=Error.INVALID_AIOHTTP
    )


async def get(
        session: ClientSession,
        url: str,
        headers: Optional[dict] = None,
) -> web.Response:
    async with session.get(url, headers=headers) as resp:
        resp.raise_for_status()
        if settings.DEBUG:
            logging.warning(
                f"\n请求url: {url}"
                f"\nresponse: {json.dumps(await resp.json(), indent=4, separators=(',', ': '))}"
            )
        return await resp.json()


async def post(
        session: ClientSession,
        url: str,
        data: Optional[dict] = None,
        headers: Optional[dict] = None,
) -> web.Response:
    async with session.post(url, json=data, headers=headers) as resp:
        resp.raise_for_status()
        if settings.DEBUG:
            logging.warning(
                f"\n请求url: {url}"
                f"\npayload: {data}"
                f"\nresponse: {json.dumps(await resp.json(), indent=4, separators=(',', ': '))}"
            )
        return await resp.json()
