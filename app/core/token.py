import asyncio
import uuid
from datetime import datetime, timedelta, timezone
from typing import TypedDict

import jwt
from jwt.exceptions import InvalidTokenError
from redis.asyncio import Redis

from app.core.config import settings
from app.domains.auth.const import TokenType, RedisKey


class JWTPayload(TypedDict, total=False):
    sub: str
    type: str
    jti: str
    iat: int
    nbf: int
    exp: int
    iss: str
    aud: str
    scopes: list[str]


class Token:

    @staticmethod
    def expire(token_type: TokenType) -> int:
        seconds = 0
        if token_type == TokenType.ACCESS:
            seconds = settings.ACCESS_TOKEN_EXPIRE_SECONDS
        elif token_type == TokenType.REFRESH:
            seconds = settings.REFRESH_TOKEN_EXPIRE_SECONDS
        return int(timedelta(seconds=seconds).total_seconds())

    @staticmethod
    def _encode(payload: JWTPayload) -> str:
        return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

    @staticmethod
    def _decode(token: str) -> JWTPayload:
        return jwt.decode(
            jwt=token,
            key=settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
            options={
                "verify_exp": True,
                "verify_nbf": True,
                "verify_iat": True,
                "verify_aud": True,
                "verify_iss": True,
            },
            audience=settings.AUDIENCE,
            issuer=settings.ISSUER,
            leeway=settings.LEEWAY,
        )

    @classmethod
    async def _allow(cls, redis: Redis, token_type: TokenType, subject: str, jti: str, ttl: int) -> None:
        allow_key = RedisKey.ALLOW(token_type, jti)
        token_key = RedisKey.TOKEN(token_type, subject)
        async with redis.pipeline() as pipeline:
            pipeline.set(allow_key, subject, ex=ttl)
            pipeline.sadd(token_key, jti)
            pipeline.expire(token_key, ttl)
            await pipeline.execute()

    @classmethod
    async def _revoke(cls, redis: Redis, token_type: TokenType, jti: str) -> None:
        allow_key = RedisKey.ALLOW(token_type, jti)
        subject = await redis.get(allow_key)
        subject = subject.decode() if isinstance(subject, (bytes, bytearray)) else subject
        if subject:
            token_key = RedisKey.TOKEN(token_type, subject)
            async with redis.pipeline() as pipeline:
                pipeline.delete(allow_key)
                pipeline.srem(token_key, jti)
                await pipeline.execute()

    @classmethod
    async def create(cls, redis: Redis, token_type: TokenType, subject: str, scopes: list[str]) -> str:
        jti = str(uuid.uuid4())
        now = datetime.now(timezone.utc)
        expire = cls.expire(token_type)
        payload = JWTPayload(
            sub=subject,
            type=token_type.value,
            jti=jti,
            iat=int(now.timestamp()),
            nbf=int(now.timestamp()),
            exp=int(now.timestamp()) + expire,
            iss=settings.ISSUER,
            aud=settings.AUDIENCE,
            scopes=scopes,
        )
        token = cls._encode(payload)
        await cls._allow(redis, token_type, subject, jti, expire)
        return token

    @classmethod
    async def verify(cls, redis: Redis, token_type: TokenType, token: str) -> JWTPayload:
        try:
            payload = cls._decode(token)
        except Exception:
            raise
        if payload.get("type") != token_type.value:
            raise InvalidTokenError()
        sub = payload.get("sub")
        if not sub:
            raise InvalidTokenError()
        jti = payload.get("jti")
        if not jti:
            raise InvalidTokenError()
        allow_key = RedisKey.ALLOW(token_type, jti)
        if not await redis.exists(allow_key):
            raise InvalidTokenError()
        return payload

    @classmethod
    async def refresh(cls, redis: Redis, token: str) -> str:
        try:
            payload = await cls.verify(redis, TokenType.REFRESH, token)
        except Exception:
            raise
        await cls._revoke(redis, TokenType.ACCESS, payload["jti"])
        access_token = await cls.create(redis, TokenType.ACCESS, payload["sub"], payload["scopes"])
        return access_token

    @classmethod
    async def clear(cls, redis: Redis, subject: str):
        async with asyncio.TaskGroup() as task_group:
            for token_type in (TokenType.ACCESS, TokenType.REFRESH):
                jti_set = await redis.smembers(RedisKey.TOKEN(token_type, subject))
                for jti in jti_set:
                    jti = jti.decode() if isinstance(jti, (bytes, bytearray)) else jti
                    task_group.create_task(cls._revoke(redis, token_type, jti))

    @staticmethod
    def extract(header_value: str | None) -> str | None:
        if not header_value:
            return None
        parts = header_value.strip().split()
        if len(parts) != 2 or parts[0].lower() != "bearer":
            return None
        return parts[1]
