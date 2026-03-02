"""JWT token creation / verification and password hashing utilities.

Pure functions - no database or cache access.  Token persistence
(allow-list) is handled in ``infra.auth.redis_repository``.
"""

import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

import bcrypt
import jwt

from app.core.config import settings
from app.core.errors import BizError, ErrorCode

# ── Password ──────────────────────────────────────────────────────────────


def hash_password(plain: str) -> str:
    """Hash a plaintext password with bcrypt."""
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt()).decode()


def verify_password(plain: str, hashed: str) -> bool:
    """Return ``True`` if *plain* matches the bcrypt *hashed* value."""
    return bcrypt.checkpw(plain.encode(), hashed.encode())


# ── JWT ───────────────────────────────────────────────────────────────────


def create_access_token(subject: str, scopes: list[str]) -> tuple[str, str]:
    """Create an access token.

    Returns:
        A ``(token, jti)`` tuple.  The caller must persist the *jti*
        in the allow-list.
    """
    return _encode(subject, scopes, "access", settings.ACCESS_TOKEN_EXPIRE_SECONDS)


def create_refresh_token(subject: str, scopes: list[str]) -> tuple[str, str]:
    """Create a refresh token.

    Returns:
        A ``(token, jti)`` tuple.
    """
    return _encode(subject, scopes, "refresh", settings.REFRESH_TOKEN_EXPIRE_SECONDS)


def decode_token(token: str) -> dict[str, Any]:
    """Decode and validate a JWT.

    Raises:
        BizError: ``TOKEN_EXPIRED`` or ``TOKEN_INVALID``.
    """
    try:
        return jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
            issuer=settings.ISSUER,
            audience=settings.AUDIENCE,
            leeway=settings.LEEWAY,
        )
    except jwt.ExpiredSignatureError:
        raise BizError(ErrorCode.TOKEN_EXPIRED) from None
    except jwt.PyJWTError:
        raise BizError(ErrorCode.TOKEN_INVALID) from None


# ── Internal ──────────────────────────────────────────────────────────────


def _encode(subject: str, scopes: list[str], token_type: str, expire_seconds: int) -> tuple[str, str]:
    jti = uuid.uuid4().hex
    now = datetime.now(UTC)
    payload = {
        "sub": subject,
        "type": token_type,
        "jti": jti,
        "iat": now,
        "nbf": now,
        "exp": now + timedelta(seconds=expire_seconds),
        "iss": settings.ISSUER,
        "aud": settings.AUDIENCE,
        "scopes": scopes,
    }
    token = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return token, jti
