from typing import AsyncGenerator, Annotated

from fastapi import Depends, HTTPException, Request, status
from redis.asyncio import Redis

from app.domains.base_exception import Error


async def get_auth_redis(request: Request) -> AsyncGenerator[Redis, None]:
    if auth_redis_pool := getattr(request.state, "auth_redis_pool", None):
        redis = Redis.from_pool(auth_redis_pool)
        try:
            yield redis
        finally:
            await redis.aclose()
    else:
        raise HTTPException(
            status_code=status.HTTP_424_FAILED_DEPENDENCY,
            detail=Error.INVALID_REDIS,
        )


AuthRedisDep = Annotated[Redis, Depends(get_auth_redis)]
