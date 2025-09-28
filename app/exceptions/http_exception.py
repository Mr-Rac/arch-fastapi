from fastapi import Request, Response, HTTPException
from fastapi.responses import JSONResponse


async def http_exception_handler(request: Request, exc: HTTPException) -> Response:
    return JSONResponse(
        content={
            "status_code": exc.status_code,
            "detail": exc.detail,
        },
        status_code=exc.status_code,
        headers=exc.headers,
    )
