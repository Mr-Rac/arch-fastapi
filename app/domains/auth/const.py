from enum import Enum


class TokenType(str, Enum):
    ACCESS = "access"
    REFRESH = "refresh"


class RedisKey:
    @staticmethod
    def ALLOW(token_type: TokenType, jti: str) -> str:
        return f"auth:allow:{token_type.value}:{jti}"

    @classmethod
    def TOKEN(cls, token_type: TokenType, subject: str) -> str:
        return f"auth:token:{token_type.value}:{subject}"
