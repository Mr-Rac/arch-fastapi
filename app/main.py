"""FastAPI application factory.

Creates the app, registers middleware, exception handlers and routes.
Logging is initialized here via :func:`setup_logging` so that every
module in the process shares the same format and ``request_id`` context.
"""

import logging
import time

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import ORJSONResponse

from app.api.v1.router import v1_router
from app.core.config import settings
from app.core.errors import BizError, ErrorCode
from app.core.log import generate_request_id, request_id_var, setup_logging
from app.lifespan import lifespan

# ── Initialize logging (once, before anything else) ──────────────────────

setup_logging(level=settings.LOG_LEVEL)
logger = logging.getLogger(__name__)

# ── App ───────────────────────────────────────────────────────────────────

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


# ── Request middleware (trace ID + access log) ────────────────────────────

access_logger = logging.getLogger("app.access")


@app.middleware("http")
async def request_context_middleware(request: Request, call_next) -> Response:
    """Assign a trace ID and log every request with its duration."""
    rid = request.headers.get("X-Request-ID") or generate_request_id()
    request_id_var.set(rid)

    start = time.perf_counter()
    response: Response = await call_next(request)
    elapsed_ms = (time.perf_counter() - start) * 1000

    response.headers["X-Request-ID"] = rid
    access_logger.info(
        "%s %s %d %.1fms",
        request.method,
        request.url.path,
        response.status_code,
        elapsed_ms,
    )
    return response


# ── Exception handlers ────────────────────────────────────────────────────


@app.exception_handler(HTTPException)
async def http_error_handler(request: Request, exc: HTTPException) -> ORJSONResponse:
    """Wrap FastAPI's built-in HTTPExceptions into the unified envelope."""
    logger.warning(
        "HTTPException | %s %s | status=%d detail=%s",
        request.method,
        request.url.path,
        exc.status_code,
        exc.detail,
    )
    return ORJSONResponse(
        status_code=exc.status_code,
        content={"code": exc.status_code, "message": exc.detail, "data": None},
    )


@app.exception_handler(BizError)
async def biz_error_handler(request: Request, exc: BizError) -> ORJSONResponse:
    """Translate ``BizError`` into a unified JSON response."""
    log_fn = logger.warning if exc.status_code < 500 else logger.error
    log_fn(
        "BizError | %s %s | code=%d message=%s",
        request.method,
        request.url.path,
        exc.code,
        exc.message,
    )
    return ORJSONResponse(
        status_code=exc.status_code,
        content={"code": exc.code, "message": exc.message, "data": exc.data},
    )


@app.exception_handler(RequestValidationError)
async def validation_error_handler(request: Request, exc: RequestValidationError) -> ORJSONResponse:
    """Return pydantic validation errors in the standard envelope."""
    logger.warning(
        "ValidationError | %s %s | errors=%s",
        request.method,
        request.url.path,
        exc.errors(),
    )
    return ORJSONResponse(
        status_code=422,
        content={"code": ErrorCode.VALIDATION_ERROR, "message": "validation error", "data": exc.errors()},
    )


@app.exception_handler(Exception)
async def global_error_handler(request: Request, exc: Exception) -> ORJSONResponse:
    """Catch-all for unexpected exceptions - log full traceback."""
    logger.exception(
        "UnhandledException | %s %s | %s: %s",
        request.method,
        request.url.path,
        type(exc).__name__,
        exc,
    )
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
