import secrets
from typing import Literal, Annotated

from pydantic import (
    BeforeValidator,
    computed_field,
    AnyUrl,
)
from pydantic_core import MultiHostUrl
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.utils.parse import parse_to_list


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_ignore_empty=True,
        extra="ignore",
    )

    # Base
    ENVIRONMENT: Literal["local", "staging", "production"] = "local"
    PROJECT_NAME: str = "Arch FastAPI"
    VERSION: str = "0.0.1"
    CORS_ORIGINS: Annotated[list[AnyUrl] | str, BeforeValidator(parse_to_list)] = []
    API_PREFIX: str = "/api"

    @computed_field
    @property
    def DEBUG(self) -> bool:
        return self.ENVIRONMENT != "production"

    @computed_field
    @property
    def ORIGINS(self) -> list[str]:
        return [str(origin).rstrip("/") for origin in self.CORS_ORIGINS]

    # OAuth
    SECRET_KEY: str = secrets.token_urlsafe(32)
    ALGORITHM: str = "HS256"
    ISSUER: str = "arc-fastapi"
    AUDIENCE: str = "arc-fastapi"
    LEEWAY: float = 30.0
    ACCESS_TOKEN_EXPIRE_SECONDS: int = 60 * 10
    REFRESH_TOKEN_EXPIRE_SECONDS: int = 60 * 60 * 24 * 7

    # Aiohttp
    AIOHTTP_TIMEOUT: int = 30

    # Redis
    REDIS_HOST: str
    REDIS_PORT: int = 6379
    REDIS_USERNAME: str | None = None
    REDIS_PASSWORD: str = ""
    REDIS_DECODE_RESPONSES: bool = True
    REDIS_RETRY_ON_TIMEOUT: bool = True
    REDIS_MAX_CONNECTIONS: int = 10

    REDIS_AUTH_DB: int = 0

    @computed_field
    @property
    def AUTH_REDIS_DB_URL(self) -> str:
        return MultiHostUrl.build(
            scheme="redis",
            username=self.REDIS_USERNAME,
            password=self.REDIS_PASSWORD,
            host=self.REDIS_HOST,
            port=self.REDIS_PORT,
            path=str(self.REDIS_AUTH_DB),
        ).unicode_string()

    # MySQL
    MYSQL_HOST: str
    MYSQL_PORT: int = 3306
    MYSQL_USERNAME: str
    MYSQL_PASSWORD: str = ""
    MYSQL_ISOLATION_LEVEL: str = "READ COMMITTED"
    MYSQL_MAX_OVERFLOW: int = 20
    MYSQL_POOL_PRE_PING: bool = True
    MYSQL_POOL_SIZE: int = 10
    MYSQL_POOL_RECYCLE: int = 1800
    MYSQL_POOL_TIMEOUT: int = 30

    MYSQL_AUTH_DB: str = "auth"

    @computed_field
    @property
    def MYSQL_AUTH_DB_URL(self) -> str:
        return MultiHostUrl.build(
            scheme="mysql+aiomysql",
            username=self.MYSQL_USERNAME,
            password=self.MYSQL_PASSWORD,
            host=self.MYSQL_HOST,
            port=self.MYSQL_PORT,
            path=self.MYSQL_AUTH_DB,
        ).unicode_string()

    @computed_field
    @property
    def MYSQL_ECHO(self) -> bool:
        return self.DEBUG

    ADMIN_USER_USERNAME: str = "admin"
    ADMIN_USER_PASSWORD: str = "admin"
    ADMIN_ROLE_NAME: str = "admin"
    ADMIN_PERMISSION_NAME: str = "admin"
    ADMIN_PERMISSION_SCOPE: str = "admin"
    ADMIN_PERMISSION_DESC: str = "admin"


settings = Settings()  # type: ignore
