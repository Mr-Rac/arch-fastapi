from typing import Annotated

from fastapi import Request, HTTPException, status, Depends
from redis.asyncio import Redis

from app.domains.base_exception import Error


async def get_auth_redis(request: Request) -> Redis:
    if auth_redis_pool := getattr(request.state, "auth_redis_pool", None):
        return Redis.from_pool(auth_redis_pool)
    raise HTTPException(
        status_code=status.HTTP_424_FAILED_DEPENDENCY,
        detail=Error.INVALID_REDIS,
    )


AuthRedisDep = Annotated[Redis, Depends(get_auth_redis)]
