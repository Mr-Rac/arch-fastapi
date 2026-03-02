"""Unified error codes and business exception.

Error code convention — ``XYYY``:
  * X=0  success
  * X=1  client errors  (bad request, validation, not found …)
  * X=2  auth errors    (credentials, token, permission …)
  * X=5  server errors  (database, cache, unexpected …)

All API routes should raise ``BizError`` instead of raw ``HTTPException``
so that the global exception handler can return a consistent JSON body.
"""

from enum import IntEnum
from typing import Any


class ErrorCode(IntEnum):
    """Business error code enumeration."""

    SUCCESS = 0

    # ── Client errors (1xxx) ──────────────────────────────────────────────
    BAD_REQUEST = 1000
    VALIDATION_ERROR = 1001
    NOT_FOUND = 1002
    CONFLICT = 1003

    # ── Auth errors (2xxx) ────────────────────────────────────────────────
    UNAUTHORIZED = 2000
    FORBIDDEN = 2001
    INVALID_CREDENTIALS = 2002
    TOKEN_EXPIRED = 2003
    TOKEN_INVALID = 2004
    USER_NOT_FOUND = 2005
    USER_ALREADY_EXISTS = 2006
    ROLE_NOT_FOUND = 2007
    ROLE_ALREADY_EXISTS = 2008
    PERMISSION_NOT_FOUND = 2009
    PERMISSION_ALREADY_EXISTS = 2010

    # ── Server errors (5xxx) ──────────────────────────────────────────────
    INTERNAL_ERROR = 5000
    DATABASE_ERROR = 5001
    CACHE_ERROR = 5002


# Default HTTP status + human-readable message per error code.
_REGISTRY: dict[ErrorCode, tuple[int, str]] = {
    ErrorCode.SUCCESS: (200, "success"),
    ErrorCode.BAD_REQUEST: (400, "bad request"),
    ErrorCode.VALIDATION_ERROR: (422, "validation error"),
    ErrorCode.NOT_FOUND: (404, "resource not found"),
    ErrorCode.CONFLICT: (409, "resource conflict"),
    ErrorCode.UNAUTHORIZED: (401, "unauthorized"),
    ErrorCode.FORBIDDEN: (403, "forbidden"),
    ErrorCode.INVALID_CREDENTIALS: (401, "invalid credentials"),
    ErrorCode.TOKEN_EXPIRED: (401, "token expired"),
    ErrorCode.TOKEN_INVALID: (401, "token invalid"),
    ErrorCode.USER_NOT_FOUND: (404, "user not found"),
    ErrorCode.USER_ALREADY_EXISTS: (409, "user already exists"),
    ErrorCode.ROLE_NOT_FOUND: (404, "role not found"),
    ErrorCode.ROLE_ALREADY_EXISTS: (409, "role already exists"),
    ErrorCode.PERMISSION_NOT_FOUND: (404, "permission not found"),
    ErrorCode.PERMISSION_ALREADY_EXISTS: (409, "permission already exists"),
    ErrorCode.INTERNAL_ERROR: (500, "internal server error"),
    ErrorCode.DATABASE_ERROR: (500, "database error"),
    ErrorCode.CACHE_ERROR: (500, "cache error"),
}


class BizError(Exception):
    """Business logic exception.

    Raised anywhere in domain / infra layer and caught by the global
    exception handler in ``main.py`` which returns a unified JSON body.

    Args:
        code: An ``ErrorCode`` member.
        message: Override the default message if needed.
        data: Optional payload to include in the response body.
    """

    def __init__(
        self,
        code: ErrorCode = ErrorCode.INTERNAL_ERROR,
        message: str | None = None,
        data: Any = None,
    ) -> None:
        http_status, default_msg = _REGISTRY.get(code, (500, "unknown error"))
        self.code: int = code
        self.status_code: int = http_status
        self.message: str = message or default_msg
        self.data: Any = data
        super().__init__(self.message)
