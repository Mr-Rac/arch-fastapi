"""FastAPI application factory.

Creates the app instance, registers middleware, exception handlers
and the versioned API router.  Uses ``ORJSONResponse`` as the default
response class for high-performance JSON serialization.
"""

import logging

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import ORJSONResponse

from app.api.v1.router import v1_router
from app.core.config import settings
from app.core.errors import BizError, ErrorCode
from app.lifespan import lifespan

app = FastAPI(
    debug=settings.DEBUG,
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_PREFIX}/openapi.json",
    docs_url=f"{settings.API_PREFIX}/docs",
    redoc_url=f"{settings.API_PREFIX}/redoc",
    lifespan=lifespan,
)

# ── CORS ──────────────────────────────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Exception handlers ────────────────────────────────────────────────────


@app.exception_handler(HTTPException)
async def http_error_handler(_request: Request, exc: HTTPException) -> ORJSONResponse:
    """Wrap FastAPI's built-in HTTPExceptions into the unified envelope."""
    return ORJSONResponse(
        status_code=exc.status_code,
        content={"code": exc.status_code, "message": exc.detail, "data": None},
    )


@app.exception_handler(BizError)
async def biz_error_handler(_request: Request, exc: BizError) -> ORJSONResponse:
    """Translate ``BizError`` into a unified JSON response."""
    return ORJSONResponse(
        status_code=exc.status_code,
        content={"code": exc.code, "message": exc.message, "data": exc.data},
    )


@app.exception_handler(RequestValidationError)
async def validation_error_handler(_request: Request, exc: RequestValidationError) -> ORJSONResponse:
    """Return pydantic validation errors in the standard envelope."""
    return ORJSONResponse(
        status_code=422,
        content={"code": ErrorCode.VALIDATION_ERROR, "message": "validation error", "data": exc.errors()},
    )


@app.exception_handler(Exception)
async def global_error_handler(_request: Request, exc: Exception) -> ORJSONResponse:
    """Catch-all for unexpected exceptions - log and return 500."""
    logging.exception("Unhandled exception: %s", exc)
    return ORJSONResponse(
        status_code=500,
        content={"code": ErrorCode.INTERNAL_ERROR, "message": "internal server error", "data": None},
    )


# ── Routes ────────────────────────────────────────────────────────────────

app.include_router(v1_router, prefix=settings.API_PREFIX)


@app.get("/health", include_in_schema=False)
async def health() -> dict[str, str]:
    """Simple liveness probe."""
    return {"status": "ok"}
