from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from app.api.dependencies.mysql import AuthMySQLDep
from app.api.dependencies.redis import AuthRedisDep
from app.core.config import settings
from app.core.token import Token
from app.domains.auth.const import TokenType
from app.domains.auth.curd import UserCurd
from app.domains.auth.exception import AuthError
from app.domains.auth.schema import UserSelect

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_PREFIX}/auth/login")


def check_scopes(*scopes: str):
    async def _checker(
            token: Annotated[str, Depends(oauth2_scheme)],
            session: AuthMySQLDep,
            redis: AuthRedisDep,
    ):
        try:
            payload = await Token.verify(redis, TokenType.ACCESS, token)
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=AuthError.INVALID_TOKEN,
                headers={
                    "WWW-Authenticate": "Bearer"
                },
            )
        user = await UserCurd.select(session, UserSelect(username=payload["sub"]))
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=AuthError.INVALID_USER,
                headers={
                    "WWW-Authenticate": "Bearer"
                },
            )
        jwt_scopes = set(payload["scopes"])
        user_scopes = set(user.scopes)

        if jwt_scopes != user_scopes:
            raise HTTPException(
                status_code=status.HTTP_426_UPGRADE_REQUIRED,
                detail=AuthError.EXPIRED_SCOPES,
                headers={
                    "WWW-Authenticate": "Bearer"
                }
            )
        if settings.ADMIN_PERMISSION_SCOPE not in user_scopes and not set(scopes).issubset(user_scopes):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=AuthError.INVALID_SCOPES,
                headers={
                    "WWW-Authenticate": "Bearer"
                },
            )

    return _checker
